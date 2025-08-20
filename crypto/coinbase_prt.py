import json
import requests
from coinbase.rest import RESTClient

# === 读取 API key ===
with open(".vscode/coinbase_key.json") as f:
    creds = json.load(f)

api_key = creds["name"]
api_secret = creds["privateKey"]
client = RESTClient(api_key=api_key, api_secret=api_secret)


# === 获取所有账户（分页） ===
def get_all_accounts(client):
    accounts = []
    resp = client.get_accounts()
    accounts.extend(resp.accounts)
    while resp.has_next:
        resp = client.get_accounts(cursor=resp.cursor)
        accounts.extend(resp.accounts)
    return accounts


# === 获取价格（支持 USD/GBP） ===
def get_price(product_id="BTC-USD"):
    url = f"https://api.exchange.coinbase.com/products/{product_id}/ticker"
    resp = requests.get(url)
    if resp.status_code == 200:
        try:
            data = resp.json()
            return float(data["price"])
        except Exception:
            print(f"[ERROR] Failed to parse price for {product_id}: {resp.text}")
            return None
    else:
        print(f"[ERROR] HTTP {resp.status_code} for {product_id}: {resp.text}")
        return None


# === 打印 Portfolio ===
def print_portfolio(base_currency="USD"):
    print(f"=== Portfolio (non-zero, {base_currency}) ===")
    all_accounts = get_all_accounts(client)
    total_value = 0

    for acc in all_accounts:
        bal = acc.available_balance
        value = float(bal["value"]) if isinstance(bal, dict) else float(bal.value)
        currency = bal["currency"] if isinstance(bal, dict) else bal.currency

        if value > 0:
            price, val_in_base = None, None
            if currency != base_currency:
                product_id = f"{currency}-{base_currency}"
                price = get_price(product_id)
                if price:
                    val_in_base = value * price
            else:
                price, val_in_base = 1.0, value

            val_str = f"{val_in_base:.2f} {base_currency}" if val_in_base else "N/A"
            print(f"{currency}: {value} (~{val_str})")
            if val_in_base:
                total_value += val_in_base

    print(f"\nTotal Portfolio Value: {total_value:.2f} {base_currency}")


# === 执行 ===
print_portfolio("USD")
print()
print_portfolio("GBP")
