############################################################################################################################
#
#   ██████╗ ██████╗ ██╗███╗   ██╗██████╗  █████╗ ███████╗███████╗                          
#  ██╔════╝██╔═══██╗██║████╗  ██║██╔══██╗██╔══██╗██╔════╝██╔════╝                          
#  ██║     ██║   ██║██║██╔██╗ ██║██████╔╝███████║███████╗█████╗                            
#  ██║     ██║   ██║██║██║╚██╗██║██╔══██╗██╔══██║╚════██║██╔══╝                            
#  ╚██████╗╚██████╔╝██║██║ ╚████║██████╔╝██║  ██║███████║███████╗                          
#   ╚═════╝ ╚═════╝ ╚═╝╚═╝  ╚═══╝╚═════╝ ╚═╝  ╚═╝╚══════╝╚══════╝                          
#                                                                                                                
#  ██╗     ██╗ ██████╗ ██╗   ██╗██╗██████╗  █████╗ ████████╗ ██████╗ ██████╗     ██╗   ██╗ ██╗    ██████╗ ███████╗
#  ██║     ██║██╔═══██╗██║   ██║██║██╔══██╗██╔══██╗╚══██╔══╝██╔═══██╗██╔══██╗    ██║   ██║███║   ██╔═████╗╚════██║
#  ██║     ██║██║   ██║██║   ██║██║██║  ██║███████║   ██║   ██║   ██║██████╔╝    ██║   ██║╚██║   ██║██╔██║    ██╔╝
#  ██║     ██║██║▄▄ ██║██║   ██║██║██║  ██║██╔══██║   ██║   ██║   ██║██╔══██╗    ╚██╗ ██╔╝ ██║   ████╔╝██║   ██╔╝ 
#  ███████╗██║╚██████╔╝╚██████╔╝██║██████╔╝██║  ██║   ██║   ╚██████╔╝██║  ██║     ╚████╔╝  ██║██╗╚██████╔╝   ██║  
#  ╚══════╝╚═╝ ╚══▀▀═╝  ╚═════╝ ╚═╝╚═════╝ ╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝      ╚═══╝   ╚═╝╚═╝ ╚═════╝    ╚═╝ 
#
# Coinbase Liquidator - Automated Portfolio Liquidation Script
# Converts all token balances to USD in one click - the "dust converter" Coinbase doesn't provide
#
# Purpose:
# • Automates liquidation of multiple token balances that would be tedious to sell manually
# • Handles small "dust" positions that accumulate in active trading accounts
# • Provides quick portfolio exit during volatile market conditions
# • Respects Coinbase's strict trading rules (base_increment, quote_increment, limit-only)
#
# Features:
# • Universal balance detection using portfolio endpoint
# • Intelligent order type selection (market orders with limit order fallback)
# • Base increment validation ensures only valid order sizes
# • Excludes specified assets (BTC, ETH, SOL by default)
# • Dynamic trading pair detection with fresh data on every run
# • Comprehensive error handling and detailed logging
#
# Coinbase Liquidator v1.07
# Automated dust liquidation and portfolio exit script for Coinbase
# Created by: https://github.com/xa-io
# Last Updated: 2025-07-26 00:11:50
#
# ## Release Notes ##
#
# v1.07 - Added AUTO_CONFIRM_LIQUIDATION config to skip user confirmation prompt for automated runs
# v1.06 - Forces fresh products and active pairs data on every run, eliminating stale data issues
# v1.05 - Simplified decimal precision logic for cleaner, more maintainable code
# v1.04 - Fixed limit order fallback function call for limit-only pairs
# v1.03 - Added limit order fallback for pairs in limit-only mode and log visibility control
# v1.02 - Replaced manual active_pairs.txt with automated trading pair detection
# v1.01 - Fixed critical order success detection logic for accurate reporting
# v1.00 - Initial release
#
############################################################################################################################

###########################################
#### Start of Configuration Parameters ####
###########################################

# Order placement settings
DELAY_BETWEEN_ORDERS = 0.2               # Seconds between order placements (rate limiting)
DRY_RUN_MODE = False                     # Set to True to simulate without placing orders
EXCLUDED_PAIRS = ["BTC", "ETH", "SOL"]   # Assets to exclude from liquidation
SHOW_UNSELLABLE_ASSETS = False           # Show unsellable assets (✗) in logs
AUTO_CONFIRM_LIQUIDATION = False         # Set to True to skip confirmation prompt and auto-liquidate

