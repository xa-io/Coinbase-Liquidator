# Coinbase Liquidator v1.11

Automated portfolio liquidation script that converts all available token balances to USD using market orders and limit orders when needed. 

## Why This Script Exists

Many cryptocurrency exchanges provide a built-in "Convert Dust to USD" feature that allows users to easily liquidate small token balances ("dust") into cash with a single click. However, Coinbase Exchange lacks this functionality, requiring traders to manually sell each small balance individually - a tedious and time-consuming process when dealing with dozens of small positions.

This script automates that entire process, intelligently handling all token balances according to Coinbase's specific trading requirements and limitations. Whether you need to clean up dust accumulation or quickly exit all positions during volatile market conditions, Coinbase Liquidator streamlines the entire liquidation workflow into a single command.

**Created:** 2025-07-25

**Author:** https://github.com/xa-io

**Last Updated:** 2025-07-27 16:32:33

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
- **User Confirmation**: Requires explicit confirmation before executing liquidations (can be disabled)
- **Automated Execution**: Optional AUTO_CONFIRM_LIQUIDATION for non-interactive environments
- **Rate Limiting**: Built-in delays between API calls and order placements
- **Error Handling**: Comprehensive exception handling with detailed error messages

## Configuration Parameters

### Order Placement Settings
- `DELAY_BETWEEN_ORDERS = 0.2` - Seconds between order placements (rate limiting)
- `DRY_RUN_MODE = False` - Set to True to simulate without placing orders
- `EXCLUDED_PAIRS = ["BTC", "ETH", "SOL"]` - Assets to exclude from liquidation
- `SHOW_UNSELLABLE_ASSETS = False` - Show unsellable assets (✗) in logs
- `AUTO_CONFIRM_LIQUIDATION = False` - Set to True to skip confirmation prompt and auto-liquidate

### Value Filtering Settings
- `IGNORE_MIN_VALUE = 5` - Skip assets with value below this USD amount (0 to disable)
- `IGNORE_MAX_VALUE = 1000` - Skip assets with value above this USD amount (0 to disable)
- `SHOW_IGNORED = True` - Show ignored assets due to value filtering
- `LOG_OUTPUT = True` - Enable logging to Liquidations folder with timestamped files

### File Configuration
- `PRODUCTS_FILE = "products.json"` - File to store Coinbase product information
- `PRODUCTS_MAX_AGE_HOURS = 4` - Hours before refreshing products file
- `FORCE_FRESH_DATA = True` - Force fresh products and pairs data on each run

### API Settings
- `API_REQUEST_DELAY = 0.3` - Delay between API requests
- `RATE_LIMIT_DELAY = 2.0` - Wait time when rate limit exceeded
- `MAX_RETRIES = 3` - Maximum retries for API calls

### Logging Settings
- `DEBUG = False` - Enable debug logging
- `SHOW_TIMESTAMP = True` - Show timestamps in logs
- `LOG_OUTPUT = True` - Enable comprehensive logging to Liquidations folder

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

## Usage

### Quick Start
```bash
python "Coinbase_Liquidator v1.11.py"
```

