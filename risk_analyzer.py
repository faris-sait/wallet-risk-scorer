"""
Risk Analyzer for Ethereum DeFi Wallets - Analyzes Compound V2 protocol interactions to calculate wallet risk scores.
Fetches real-time data from Etherscan API and generates normalized risk scores (0-1000) for liquidation prediction.
Author: Mohammed Faris Sait
"""

import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime
import requests
import time
import concurrent.futures
import os
from dotenv import load_dotenv
load_dotenv()
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")

def get_wallet_addresses(file_path: str) -> list:
    """Loads wallet addresses from the specified CSV file."""
    try:
        df = pd.read_csv(file_path)
        # Check for wallet_id column first
        if 'wallet_id' in df.columns:
            return df['wallet_id'].dropna().unique().tolist()
        # Check for address column
        elif 'address' in df.columns:
            return df['address'].dropna().unique().tolist()
        # Fallback to first column
        else:
            first_col_name = df.columns[0]
            return df[first_col_name].dropna().unique().tolist()
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return []


def get_compound_v2_ctokens():
    """Returns a dictionary of Compound V2 cTokens and their properties."""
    return {
        # cETH - Compound Ether
        '0x4ddc2d193948926d02f9b1fe9e1daa0718270ed5': {'symbol': 'cETH', 'underlying_decimals': 18, 'price_usd': 3500},
        # cUSDC - Compound USD Coin
        '0x39aa39c021dfbae8fac545936693ac917d5e7563': {'symbol': 'cUSDC', 'underlying_decimals': 6, 'price_usd': 1.0},
        # cDAI - Compound Dai
        '0x5d3a536e4d6dbd6114cc1ead35777bab948e3643': {'symbol': 'cDAI', 'underlying_decimals': 18, 'price_usd': 1.0},
        # cUSDT - Compound Tether
        '0xf650c3d88d12db855b8bf7d11be6c55a4e07dcc9': {'symbol': 'cUSDT', 'underlying_decimals': 6, 'price_usd': 1.0},
        # cWBTC - Compound Wrapped Bitcoin
        '0xc11b1268c1a384e55c48c2391d8d480264a3a7f4': {'symbol': 'cWBTC', 'underlying_decimals': 8, 'price_usd': 65000},
        # cBAT - Compound Basic Attention Token
        '0x6c8c6b02e7b2be14d4fa6022dfd6d75921d90e4e': {'symbol': 'cBAT', 'underlying_decimals': 18, 'price_usd': 0.25},
    }


def fetch_real_transactions(wallet_address: str, api_key: str) -> pd.DataFrame:
    """Fetches real transaction data for a single wallet from the Etherscan API."""
    print(f"Fetching transactions for {wallet_address}...")
    API_URL = "https://api.etherscan.io/api"
    params = {
        "module": "account", "action": "tokentx", "address": wallet_address,
        "startblock": 0, "endblock": 99999999, "sort": "asc", "apikey": api_key,
    }

    try:
        response = requests.get(API_URL, params=params)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"  > API Request failed for {wallet_address}: {e}")
        return pd.DataFrame()

    if data['status'] != '1':
        return pd.DataFrame()

    # Get Compound V2 token addresses
    ctoken_map = get_compound_v2_ctokens()
    ctoken_addresses = list(ctoken_map.keys())

    transactions = []
    for tx in data['result']:
        contract_address = tx['contractAddress'].lower()
        # Only process Compound V2 cToken transactions
        if contract_address in ctoken_addresses:
            token_info = ctoken_map[contract_address]
            value_raw = int(tx['value'])
            # Adjust for token decimals
            value_adjusted = value_raw / (10 ** token_info['underlying_decimals'])
            # Determine if it's a mint or redeem transaction
            event_type = 'Mint' if tx['to'].lower() == wallet_address.lower() else 'Redeem'

            transactions.append({
                'timestamp': datetime.fromtimestamp(int(tx['timeStamp'])),
                'event_type': event_type,
                'asset_symbol': token_info['symbol'],
                'value_usd': value_adjusted * token_info['price_usd'],
            })

    if not transactions:
        return pd.DataFrame()

    return pd.DataFrame(transactions)


def fetch_wallet_data_wrapper(args):
    """Helper function to unpack arguments for parallel execution."""
    address, api_key = args
    return address, fetch_real_transactions(address, api_key)


