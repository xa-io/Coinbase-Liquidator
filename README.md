# Coinbase Liquidator

Automated portfolio liquidation script that converts all available token balances to USD using market orders and limit orders when needed. 

## Why This Script Exists

Many cryptocurrency exchanges provide a built-in "Convert Dust to USD" feature that allows users to easily liquidate small token balances ("dust") into cash with a single click. However, Coinbase Exchange lacks this functionality, requiring traders to manually sell each small balance individually - a tedious and time-consuming process when dealing with dozens of small positions.

This script automates that entire process, intelligently handling all token balances according to Coinbase's specific trading requirements and limitations. Whether you need to clean up dust accumulation or quickly exit all positions during volatile market conditions, Coinbase Liquidator streamlines the entire liquidation workflow into a single command.

**Created:** 2025-07-25

**Author:** https://github.com/xa-io

## Features

### Core Functionality
- **Universal Balance Detection**: Uses Coinbase portfolio endpoint to detect all available assets and balances
- **Base Increment Validation**: Checks products.json to ensure only sellable amounts are liquidated based on trading pair requirements
- **Trading-Enabled Pair Filtering**: Dynamically generates active pairs from products.json (status=online, trading_disabled=false)
- **Smart Order Placement**: Places market sell orders with limit order fallback for limit-only pairs
- **Fresh Data Updates**: Forces fresh products and active pairs data on each run to ensure accuracy
- **Comprehensive Logging**: Detailed debug output and transaction logging with timestamps

### Smart Liquidation Logic
- **Asset Exclusion**: Respects EXCLUDED_PAIRS list to protect specific assets (BTC, ETH, SOL by default)
- **Base Increment Compliance**: Calculates sellable amounts as multiples of base_increment (e.g., SEAM requires 0.1 minimum, PUMP requires 1 minimum)
- **Cash Asset Protection**: Automatically skips USD and other cash assets
- **Value-Based Prioritization**: Liquidates highest-value assets first for optimal execution
- **Fresh Data Updates**: Forces fresh products and active pairs data on each run for accuracy

### Safety Features
- **Dry Run Mode**: Test liquidation logic without placing actual orders
- **User Confirmation**: Requires explicit confirmation before executing liquidations
- **Rate Limiting**: Built-in delays between API calls and order placements
- **Error Handling**: Comprehensive exception handling with detailed error messages

## Configuration Parameters

### Order Placement Settings
- `DELAY_BETWEEN_ORDERS = 0.2` - Seconds between order placements (rate limiting)
- `DRY_RUN_MODE = False` - Set to True to simulate without placing orders
- `EXCLUDED_PAIRS = ["BTC", "ETH", "SOL"]` - Assets to exclude from liquidation
- `SHOW_UNSELLABLE_ASSETS = True` - Show unsellable assets (✗) in logs

### File Configuration
- `PRODUCTS_FILE = "products.json"` - File to store Coinbase product information
- `PRODUCTS_MAX_AGE_HOURS = 4` - Hours before refreshing products file
- `FORCE_FRESH_DATA = True` - Force fresh products and pairs data on each run
- `ACTIVE_PAIRS_FILE = "active_pairs.txt"` - File containing trading-enabled pairs

### API Settings
- `API_REQUEST_DELAY = 0.3` - Delay between API requests
- `RATE_LIMIT_DELAY = 2.0` - Wait time when rate limit exceeded
- `MAX_RETRIES = 3` - Maximum retries for API calls

### Logging Settings
- `DEBUG = False` - Enable debug logging
- `SHOW_TIMESTAMP = False` - Show timestamps in logs

## Prerequisites

### Required Files
1. **Environment Variables**: Create `.env` file with:
   ```
   COINBASE_API_KEY=organizations/fake-organization-id/apiKeys/fake-api-key-id
   COINBASE_API_SECRET=-----BEGIN EC PRIVATE KEY-----\nTHISISFAKEPRIVATEKEYDO-NOTUSEFAKEKEYINPROD\n-----END EC PRIVATE KEY-----\n
   ```

2. **Python Dependencies**: Install required packages:
   ```bash
   pip install python-dotenv coinbase-advanced-py requests
   ```

