import os
import requests
from dotenv import load_dotenv
from web3 import Web3

# Load env
load_dotenv()
RPC_URL = os.getenv("RPC_URL")
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
w3 = Web3(Web3.HTTPProvider(RPC_URL))

if not w3.is_connected():
    raise RuntimeError("❌ Failed to connect to Ethereum RPC")
print("✅ Connected to Ethereum")

# --- Utility: checksum wrapper ---
def checksum(addr: str) -> str:
    return Web3.to_checksum_address(addr)

# --- Etherscan Label Lookup ---
def get_address_label(address: str) -> str:
    """
    Query Etherscan for address label.
    If not found, return the raw address.
    """
    try:
        url = f"https://api.etherscan.io/api"
        params = {
            "module": "account",
            "action": "txlist",
            "address": checksum(address),
            "startblock": 0,
            "endblock": 0,
            "page": 1,
            "offset": 1,
            "sort": "asc",
            "apikey": ETHERSCAN_API_KEY,
        }
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            # ⚠️ Etherscan 没有直接的 "label" API，但可以通过解析响应的 "to"/"from" 识别
            # 如果你有 Etherscan Pro，可以用 "contract" 模块直接查标签
            # 这里先返回简化版
            return f"{address} (queried from Etherscan)"
        else:
            return address
    except Exception as e:
        return f"{address} (lookup failed: {e})"

# --- Demo ---
if __name__ == "__main__":
    spender = "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"  # Uniswap V2 Router

    label = get_address_label(spender)
    print(f"🔍 Label for spender: {label}")