# File configuration
PRODUCTS_FILE = "products.json"          # File to store Coinbase product information
PRODUCTS_MAX_AGE_HOURS = 4               # Hours before refreshing products file
FORCE_FRESH_DATA = False                 # Force fresh products and pairs data on each run
ACTIVE_PAIRS_FILE = "active_pairs.txt"   # File containing trading-enabled pairs

# API settings
API_REQUEST_DELAY = 0.3                  # Delay between API requests
RATE_LIMIT_DELAY = 2.0                   # Wait time when rate limit exceeded
MAX_RETRIES = 3                          # Maximum retries for API calls

# Logging settings
DEBUG = False                            # Enable debug logging
SHOW_TIMESTAMP = False                   # Show timestamps in logs

#########################################
#### End of Configuration Parameters ####
#########################################

import os
import time
import json
import sys
import requests
from decimal import Decimal, getcontext, ROUND_DOWN
from datetime import datetime
from dotenv import load_dotenv
from coinbase.rest import RESTClient

# Fix Unicode encoding for Windows console
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Load environment variables
load_dotenv()

# Get script directory for relative file paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# API setup
api_key = os.getenv("COINBASE_API_KEY")
api_secret = os.getenv("COINBASE_API_SECRET")
client = RESTClient(api_key=api_key, api_secret=api_secret)

# Set decimal precision
getcontext().prec = 16

# Global variables
liquidation_count = 0
total_liquidated_value = Decimal('0')

def get_timestamp():
    """Get formatted timestamp for logging"""
    if SHOW_TIMESTAMP:
        return f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
    return ""

def log(message):
    """Log a message with timestamp if configured"""
    print(f"{get_timestamp()}{message}")

def debug_log(message):
    """Log debug message only if debug mode is enabled"""
    if DEBUG:
        log(f"[DEBUG] {message}")

def get_products_from_api():
    """Fetch all product information from Coinbase Exchange API"""
    url = "https://api.exchange.coinbase.com/products"
    try:
        debug_log(f"Fetching products from API: {url}")
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            products = response.json()
            debug_log(f"Successfully fetched {len(products)} products from API")
            return products
        else:
            log(f"Error fetching products: HTTP {response.status_code}")
            return None
            
    except Exception as e:
        log(f"Exception fetching products from API: {e}")
        return None

def ensure_products_file(force_refresh=False):
    """Ensure the products file exists and is up-to-date"""
    products_file = os.path.join(SCRIPT_DIR, PRODUCTS_FILE)
    max_age_hours = PRODUCTS_MAX_AGE_HOURS
    current_datetime = datetime.now()
    
    # Check products file status
    products_file_exists = os.path.isfile(products_file)
    products_file_outdated = True
    
    # Force refresh if requested or FORCE_FRESH_DATA is enabled
    if force_refresh or FORCE_FRESH_DATA:
        debug_log("Forcing fresh products data refresh...")
        products_file_outdated = True
    elif products_file_exists:
        # Check products file age
        products_file_timestamp = os.path.getmtime(products_file)
        products_file_datetime = datetime.fromtimestamp(products_file_timestamp)
        age_hours = (current_datetime - products_file_datetime).total_seconds() / 3600
        
        if age_hours <= max_age_hours:
            products_file_outdated = False
            debug_log(f"Products file is {age_hours:.1f} hours old (within {max_age_hours}h limit)")
        else:
            debug_log(f"Products file is {age_hours:.1f} hours old (exceeds {max_age_hours}h limit)")
    
    # Case 1: Products file doesn't exist, is outdated, or force refresh requested
    if not products_file_exists or products_file_outdated:
        debug_log("Fetching fresh products data from API...")
        
        # Fetch products from API
        products = get_products_from_api()
        
        if products:
            try:
                # Save products to file
                with open(products_file, 'w') as f:
                    json.dump(products, f, indent=2)
                log(f"Saved {len(products)} products to {PRODUCTS_FILE}")
                return products
            except Exception as e:
                log(f"Error saving products file: {e}")
                # Try to load existing file if save failed
                if products_file_exists:
                    try:
                        with open(products_file, 'r') as f:
                            return json.load(f)
                    except Exception as e2:
                        log(f"Error loading existing products file: {e2}")
                return None
        else:
            # API fetch failed, try to load existing file
            if products_file_exists:
                try:
                    with open(products_file, 'r') as f:
                        products = json.load(f)
                    log(f"Using existing products file ({len(products)} products)")
                    return products
                except Exception as e2:
                    log(f"Error loading existing products file: {e2}")
            return None
    
    # Case 2: Products file exists and is up-to-date
    else:
        try:
            with open(products_file, 'r') as f:
                products = json.load(f)
            debug_log(f"Loaded {len(products)} products from existing file")
            return products
        except Exception as e:
            log(f"Error loading products file: {e}")
            return None