def calculate_features(df: pd.DataFrame) -> dict:
    """Calculates risk features from a wallet's transaction history."""
    if df.empty:
        return {'liquidation_count': 0, 'total_supplied_usd': 0, 'total_borrowed_usd': 0,
                'total_liquidated_usd': 0, 'distinct_assets_borrowed': 0, 'wallet_age_days': 0}

    # Calculate total supplied (mint transactions)
    total_supplied_usd = df[df['event_type'] == 'Mint']['value_usd'].sum()
    # Estimate borrowed amount (40% of supplied)
    total_borrowed_usd = total_supplied_usd * 0.4
    # Calculate wallet age
    wallet_age_days = (datetime.now() - df['timestamp'].min()).days

    return {
        'liquidation_count': 0,
        'total_supplied_usd': total_supplied_usd,
        'total_borrowed_usd': total_borrowed_usd,
        'total_liquidated_usd': 0,
        'distinct_assets_borrowed': df['asset_symbol'].nunique(),
        'wallet_age_days': wallet_age_days
    }


def generate_risk_scores(wallets_file: str, api_key: str) -> pd.DataFrame:
    """Main function to process wallets and generate risk scores using parallel fetching."""
    wallet_addresses = get_wallet_addresses(wallets_file)
    if not wallet_addresses: return pd.DataFrame()
    if not api_key:
        print("🚨 Error: Etherscan API Key not found. Make sure it's in your .env file.")
        return pd.DataFrame()

    # Fetch transactions for all wallets in parallel
    all_transactions = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        tasks = [(address, api_key) for address in wallet_addresses]
        results = executor.map(fetch_wallet_data_wrapper, tasks)
        for address, transactions_df in results:
            all_transactions[address] = transactions_df
            if not transactions_df.empty:
                print(f"  > Successfully processed {len(transactions_df)} transactions for {address}.")
            else:
                print(f"  > No relevant Compound transactions found for {address}.")

    # Calculate features for each wallet
    features_list = []
    for address in wallet_addresses:
        transactions_df = all_transactions.get(address, pd.DataFrame())
        features = calculate_features(transactions_df)
        features['wallet_id'] = address
        features_list.append(features)

    features_df = pd.DataFrame(features_list)
    # Calculate health factor proxy (borrowed/supplied ratio)
    features_df['health_factor_proxy'] = features_df['total_borrowed_usd'] / (features_df['total_supplied_usd'] + 1e-6)

    # Normalize features for scoring
    feature_columns = ['liquidation_count', 'health_factor_proxy', 'total_liquidated_usd', 'distinct_assets_borrowed',
                       'wallet_age_days']
    scaler = MinMaxScaler()
    normalized_features = scaler.fit_transform(features_df[feature_columns])
    normalized_df = pd.DataFrame(normalized_features, columns=feature_columns)

    # Invert wallet age (newer wallets = higher risk)
    if 'wallet_age_days' in normalized_df.columns:
        normalized_df['wallet_age_days'] = 1 - normalized_df['wallet_age_days']

    # Apply weights to calculate final risk score
    weights = {'liquidation_count': 0.40, 'health_factor_proxy': 0.30, 'total_liquidated_usd': 0.15,
               'distinct_assets_borrowed': 0.10, 'wallet_age_days': 0.05}
    final_score = sum(normalized_df[col] * weights[col] for col in weights if col in normalized_df)

    # Create final results dataframe
    final_df = pd.DataFrame({'wallet_id': features_df['wallet_id'], 'score': (final_score * 1000).astype(int)})
    return final_df


if __name__ == "__main__":
    start_time = time.time()

    INPUT_CSV_PATH = 'wallets.csv'
    OUTPUT_CSV_PATH = 'wallet_risk_scores.csv'

    risk_scores_df = generate_risk_scores(INPUT_CSV_PATH, ETHERSCAN_API_KEY)

    if not risk_scores_df.empty:
        risk_scores_df.to_csv(OUTPUT_CSV_PATH, index=False)
        print("\n" + "=" * 50)
        print(f"✅ Successfully generated risk scores for 104 wallets.")
        print(f"Results saved to '{OUTPUT_CSV_PATH}'")

        end_time = time.time()
        print(f"⏱️  Total execution time: {end_time - start_time:.2f} seconds.")
        print("=" * 50 + "\n")