### Example Output
```
============================================================
COINBASE PORTFOLIO LIQUIDATOR
============================================================
Loading products data...
Loading active trading pairs...
Fetching portfolio balances...
Found 97 assets in portfolio
------------------------------------------------------------
✗ SOL      | Excluded:               0 | Value: $      0.71 | Pair: SOL-USD
✗ BTC      | Excluded:      0.00029942 | Value: $     35.67 | Pair: BTC-USD
✓ PLU      | Sellable:            1.00 | Value: $    0.65 | Pair: PLU-USD
✓ PUMP     | Sellable:            7355 | Value: $   20.22 | Pair: PUMP-USD
✓ LINK     | Sellable:              25 | Value: $  387.50 | Pair: LINK-USD
✓ UNI      | Sellable:             150 | Value: $  142.50 | Pair: UNI-USD
------------------------------------------------------------
Total Portfolio Value: $587.62
Liquidation Candidates: 4
Total Liquidation Value: $550.87
------------------------------------------------------------
Auto-liquidating 4 assets ($550.87)...
------------------------------------------------------------
Starting liquidation process...
Liquidating PLU: 1.00 ($0.65)...
✓ #1 Market sell placed: 1.00 PLU-USD (Order ID: N/A)
Liquidating PUMP: 7355 ($20.22)...
✓ #2 Market sell placed: 7355 PUMP-USD (Order ID: N/A)
Liquidating LINK: 25 ($387.50)...
✓ #3 Market sell placed: 25 LINK-USD (Order ID: N/A)
Liquidating UNI: 150 ($142.50)...
✓ #4 Market sell placed: 150 UNI-USD (Order ID: N/A)
------------------------------------------------------------
LIQUIDATION SUMMARY
------------------------------------------------------------
Successful Liquidations: 4
Failed Liquidations: 0
Total Liquidated Value: $550.87
Total Orders Placed: 4
✓ Liquidation process completed successfully!
Note: Open orders remain in your account.
Note: Market orders may take a few moments to execute.
Check your Coinbase account for order status and balances.
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

## Logging System

### Comprehensive Console Logging
When `LOG_OUTPUT = True` (default), the script creates comprehensive log files that capture the entire console output for each liquidation run.

### Log File Structure
- **Location**: `Liquidations/` folder in the script directory
- **Filename Format**: `Liquidations - YYYY-MM-DD_HH-MM-SS.log`
- **Content**: Complete console output with timestamps for each entry

### Log File Contents
Each log file includes:
- Script version and configuration settings
- Complete liquidation analysis and decision process
- All asset evaluations (sellable, excluded, ignored)
- Order placement attempts and results
- Final liquidation summary with totals
- Error messages and debug information (if enabled)

### Example Log Entry Format
```
Coinbase Liquidator v1.11 Log
Started: 2025-07-27 16:32:33
Configuration: DRY_RUN=True, AUTO_CONFIRM=False
Excluded Assets: ['BTC', 'ETH', 'SOL']
================================================================================