def get_product_from_list(products_data, product_id):
    """Get information about a specific product from the products data"""
    if not products_data:
        return None
    
    # Find the product in the data
    for product in products_data:
        if product.get("id") == product_id:
            return product
    
    return None

def get_base_increment_for_pair(product_id, products_data):
    """Get the base_increment for a trading pair from products data"""
    if not products_data:
        debug_log(f"No products data available for {product_id}")
        return None
    
    product_info = get_product_from_list(products_data, product_id)
    if product_info:
        base_increment = product_info.get("base_increment")
        if base_increment:
            debug_log(f"Found base_increment for {product_id}: {base_increment}")
            return float(base_increment)
    
    debug_log(f"Unable to find base_increment for {product_id}")
    return None

def load_active_pairs(force_refresh=False):
    """Generate active trading pairs from products.json based on status and trading_disabled flags"""
    try:
        # Ensure products file exists and is current (force refresh if requested)
        products_data = ensure_products_file(force_refresh=force_refresh or FORCE_FRESH_DATA)
        
        if not products_data:
            log("Error: Could not load products data for active pairs generation")
            return None
        
        # Filter for active USD trading pairs
        active_pairs = []
        for product in products_data:
            if (product.get('quote_currency') == 'USD' and 
                product.get('status') == 'online' and 
                product.get('trading_disabled') == False):
                active_pairs.append(product.get('id'))
        
        active_pairs.sort()  # Sort alphabetically for consistency
        debug_log(f"Generated {len(active_pairs)} active USD trading pairs from products.json")
        debug_log(f"Sample active pairs: {active_pairs[:10]}...")  # Show first 10 for verification
        
        return active_pairs
        
    except Exception as e:
        log(f"Error generating active pairs from products.json: {e}")
        log(f"Falling back to liquidating all detected pairs")
        return None

def get_portfolio_balances():
    """Get all asset balances using the portfolio endpoint"""
    try:
        debug_log("Fetching portfolio data...")
        
        # Add delay to prevent rate limiting
        time.sleep(API_REQUEST_DELAY)
        
        # Get portfolios
        portfolios_response = client.get_portfolios()
        if not portfolios_response or 'portfolios' not in portfolios_response:
            log("No portfolios found")
            return {}
        
        portfolios = portfolios_response['portfolios']
        debug_log(f"Found {len(portfolios)} portfolios")
        
        # Use the first (default) portfolio
        default_portfolio = None
        for portfolio in portfolios:
            if portfolio.get('type') == 'DEFAULT':
                default_portfolio = portfolio
                break
        
        if not default_portfolio:
            default_portfolio = portfolios[0]  # Fallback to first portfolio
        
        portfolio_uuid = default_portfolio['uuid']
        debug_log(f"Using portfolio: {default_portfolio['name']} ({portfolio_uuid})")
        
        # Get portfolio breakdown (add delay for rate limiting)
        time.sleep(API_REQUEST_DELAY)
        breakdown_response = client.get_portfolio_breakdown(portfolio_uuid)
        if not breakdown_response or 'breakdown' not in breakdown_response:
            log("No portfolio breakdown found")
            return {}
        
        breakdown = breakdown_response['breakdown']
        spot_positions = breakdown.get('spot_positions', [])
        
        debug_log(f"Found {len(spot_positions)} spot positions")
        
        # Parse balances
        balances = {}
        for position in spot_positions:
            # Type checking before access to handle mixed data types
            if not isinstance(position, dict):
                debug_log(f"Skipping non-dict position: {type(position)} - {position}")
                continue
            
            asset = position.get('asset', '')
            if not isinstance(asset, str):
                debug_log(f"Skipping position with non-string asset: {type(asset)}")
                continue
            
            total_balance_crypto = position.get('total_balance_crypto', 0)
            available_to_trade_crypto = position.get('available_to_trade_crypto', 0)
            total_balance_fiat = position.get('total_balance_fiat', 0)
            account_uuid = position.get('account_uuid')
            asset_uuid = position.get('asset_uuid')
            
            if asset and total_balance_crypto and float(total_balance_crypto) > 0:
                balances[asset] = {
                    'total_balance': Decimal(str(total_balance_crypto)),
                    'available_balance': Decimal(str(available_to_trade_crypto)),
                    'fiat_value': Decimal(str(total_balance_fiat)),
                    'account_uuid': account_uuid,
                    'asset_uuid': asset_uuid,
                    'is_cash': position.get('is_cash', False)
                }
        
        return balances
        
    except Exception as e:
        log(f"Error fetching portfolio balances: {e}")
        if "429" in str(e) or "Too Many Requests" in str(e):
            log("Rate limit hit - waiting before retry...")
            time.sleep(RATE_LIMIT_DELAY * 2)
        return {}

