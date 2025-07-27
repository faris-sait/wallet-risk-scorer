# 🔍 Wallet Risk Scoring From Scratch

## 🌟 Overview

The Risk Analyzer is a Python script that evaluates the risk profile of cryptocurrency wallets by analyzing their transaction history on Ethereum 🔷, specifically focusing on Compound V2 protocol interactions. It fetches real transaction data from the Etherscan API 📡, calculates various risk metrics 📊, and generates normalized risk scores for each wallet 💳.

## ✨ Features

- **📡 Real-time Data Fetching**: Retrieves transaction data from Etherscan API
- **🏦 Compound V2 Integration**: Specifically analyzes interactions with Compound V2 cTokens
- **⚡ Parallel Processing**: Uses concurrent execution for efficient API calls
- **🎯 Risk Scoring**: Generates weighted risk scores based on multiple factors
- **📁 CSV Input/Output**: Reads wallet addresses from CSV and outputs results to CSV

## 🛠️ Requirements

### 📦 Dependencies

```python
pip install pandas scikit-learn requests python-dotenv
```

### 🔐 Environment Setup

Create a `.env` file in the project directory:

```
ETHERSCAN_API_KEY=your_etherscan_api_key_here
```

### 📄 Input File

Create a `wallets.csv` file with wallet addresses. The script supports multiple column names:
- `wallet_id` 🆔
- `address` 📍
- Or any first column containing wallet addresses 📋

## ⚙️ Core Functions

### 📖 `get_wallet_addresses(file_path: str) -> list`

**🎯 Purpose**: Loads wallet addresses from a CSV file.

**📥 Parameters**:
- `file_path`: Path to the CSV file containing wallet addresses

**📤 Returns**: List of unique wallet addresses

**🚨 Error Handling**: Returns empty list if file not found

### 🏦 `get_compound_v2_ctokens() -> dict`

**🎯 Purpose**: Returns configuration for supported Compound V2 cTokens.

**📤 Returns**: Dictionary mapping contract addresses to token information:
- `symbol`: Token symbol (e.g., 'cETH', 'cUSDC') 🏷️
- `underlying_decimals`: Decimal places for the underlying asset 🔢
- `price_usd`: Estimated USD price for calculations 💰

**🪙 Supported Tokens**:
- 🌐 cETH (Compound Ether)
- 💵 cUSDC (Compound USD Coin)
- 🏛️ cDAI (Compound Dai)
- 💰 cUSDT (Compound Tether)
- 🟡 cWBTC (Compound Wrapped Bitcoin)
- 🦇 cBAT (Compound Basic Attention Token)

### 🔄 `fetch_real_transactions(wallet_address: str, api_key: str) -> pd.DataFrame`

**🎯 Purpose**: Fetches transaction data for a single wallet from Etherscan API.

**📥 Parameters**:
- `wallet_address`: Ethereum wallet address 📱
- `api_key`: Etherscan API key 🔑

**📤 Returns**: DataFrame with columns:
- `timestamp`: Transaction timestamp ⏰
- `event_type`: 'Mint' or 'Redeem' 🔄
- `asset_symbol`: cToken symbol 🏷️
- `value_usd`: USD value of the transaction 💵

**🔧 API Configuration**:
- 🌐 Endpoint: Etherscan token transactions API
- 📦 Block range: 0 to 99999999 (all blocks)
- ⬆️ Sort order: Ascending by timestamp

### 📊 `calculate_features(df: pd.DataFrame) -> dict`

**🎯 Purpose**: Calculates risk-related features from transaction history.

**📥 Parameters**:
- `df`: DataFrame of wallet transactions

**📤 Returns**: Dictionary with risk features:
- `liquidation_count`: Number of liquidation events (currently 0) ⚠️
- `total_supplied_usd`: Total USD value supplied to Compound 💰
- `total_borrowed_usd`: Estimated borrowed amount (40% of supplied) 📈
- `total_liquidated_usd`: Total USD value liquidated (currently 0) 💥
- `distinct_assets_borrowed`: Number of unique assets interacted with 🔄
- `wallet_age_days`: Age of wallet in days 📅

### 🎯 `generate_risk_scores(wallets_file: str, api_key: str) -> pd.DataFrame`

**🎯 Purpose**: Main orchestration function that processes all wallets and generates risk scores.

**📥 Parameters**:
- `wallets_file`: Path to CSV file with wallet addresses 📁
- `api_key`: Etherscan API key 🔑

**📤 Returns**: DataFrame with columns:
- `wallet_id`: Wallet address 🆔
- `score`: Risk score (0-1000 scale) 📊

**🔄 Process Flow**:
1. 📖 Load wallet addresses from CSV
2. 📡 Fetch transaction data in parallel (max 5 concurrent requests)
3. 🧮 Calculate features for each wallet
4. 📏 Normalize features using MinMaxScaler
5. ⚖️ Apply weighted scoring algorithm
6. 📊 Scale final scores to 0-1000 range

## 🎯 Risk Scoring Algorithm

### ⚖️ Feature Weights

The risk score is calculated using weighted features:

| Feature 📊 | Weight ⚖️ | Description 📝 |
|---------|--------|-------------|
| `liquidation_count` | 40% ⚠️ | Historical liquidation events |
| `health_factor_proxy` | 30% 🩺 | Ratio of borrowed to supplied funds |
| `total_liquidated_usd` | 15% 💥 | Total value lost to liquidations |
| `distinct_assets_borrowed` | 10% 🔄 | Portfolio diversification |
| `wallet_age_days` | 5% 📅 | Account maturity (inverted) |

### 📏 Normalization