[2025-07-27 16:32:33] ============================================================
[2025-07-27 16:32:33] COINBASE PORTFOLIO LIQUIDATOR
[2025-07-27 16:32:33] ============================================================
[2025-07-27 16:32:33] Loading products data...
```

### Log Management
- Each script run creates a new timestamped log file
- Log files are automatically created in the `Liquidations/` directory
- No automatic cleanup - manage log files manually as needed
- Logs are written in real-time with buffering for performance

## Security Notes

- API keys are loaded from environment variables (never hardcoded)
- Market orders execute immediately at current market prices
- No limit orders or advanced trading features (liquidation focus)
- Dry run mode available for testing without financial risk

## Version History

### v1.11 (2025-07-27 16:32:33) - COMPREHENSIVE LOGGING SYSTEM
- **NEW LOGGING FUNCTIONALITY**: Added LOG_OUTPUT configuration parameter (default: True)
- Creates Liquidations folder for organized log file storage with timestamped files
- Complete console output capture with timestamps and log buffer system
- Enhanced log capture includes all liquidation analysis, decisions, and results
- **IMPORT OPTIMIZATION**: Moved all imports to top of script for better organization
- Updated script header, README.md, and changelog with comprehensive documentation
- Backup created: Coinbase_Liquidator v1.10 - 2025-07-27_16-32-33.py

### v1.10 - ENHANCED LIQUIDATION LOGIC
- Enhanced liquidation logic with improved error handling and order placement reliability
- Improved market order placement with better success detection
- Enhanced API error handling and retry mechanisms
- Better order validation and processing

### v1.09 (2025-07-27 11:44:35) - ENHANCED IGNORED ASSETS DISPLAY
- **NEW FEATURE**: Added SHOW_IGNORED parameter to display ignored assets with enhanced formatting
- Shows ignored assets with "✓ ASSET | Ignored: amount | Value: $X.XX | Pair: ASSET-USD" format
- Provides better visibility into which high-value or low-value assets are being skipped
- Enhanced spacing and formatting for improved readability

### v1.08 (2025-07-27 11:31:44) - VALUE FILTERING IMPLEMENTATION
- **NEW FEATURE**: Added IGNORE_MIN_VALUE and IGNORE_MAX_VALUE configuration parameters
- Skip assets below minimum USD value threshold (default: $5)
- Skip assets above maximum USD value threshold (default: $1000) 
- Set either value to 0 to disable that filter
- Enhanced liquidation control for protecting high-value assets and ignoring dust

### v1.07 (2025-07-26 00:11:50) - AUTO_CONFIRM_LIQUIDATION & README UPDATE (STABLE VERSION)
- **NEW FEATURE**: Added AUTO_CONFIRM_LIQUIDATION for non-interactive environments
- **README UPDATE**: Updated README with v1.07 timestamp and new feature documentation

### v1.06 (2025-07-25 21:37:00) - FRESH DATA IMPLEMENTATION
- **MAJOR ENHANCEMENT**: Forces fresh products and active pairs data on every run
- Eliminates stale data issues that could cause INVALID_PRICE_PRECISION errors
- Ensures accurate base_increment and quote_increment values for all calculations
- All product info lookups use current data for accurate decimal precision

### v1.05 (2025-07-25 21:23:15) - CODE SIMPLIFICATION
- **IMPROVED PRODUCT INFO HANDLING**: Simplified decimal precision logic
- More reliable product info fetching using direct API access
- Cleaner code that's easier to maintain and debug
- Same precision accuracy with simplified logic

### v1.04 (2025-07-25 21:18:45) - LIMIT ORDER FALLBACK FIX
- **BUG FIX**: Fixed "name 'load_products' is not defined" error in limit order fallback
- Changed incorrect function call to ensure_products_file() in place_limit_order_fallback()
- Limit order fallback now works correctly for TIME-USD, INV-USD, and other limit-only pairs

### v1.03 (2025-07-25 21:14:30) - LIMIT ORDER FALLBACK & LOG CONTROL
- **NEW FEATURE**: Added limit order fallback for pairs in limit-only mode
- Places limit orders 10% below market price using public order book data
- Added SHOW_UNSELLABLE_ASSETS config to control log verbosity
- Proper decimal precision ensures orders are accepted by Coinbase API

### v1.02 (2025-07-25 21:05:15) - AUTOMATED ACTIVE PAIRS DETECTION
- **MAJOR IMPROVEMENT**: Replaced manual active_pairs with automated detection
- Dynamically filters for pairs with status="online" and trading_disabled=false
- Increased liquidation candidates from 1 asset to 14 assets
- Future-proof solution that adapts to new Coinbase trading pairs automatically

### v1.01 (2025-07-25 20:51:45) - CRITICAL ORDER SUCCESS FIX
- **MAJOR BUG FIX**: Fixed critical order success detection logic
- Orders were succeeding but being marked as failed due to incorrect API response interpretation
- Now correctly identifies successful orders and logs order IDs for tracking
- Eliminates false failure reports when orders are actually successful

### v1.00 (2025-07-25 20:33:39) - INITIAL RELEASE
- **COMPREHENSIVE LIQUIDATION SCRIPT**: Universal balance detection using portfolio endpoint
- Base increment validation from products.json with 4-hour auto-refresh
- Trading-enabled pair filtering for active USD pairs
- Market order placement with DELAY_BETWEEN_ORDERS = 0.2 seconds rate limiting
- Smart liquidation logic with value-based prioritization
- Safety features: dry run mode, user confirmation, comprehensive error handling