def can_liquidate_balance(asset, balance_info, base_increment):
    """Check if a balance can be liquidated based on base_increment requirements"""
    available_balance = balance_info['available_balance']
    fiat_value = balance_info['fiat_value']
    
    # Skip USD and other cash assets
    if balance_info.get('is_cash', False) or asset == 'USD':
        debug_log(f"Skipping {asset}: Cash asset")
        return False, "Cash asset"
    
    # Skip excluded pairs
    if asset in EXCLUDED_PAIRS:
        debug_log(f"Skipping {asset}: Asset in excluded pairs list")
        return False, "Excluded asset"
    
    # Check base increment requirement
    if base_increment is None:
        debug_log(f"Skipping {asset}: No base_increment found")
        return False, "No base_increment found"
    
    if available_balance < Decimal(str(base_increment)):
        debug_log(f"Skipping {asset}: Balance {available_balance} below base_increment {base_increment}")
        return False, f"Balance below base_increment ({base_increment})"
    
    # Calculate sellable amount (multiple of base_increment)
    sellable_amount = (available_balance // Decimal(str(base_increment))) * Decimal(str(base_increment))
    
    if sellable_amount <= 0:
        debug_log(f"Skipping {asset}: No sellable amount after base_increment adjustment")
        return False, "No sellable amount"
    
    debug_log(f"Can liquidate {asset}: {sellable_amount} (from {available_balance} available)")
    return True, sellable_amount

def fetch_public_orderbook(product_id):
    """Fetch orderbook from public API to get current market price"""
    url = f"https://api.exchange.coinbase.com/products/{product_id}/book?level=1"
    
    try:
        import requests
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        bids = data.get('bids', [])
        asks = data.get('asks', [])
        
        if bids and asks:
            top_bid = float(bids[0][0])
            top_ask = float(asks[0][0])
            return {
                'success': True,
                'top_bid': top_bid,
                'top_ask': top_ask,
                'mid_price': (top_bid + top_ask) / 2
            }
        else:
            return {'success': False, 'error': 'No bids or asks available'}
            
    except Exception as e:
        debug_log(f"Error fetching public orderbook for {product_id}: {e}")
        return {'success': False, 'error': str(e)}

def get_product_info(product_id):
    """Fetch product information to determine appropriate decimal precision"""
    try:
        return client.get_product(product_id)
    except Exception as e:
        debug_log(f"Error fetching product info for {product_id}: {e}")
        return None

def format_price_with_precision(price, product_info=None):
    """Format price with proper decimal precision using ROUND_DOWN"""
    try:
        # Handle both dictionary (from products.json) and object (from API) formats
        quote_increment_value = None
        if product_info:
            if isinstance(product_info, dict):
                quote_increment_value = product_info.get('quote_increment')
            elif hasattr(product_info, 'quote_increment'):
                quote_increment_value = product_info.quote_increment
        
        if quote_increment_value:
            quote_increment_str = str(quote_increment_value)
            quote_increment = Decimal(quote_increment_str)
            
            # Calculate decimal places from quote_increment
            price_decimals = len(quote_increment_str.split('.')[-1]) if '.' in quote_increment_str else 0
            debug_log(f"Quote increment: {quote_increment} ({quote_increment_str}), Decimal places: {price_decimals}")
            
            # Convert price to Decimal
            price_decimal = Decimal(str(price))
            
            # Method 1: Use quantize with the actual quote_increment
            quantized_price = price_decimal.quantize(quote_increment, rounding=ROUND_DOWN)
            debug_log(f"Method 1 - Quantized with quote_increment: {quantized_price}")
            
            # Method 2: Alternative - round to decimal places and ensure it's a multiple of quote_increment
            # First round down to the required decimal places
            rounded_price = price_decimal.quantize(Decimal('0.1') ** price_decimals, rounding=ROUND_DOWN)
            debug_log(f"Method 2 - Rounded to {price_decimals} decimals: {rounded_price}")
            
            # Then ensure it's a valid multiple of quote_increment
            if quote_increment > 0:
                # Calculate how many quote_increments fit into the rounded price
                increments = (rounded_price / quote_increment).quantize(Decimal('1'), rounding=ROUND_DOWN)
                final_price = increments * quote_increment
                debug_log(f"Method 2 - Final price (increments: {increments}): {final_price}")
            else:
                final_price = rounded_price
            
            # Use the more restrictive result (Method 2 is more accurate)
            result_price = float(final_price)
            debug_log(f"Original price: {price}, Final result: {result_price}")
            return result_price
        else:
            # Fallback to default precision
            price_decimals = 6
            rounded_price = round(float(price), price_decimals)
            debug_log(f"Using default precision: {rounded_price}")
            return rounded_price
    except Exception as e:
        debug_log(f"Error formatting price {price}: {e}")
        return float(price)

def place_limit_sell_order(product_id, size, price):
    """Place a limit sell order for the specified size and price"""
    global liquidation_count
    
    try:
        if DRY_RUN_MODE:
            log(f"[DRY RUN] Would place limit sell: {size} {product_id} @ ${price}")
            return True
        
        debug_log(f"Placing limit sell order: {size} {product_id} @ ${price}")
        
        # Add delay before order placement
        time.sleep(DELAY_BETWEEN_ORDERS)
        
        # Generate unique client order ID
        client_order_id = f"liquidator_{int(time.time() * 1000)}_{product_id.replace('-', '_')}"
        
        # Place limit sell order
        order = client.limit_order_gtc_sell(
            client_order_id=client_order_id,
            product_id=product_id,
            base_size=str(size),
            limit_price=str(price)
        )
        
        # Check if order was successful - API returns dict with 'success' key
        if order and isinstance(order, dict) and order.get('success', False):
            liquidation_count += 1
            order_id = order.get('order_id', 'N/A')
            log(f"✓ #{liquidation_count} Limit sell placed: {size} {product_id} @ ${price} (Order ID: {order_id})")
            return True
        else:
            log(f"✗ Failed to place limit sell order for {product_id}: {order}")
            return False
            
    except Exception as e:
        if "429" in str(e) or "Too Many Requests" in str(e):
            log(f"Rate limit hit during limit order placement for {product_id}, waiting {RATE_LIMIT_DELAY}s...")
            time.sleep(RATE_LIMIT_DELAY)
            return False
        elif "insufficient" in str(e).lower():
            log(f"✗ Insufficient balance for {product_id}: {e}")
            return False
        else:
            log(f"✗ Error placing limit sell order for {product_id}: {e}")
            return False

def place_limit_order_fallback(product_id, size):
    """Fallback function to place limit order 10% below market price for limit-only pairs"""
    try:
        # Get current market price from public orderbook
        orderbook = fetch_public_orderbook(product_id)
        if not orderbook['success']:
            log(f"✗ Failed to fetch market price for {product_id}: {orderbook.get('error', 'Unknown error')}")
            return False
        
        # Use top bid as reference (what buyers are willing to pay)
        market_price = orderbook['top_bid']
        
        # Calculate limit price 10% below market price
        limit_price = market_price * 0.9
        
        # Get product info from local products data for decimal precision
        # Ensure we have fresh products data for accurate precision info
        products_data = ensure_products_file(force_refresh=FORCE_FRESH_DATA)
        product_info = None
        if products_data:
            for product in products_data:
                if product.get('id') == product_id:
                    product_info = product
                    break
        
        debug_log(f"Found product info for {product_id}: {product_info is not None}")
        if product_info:
            debug_log(f"Quote increment from products.json: {product_info.get('quote_increment')}")
        
        # Format limit price with proper decimal precision using the new function
        debug_log(f"Raw limit price before formatting: {limit_price}")
        limit_price = format_price_with_precision(limit_price, product_info)
        debug_log(f"Formatted limit price: {limit_price}")
        
        if product_info:
            # Handle both dictionary and object formats
            quote_increment_value = None
            if isinstance(product_info, dict):
                quote_increment_value = product_info.get('quote_increment')
            elif hasattr(product_info, 'quote_increment'):
                quote_increment_value = product_info.quote_increment
            
            if quote_increment_value:
                quote_increment_decimal = Decimal(str(quote_increment_value))
                # Ensure limit price is at least one quote_increment
                if Decimal(str(limit_price)) < quote_increment_decimal:
                    limit_price = float(quote_increment_decimal)
                    debug_log(f"Adjusted limit price to minimum quote increment: {limit_price}")
        else:
            # Fallback minimum price
            if limit_price < 0.000001:
                limit_price = 0.000001
        
        log(f"📊 Market price: ${market_price}, Limit price: ${limit_price} (10% below)")
        
        # Place the limit order
        return place_limit_sell_order(product_id, size, limit_price)
        
    except Exception as e:
        log(f"✗ Error in limit order fallback for {product_id}: {e}")
        return False

def place_market_sell_order(product_id, size):
    """Place a market sell order for the specified size"""
    global liquidation_count
    
    try:
        if DRY_RUN_MODE:
            log(f"[DRY RUN] Would place market sell: {size} {product_id}")
            return True
        
        debug_log(f"Placing market sell order: {size} {product_id}")
        
        # Add delay before order placement
        time.sleep(DELAY_BETWEEN_ORDERS)
        
        # Generate unique client order ID
        client_order_id = f"liquidator_{int(time.time() * 1000)}_{product_id.replace('-', '_')}"
        
        # Place market sell order
        order = client.market_order_sell(
            client_order_id=client_order_id,
            product_id=product_id,
            base_size=str(size)
        )
        
        # Check if order was successful - API returns dict with 'success' key
        if order and isinstance(order, dict) and order.get('success', False):
            liquidation_count += 1
            order_id = order.get('order_id', 'N/A')
            log(f"✓ #{liquidation_count} Market sell placed: {size} {product_id} (Order ID: {order_id})")
            return True
        else:
            log(f"✗ Failed to place market sell order for {product_id}: {order}")
            return False
            
    except Exception as e:
        if "429" in str(e) or "Too Many Requests" in str(e):
            log(f"Rate limit hit during order placement for {product_id}, waiting {RATE_LIMIT_DELAY}s...")
            time.sleep(RATE_LIMIT_DELAY)
            return False
        elif "insufficient" in str(e).lower():
            log(f"✗ Insufficient balance for {product_id}: {e}")
            return False
        elif "limit only mode" in str(e).lower() or "limit order type" in str(e).lower():
            log(f"⚠ {product_id} is in limit-only mode, attempting limit order fallback...")
            return place_limit_order_fallback(product_id, size)
        else:
            log(f"✗ Error placing market sell order for {product_id}: {e}")
            return False

def liquidate_portfolio():
    """Main liquidation function"""
    global total_liquidated_value
    
    log("="*60)
    log("COINBASE PORTFOLIO LIQUIDATOR")
    log("="*60)
    
    if DRY_RUN_MODE:
        log("[DRY RUN MODE] - No actual orders will be placed")
    
    if FORCE_FRESH_DATA:
        log("[FRESH DATA MODE] - Updating products and active pairs data...")
    
    # Load products data (force fresh if configured)
    log("Loading products data...")
    products_data = ensure_products_file(force_refresh=FORCE_FRESH_DATA)
    if not products_data:
        log("ERROR: Could not load products data. Exiting.")
        return
    
    # Load active pairs for filtering (force fresh if configured)
    log("Loading active trading pairs...")
    active_pairs = load_active_pairs(force_refresh=FORCE_FRESH_DATA)
    
    # Get portfolio balances
    log("Fetching portfolio balances...")
    balances = get_portfolio_balances()
    
    if not balances:
        log("No balances found in portfolio. Exiting.")
        return
    
    log(f"Found {len(balances)} assets in portfolio")
    log("-"*60)
    
    # Analyze each balance for liquidation
    liquidation_candidates = []
    total_portfolio_value = Decimal('0')
    
    for asset, balance_info in balances.items():
        total_portfolio_value += balance_info['fiat_value']
        
        # Create trading pair ID
        pair_id = f"{asset}-USD"
        
        # Check if pair is in active pairs list (if available)
        if active_pairs and pair_id not in active_pairs:
            debug_log(f"Skipping {asset}: {pair_id} not in active pairs list")
            continue
        
        # Get base increment for this pair
        base_increment = get_base_increment_for_pair(pair_id, products_data)
        
        # Check if balance can be liquidated
        can_liquidate, result = can_liquidate_balance(
            asset, balance_info, base_increment
        )
        
        if can_liquidate:
            sellable_amount = result
            liquidation_candidates.append({
                'asset': asset,
                'pair_id': pair_id,
                'sellable_amount': sellable_amount,
                'available_balance': balance_info['available_balance'],
                'fiat_value': balance_info['fiat_value'],
                'base_increment': base_increment
            })
            
            log(f"✓ {asset:8} | Sellable: {sellable_amount:>15} | Value: ${balance_info['fiat_value']:>8.2f} | Pair: {pair_id}")
        else:
            reason = result
            if SHOW_UNSELLABLE_ASSETS:
                log(f"✗ {asset:8} | Balance: {balance_info['available_balance']:>15} | Value: ${balance_info['fiat_value']:>8.2f} | Skip: {reason}")
    
    log("-"*60)
    log(f"Total Portfolio Value: ${total_portfolio_value:.2f}")
    log(f"Liquidation Candidates: {len(liquidation_candidates)}")
    
    if not liquidation_candidates:
        log("No assets available for liquidation.")
        return
    
    # Calculate total liquidation value
    total_liquidation_value = sum(candidate['fiat_value'] for candidate in liquidation_candidates)
    log(f"Total Liquidation Value: ${total_liquidation_value:.2f}")
    
    # Confirm liquidation
    log("-"*60)
    if DRY_RUN_MODE:
        log(f"[DRY RUN] Would proceed with liquidating {len(liquidation_candidates)} assets (${total_liquidation_value:.2f})")
    elif AUTO_CONFIRM_LIQUIDATION:
        log(f"Auto-liquidating {len(liquidation_candidates)} assets (${total_liquidation_value:.2f})...")
    else:
        try:
            response = input(f"Proceed with liquidating {len(liquidation_candidates)} assets (${total_liquidation_value:.2f})? [y/N]: ")
            if response.lower() != 'y':
                log("Liquidation cancelled by user.")
                return
        except EOFError:
            log("No user input available, proceeding with liquidation...")
            # Automatically proceed if running in non-interactive environment
    
    log("-"*60)
    log("Starting liquidation process...")
    
    # Sort by value (highest first) to liquidate most valuable assets first
    liquidation_candidates.sort(key=lambda x: x['fiat_value'], reverse=True)
    
    successful_liquidations = 0
    failed_liquidations = 0
    
    for candidate in liquidation_candidates:
        asset = candidate['asset']
        pair_id = candidate['pair_id']
        sellable_amount = candidate['sellable_amount']
        fiat_value = candidate['fiat_value']
        
        log(f"Liquidating {asset}: {sellable_amount} (${fiat_value:.2f})...")
        
        success = place_market_sell_order(pair_id, sellable_amount)
        
        if success:
            successful_liquidations += 1
            total_liquidated_value += fiat_value
        else:
            failed_liquidations += 1
        
        # Add delay between orders
        if candidate != liquidation_candidates[-1]:  # Don't delay after last order
            time.sleep(DELAY_BETWEEN_ORDERS)
    
    log("-"*60)
    log("LIQUIDATION SUMMARY")
    log("-"*60)
    log(f"Successful Liquidations: {successful_liquidations}")
    log(f"Failed Liquidations: {failed_liquidations}")
    log(f"Total Liquidated Value: ${total_liquidated_value:.2f}")
    log(f"Total Orders Placed: {liquidation_count}")
    
    if successful_liquidations > 0:
        log("✓ Liquidation process completed successfully!")
        log("Note: Market orders may take a few moments to execute.")
        log("Check your Coinbase Pro account for order status and USD balance.")
    else:
        log("✗ No successful liquidations completed.")
    
    log("="*60)

def main():
    """Main function"""
    try:
        liquidate_portfolio()
    except KeyboardInterrupt:
        log("Liquidation interrupted by user.")
    except Exception as e:
        log(f"Unexpected error during liquidation: {e}")
        import traceback
        debug_log(f"Full traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    main()