- 📊 All features are normalized to 0-1 scale using MinMaxScaler
- 🔄 `wallet_age_days` is inverted (1 - normalized_value) so newer wallets have higher risk
- 📈 Final score is scaled to 0-1000 range for readability

### 🩺 Health Factor Proxy

```python
health_factor_proxy = total_borrowed_usd / (total_supplied_usd + 1e-6)
```

This approximates the health factor used in DeFi protocols, where higher ratios indicate higher risk ⚠️.

## 🚀 Usage

### 📝 Basic Usage

```python
from risk_analyzer import generate_risk_scores
import os

# 🔑 Load API key from environment
api_key = os.getenv("ETHERSCAN_API_KEY")

# 🎯 Generate risk scores
risk_scores = generate_risk_scores('wallets.csv', api_key)

# 💾 Save results
risk_scores.to_csv('wallet_risk_scores.csv', index=False)
```

### 💻 Command Line Execution

```bash
python risk_analyzer.py
```

This will:
1. 📖 Read wallet addresses from `wallets.csv`
2. ⚙️ Process transactions for each wallet
3. 🎯 Generate risk scores
4. 💾 Save results to `wallet_risk_scores.csv`

## ⚡ Performance Considerations

### 🚀 Parallel Processing

- ⚡ Uses `ThreadPoolExecutor` with max 5 workers
- 🛡️ Prevents API rate limiting while maintaining efficiency
- 🔄 Each wallet is processed independently

### 📊 API Rate Limits

- ⏰ Etherscan API has rate limits (typically 5 requests/second for free tier)
- 🛡️ Built-in error handling for failed requests
- ⚖️ Concurrent execution designed to respect rate limits

### 💾 Memory Usage

- 📦 Processes wallets in batches to manage memory
- 📊 DataFrames are created incrementally
- 🧮 Large transaction histories may require memory optimization

## 🚨 Error Handling

### 📡 API Errors

- 🛡️ Catches `requests.exceptions.RequestException`
- 📊 Returns empty DataFrame for failed requests
- ➡️ Continues processing other wallets

### 📁 File Errors

- 🔍 Handles missing input CSV files
- ✅ Validates CSV structure and column names
- 💬 Provides informative error messages

### 🔍 Data Validation

- ❌ Checks for empty transaction sets
- 🛡️ Handles division by zero in calculations
- ✅ Validates API response format

## 📤 Output Format

### 💻 Console Output

```
📡 Fetching transactions for 0x1234...
  ✅ Successfully processed 45 transactions for 0x1234.
  ❌ No relevant Compound transactions found for 0x5678.

🎉==================================================
✅ Successfully generated risk scores for 104 wallets.
💾 Results saved to 'wallet_risk_scores.csv'
⏱️  Total execution time: 23.45 seconds.
🎉==================================================
```

### 📄 CSV Output

```csv
wallet_id,score
0x1234567890abcdef...,245
0xabcdef1234567890...,678
0x9876543210fedcba...,123
```

## ⚠️ Limitations

### 🚧 Current Limitations

1. **🏦 Limited Protocol Coverage**: Only analyzes Compound V2 transactions
2. **💰 Static Price Data**: Uses hardcoded token prices instead of real-time data
3. **⚠️ Simplified Liquidation Detection**: Currently doesn't detect actual liquidation events
4. **📅 Historical Data Only**: Doesn't consider current market conditions

### 🚀 Future Enhancements

1. **🌐 Multi-Protocol Support**: Extend to Aave, MakerDAO, and other DeFi protocols
2. **📈 Real-time Price Feeds**: Integrate with price APIs (CoinGecko, CoinMarketCap)
3. **🧠 Advanced Risk Metrics**: Implement volatility analysis, correlation metrics
4. **🤖 Machine Learning**: Train models on historical liquidation data

## 🔧 Troubleshooting

### 🚨 Common Issues

**🔑 "API Key not found"**
- ✅ Ensure `.env` file exists in project directory
- 🔍 Verify `ETHERSCAN_API_KEY` is correctly set
- ✅ Check API key validity on Etherscan

**❌ "No transactions found"**
- 🏦 Wallet may not have interacted with Compound V2
- 📍 Check wallet address format (should be valid Ethereum address)
- 🌐 Verify network connectivity

**⏰ "Rate limit exceeded"**
- ⬇️ Reduce `max_workers` in ThreadPoolExecutor
- ⏱️ Add delays between API calls
- 💰 Consider upgrading to paid Etherscan API plan

## ⚙️ Configuration

### 🎛️ Customization Options

**🏦 Modify Token Support**:
```python
# 🆕 Add new cTokens to get_compound_v2_ctokens()
def get_compound_v2_ctokens():
    return {
        # 🏛️ Existing tokens...
        '0xnewtoken': {'symbol': 'cNEW', 'underlying_decimals': 18, 'price_usd': 100}
    }
```

**⚖️ Adjust Risk Weights**:
```python
# 🎯 Modify weights in generate_risk_scores()
weights = {
    'liquidation_count': 0.50,  # ⬆️ Increase liquidation importance
    'health_factor_proxy': 0.25,
    # ... 🏷️ other weights
}
```

**⚡ Change Concurrency**:
```python
# 🚀 Modify max_workers in ThreadPoolExecutor
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
```

## 🔐 Security Considerations

- 🔑 API keys are loaded from environment variables (never hardcoded)
- 🤐 No sensitive data is logged or printed
- 🔒 All API requests use HTTPS
- 🛡️ Input validation prevents injection attacks

## 📜 License and Disclaimer

This tool is for educational and research purposes 🎓. Users should:
- ✅ Verify all risk calculations independently
- ❌ Not rely solely on these scores for financial decisions
- 📖 Understand the limitations and assumptions made
- ⚖️ Comply with relevant regulations and terms of service