3. **Optional Files**:
   - `products.json` - Auto-created from Coinbase API
   - `active_pairs.txt` - Auto-detected from fetch_usd_pairs directory if available

## Usage

### Quick Start
```bash
python Coinbase_Liquidator.py
```

### Example Output
```
============================================================
COINBASE PORTFOLIO LIQUIDATOR
============================================================
[FRESH DATA MODE] - Updating products and active pairs data...
Loading products data...
Saved 1247 products to products.json
Loading active trading pairs...
Generated 891 active USD trading pairs from products.json
Fetching portfolio balances...
Found 18 assets in portfolio
------------------------------------------------------------
✓ PUMP     | Sellable:            7355 | Value: $   20.22 | Pair: PUMP-USD
✓ LINK     | Sellable:              25 | Value: $  387.50 | Pair: LINK-USD
✓ UNI      | Sellable:             150 | Value: $  142.50 | Pair: UNI-USD
✓ MATIC    | Sellable:            2000 | Value: $   85.40 | Pair: MATIC-USD
✗ BTC      | Balance:       0.001234 | Value: $   52.45 | Skip: Asset in EXCLUDED_PAIRS list
✗ ETH      | Balance:            0.15 | Value: $  425.75 | Skip: Asset in EXCLUDED_PAIRS list
✗ SOL      | Balance:             2.5 | Value: $  187.25 | Skip: Asset in EXCLUDED_PAIRS list
✗ SEAM     | Balance:     0.035101302 | Value: $    0.02 | Skip: Balance below base_increment (0.1)
✗ DUST     | Balance:            0.05 | Value: $    0.01 | Skip: Value $0.0100 below minimum
------------------------------------------------------------
Total Portfolio Value: $1,300.09
Liquidation Candidates: 4
Total Liquidation Value: $635.62
------------------------------------------------------------
Proceed with liquidating 4 assets ($635.62)? [y/N]: y
------------------------------------------------------------
Starting liquidation process...
Liquidating LINK: 25 ($387.50)...
✓ #1 Market sell placed: 25 LINK-USD
Liquidating UNI: 150 ($142.50)...
✓ #2 Market sell placed: 150 UNI-USD
Liquidating MATIC: 2000 ($85.40)...
✓ #3 Market sell placed: 2000 MATIC-USD
Liquidating PUMP: 7355 ($20.22)...
✓ #4 Market sell placed: 7355 PUMP-USD
------------------------------------------------------------
LIQUIDATION SUMMARY
------------------------------------------------------------
Successful Liquidations: 4
Failed Liquidations: 0
Total Liquidated Value: $635.62
Total Orders Placed: 4

✓ Liquidation process completed successfully!
Note: Market orders may take a few moments to execute.
Check your Coinbase Pro account for order status and USD balance.
============================================================
```

## How It Works

### 1. Balance Detection
- Uses Coinbase portfolio endpoint to get comprehensive asset data
- Handles mixed data types and API response variations
- Extracts available balances and USD values for all assets

### 2. Liquidation Analysis
- Loads products.json to get base_increment requirements for each trading pair
- Filters assets based on minimum USD value and base_increment compliance
- Checks active_pairs.txt to ensure pairs are currently trading-enabled
- Calculates exact sellable amounts as multiples of base_increment

### 3. Order Execution
- Sorts liquidation candidates by value (highest first)
- Places market sell orders with proper rate limiting
- Handles API errors, insufficient balance errors, and rate limiting
- Provides detailed feedback on each liquidation attempt

### 4. Safety Checks
- Skips cash assets (USD, etc.) automatically
- Requires user confirmation before placing orders
- Supports dry run mode for testing
- Comprehensive error handling and logging

## Base Increment Examples

The script automatically handles different base increment requirements:

- **PUMP-USD**: base_increment = 1 (whole numbers only)
  - Balance: 7355.5 → Sellable: 7355
- **SEAM-USD**: base_increment = 0.1 (0.1 minimum)
  - Balance: 0.035 → Sellable: 0 (below minimum)
