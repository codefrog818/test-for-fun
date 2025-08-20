import os
from dotenv import load_dotenv
from web3 import Web3

# Load env
load_dotenv()
RPC_URL = os.getenv("RPC_URL")
w3 = Web3(Web3.HTTPProvider(RPC_URL))

if not w3.is_connected():
    raise RuntimeError("❌ Failed to connect to Ethereum RPC")
print("✅ Connected to Ethereum")

# Common tokens
TOKEN_MAP = {
    "USDC": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
    "USDT": "0xdac17f958d2ee523a2206206994597c13d831ec7",
    "DAI":  "0x6b175474e89094c44da98b954eedeac495271d0f",
    "WBTC": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
    "UNI":  "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984",
}

# ERC20 ABI (partial)
ERC20_ABI = [
    {"constant": True, "inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "account", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": False, "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
]

def get_contract(symbol_or_address):
    """Get ERC20 contract by symbol or address"""
    if symbol_or_address.upper() in TOKEN_MAP:
        token_address = TOKEN_MAP[symbol_or_address.upper()]
    else:
        token_address = symbol_or_address
    return w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=ERC20_ABI)

def get_token_info(symbol_or_address, wallet_address=None):
    """Print token info and optional wallet balance"""
    contract = get_contract(symbol_or_address)
    name = contract.functions.name().call()
    symbol = contract.functions.symbol().call()
    decimals = contract.functions.decimals().call()
    total_supply = contract.functions.totalSupply().call() / (10 ** decimals)

    print(f"\n📌 Token Info for {symbol}")
    print(f"   Name:         {name}")
    print(f"   Symbol:       {symbol}")
    print(f"   Decimals:     {decimals}")
    print(f"   Total Supply: {total_supply:,.0f} {symbol}")

    if wallet_address:
        wallet_address = Web3.to_checksum_address(wallet_address)
        balance = contract.functions.balanceOf(wallet_address).call() / (10 ** decimals)
        print(f"   Balance of {wallet_address}: {balance:,.4f} {symbol}")

def check_allowance(symbol_or_address, owner, spender):
    """Check allowance of spender from owner"""
    contract = get_contract(symbol_or_address)
    decimals = contract.functions.decimals().call()
    allowance = contract.functions.allowance(
        Web3.to_checksum_address(owner),
        Web3.to_checksum_address(spender)
    ).call() / (10 ** decimals)

    print(f"\n🔑 Allowance")
    print(f"   Owner:   {owner}")
    print(f"   Spender: {spender}")
    print(f"   Allowed: {allowance}")

def build_approve_tx(symbol_or_address, owner, spender, amount):
    """Build approve transaction (unsigned)"""
    contract = get_contract(symbol_or_address)
    decimals = contract.functions.decimals().call()
    amount_wei = int(amount * (10 ** decimals))

    tx = contract.functions.approve(
        Web3.to_checksum_address(spender),
        amount_wei
    ).build_transaction({
        "from": Web3.to_checksum_address(owner),
        "nonce": w3.eth.get_transaction_count(owner),
        "gas": 100000,
        "gasPrice": w3.to_wei("20", "gwei"),
    })
    print("\n📝 Approve transaction (unsigned):")
    print(tx)
    return tx

if __name__ == "__main__":
    # Example wallet (随便换个以太坊地址)
    my_wallet = "0x000000000000000000000000000000000000dead"
    spender = "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"  # UniswapV2Router02

    # 1. Token info
    get_token_info("USDC", my_wallet)

    # 2. Allowance check
    check_allowance("USDC", my_wallet, spender)

    # 3. Approve tx (模拟构建，不会发)
    build_approve_tx("USDC", my_wallet, spender, amount=1000)
