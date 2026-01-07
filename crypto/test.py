import os
import csv
import json
import time
from dotenv import load_dotenv
from web3 import Web3

# Load .env
load_dotenv()
RPC_URL = os.getenv("RPC_URL")

# Connect Web3
w3 = Web3(Web3.HTTPProvider(RPC_URL))
if not w3.is_connected():
    raise RuntimeError("❌ Failed to connect to Ethereum node")
print("✅ Connected to Ethereum Mainnet")

# USDC Contract
USDC_ADDRESS = Web3.to_checksum_address("0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48")
USDC_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "from", "type": "address"},
            {"indexed": True, "name": "to", "type": "address"},
            {"indexed": False, "name": "value", "type": "uint256"},
        ],
        "name": "Transfer",
        "type": "event",
    }
]
contract = w3.eth.contract(address=USDC_ADDRESS, abi=USDC_ABI)

# Load address labels
with open("crypto/address_labels.json", "r") as f:
    ADDRESS_LABELS = json.load(f)

def label_address(addr: str) -> str:
    return ADDRESS_LABELS.get(addr, addr[:6] + "..." + addr[-4:])

# CSV file
CSV_FILE = "usdc_whale_transfers.csv"
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["blockNumber", "txHash", "from", "to", "value_usdc", "from_label", "to_label"])

# Last block file
LAST_BLOCK_FILE = "last_block.txt"
if os.path.exists(LAST_BLOCK_FILE):
    with open(LAST_BLOCK_FILE, "r") as f:
        last_block = int(f.read().strip())
else:
    last_block = w3.eth.block_number
print(f"▶️ Starting from block {last_block}")

# Threshold
THRESHOLD = 100_000

while True:
    try:
        latest_block = w3.eth.block_number
        if latest_block > last_block:
            for block in range(last_block + 1, latest_block + 1):
                logs = contract.events.Transfer().get_logs(
                    from_block=block,
                    to_block=block
                )
                for event in logs:
                    from_addr = Web3.to_checksum_address(event["args"]["from"])
                    to_addr = Web3.to_checksum_address(event["args"]["to"])
                    value = event["args"]["value"] / 1e6

                    if value > THRESHOLD:
                        from_label = label_address(from_addr)
                        to_label = label_address(to_addr)
                        tx_hash = event["transactionHash"].hex()

                        print(f"🐋 Whale Transfer: {value:,.0f} USDC | Block {block}")
                        print(f"   From: {from_label} ({from_addr})")
                        print(f"   To:   {to_label} ({to_addr})")
                        print(f"   Tx:   {tx_hash}\n")

                        # Save to CSV
                        with open(CSV_FILE, "a", newline="") as f:
                            writer = csv.writer(f)
                            writer.writerow([block, tx_hash, from_addr, to_addr, value, from_label, to_label])

            # Save progress
            last_block = latest_block
            with open(LAST_BLOCK_FILE, "w") as f:
                f.write(str(last_block))

        time.sleep(5)  # poll every 5s

    except Exception as e:
        print("❌ Error:", e)
        time.sleep(10)