- **BTC-USD**: base_increment = 0.00000001 (8 decimals)
  - Balance: 0.01234567 → Would be sellable: 0.01234567 (matches 8 decimals)
  - But: Sellable: 0 (excluded in EXCLUDED_PAIRS)

## Error Handling

### Common Scenarios
- **Rate Limiting**: Automatic backoff and retry with exponential delays
- **Insufficient Balance**: Graceful handling with detailed error messages
- **Invalid Pairs**: Automatic filtering using active_pairs.txt
- **API Errors**: Comprehensive exception handling with debug output

### Troubleshooting
1. **"No balances found"**: Check API credentials and portfolio access
2. **"No products data"**: Verify internet connection and API access
3. **"Rate limit hit"**: Increase DELAY_BETWEEN_ORDERS and API_REQUEST_DELAY
4. **"Insufficient balance"**: Normal for dust amounts below base_increment

## File Dependencies

- **products.json**: Automatically created from Coinbase API with product information
- **.env file**: Required with API credentials (COINBASE_API_KEY and COINBASE_API_SECRET)
- **Python dependencies**: Install via `pip install python-dotenv coinbase-advanced-py requests`

## Security Notes

- API keys are loaded from environment variables (never hardcoded)
- Market orders execute immediately at current market prices
- No limit orders or advanced trading features (liquidation focus)
- Dry run mode available for testing without financial risk

## Version History

### v1.06 (2025-01-25 21:37:00) - FRESH DATA IMPLEMENTATION
- **MAJOR ENHANCEMENT**: Forces fresh products and active pairs data on every run
- Eliminates stale data issues that could cause INVALID_PRICE_PRECISION errors
- Ensures accurate base_increment and quote_increment values for all calculations
- All product info lookups use current data for accurate decimal precision

### v1.05 (2025-01-25 21:23:15) - CODE SIMPLIFICATION
- **IMPROVED PRODUCT INFO HANDLING**: Simplified decimal precision logic
- More reliable product info fetching using direct API access
- Cleaner code that's easier to maintain and debug
- Same precision accuracy with simplified logic

### v1.04 (2025-01-25 21:18:45) - LIMIT ORDER FALLBACK FIX
- **BUG FIX**: Fixed "name 'load_products' is not defined" error in limit order fallback
- Changed incorrect function call to ensure_products_file() in place_limit_order_fallback()
- Limit order fallback now works correctly for TIME-USD, INV-USD, and other limit-only pairs

### v1.03 (2025-01-25 21:14:30) - LIMIT ORDER FALLBACK & LOG CONTROL
- **NEW FEATURE**: Added limit order fallback for pairs in limit-only mode
- Places limit orders 10% below market price using public order book data
- Added SHOW_UNSELLABLE_ASSETS config to control log verbosity
- Proper decimal precision ensures orders are accepted by Coinbase API

### v1.02 (2025-01-25 21:05:15) - AUTOMATED ACTIVE PAIRS DETECTION
- **MAJOR IMPROVEMENT**: Replaced manual active_pairs.txt with automated detection
- Dynamically filters for pairs with status="online" and trading_disabled=false
- Increased liquidation candidates from 1 asset to 14 assets
- Future-proof solution that adapts to new Coinbase trading pairs automatically

### v1.01 (2025-01-25 20:51:45) - CRITICAL ORDER SUCCESS FIX
- **MAJOR BUG FIX**: Fixed critical order success detection logic
- Orders were succeeding but being marked as failed due to incorrect API response interpretation
- Now correctly identifies successful orders and logs order IDs for tracking
- Eliminates false failure reports when orders are actually successful

### v1.00 (2025-01-25 20:33:39) - INITIAL RELEASE
- **COMPREHENSIVE LIQUIDATION SCRIPT**: Universal balance detection using portfolio endpoint
- Base increment validation from products.json with 4-hour auto-refresh
- Trading-enabled pair filtering for active USD pairs
- Market order placement with DELAY_BETWEEN_ORDERS = 0.2 seconds rate limiting
- Smart liquidation logic with value-based prioritization
- Safety features: dry run mode, user confirmation, comprehensive error handling
