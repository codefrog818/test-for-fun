
import os
import datetime
import requests
import yfinance as yf
from fredapi import Fred
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

FRED_API_KEY = os.getenv("FRED_API_KEY")
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASS = os.getenv("SMTP_PASS")
TO_EMAIL = os.getenv("SMTP_PASS").split(',')

fred = Fred(api_key=FRED_API_KEY)

def get_weather(city="Beijing"):
    try:
        url = f"https://wttr.in/{city}?format=%C+%t"
        res = requests.get(url, timeout=5)
        return res.text.strip()
    except:
        return "Weather fetch failed"

def get_index_price(ticker, name):
    try:
        data = yf.Ticker(ticker).history(period="2d")
        today = data.iloc[-1]["Close"]
        yesterday = data.iloc[-2]["Close"]
        pct = (today - yesterday) / yesterday * 100
        return f"{name}: {today:.2f} ({pct:+.2f}%)"
    except:
        return f"{name}: Fetch error"

def get_bitcoin_price():
    try:
        url = "https://api.coingecko.com/api/v3/coins/bitcoin?localization=false&tickers=false&market_data=true"
        res = requests.get(url)
        data = res.json()
        price = data["market_data"]["current_price"]["usd"]
        change = data["market_data"]["price_change_percentage_24h"]
        return f"Bitcoin: {price:.2f} USD ({change:+.2f}%)"
    except:
        return "Bitcoin: Error"

def get_usd_fx_rates():
    try:
        url = "https://api.frankfurter.app/latest?from=USD&to=GBP,EUR,JPY,CNY"
        res = requests.get(url)
        data = res.json()
        lines = ["📊 FX (USD base):"]
        for k, v in data["rates"].items():
            lines.append(f"USD/{k}: {v:.4f}")
        return lines
    except:
        return ["FX fetch error"]

def get_interest_rates():
    lines = ["\n📉 US Interest Rates:"]
    try:
        sofr = fred.get_series("SOFR").dropna()
        effr = fred.get_series("EFFR").dropna()
        lines.append(f"SOFR: {sofr[-1]:.2f}% (as of {sofr.index[-1].date()})")
        lines.append(f"EFFR: {effr[-1]:.2f}% (as of {effr.index[-1].date()})")
    except Exception as e:
        lines.append(f"Rates: Error ({e})")
    return lines

macro = {
    "US CPI (YoY)": "CPIAUCSL",
    "Core CPI": "CPILFESL",
    "Fed Target Upper": "DFEDTARU",
    "10Y Yield": "GS10",
    "2Y Yield": "GS2",
    "Yield Spread": "T10Y2Y",
    "Unemployment": "UNRATE",
    "Retail Sales": "RSAFS",
    "GDP YoY": "A191RL1Q225SBEA",
    "Japan CPI": "JPNCPIALLMINMEI",
    "ECB Rate": "ECBMRO",
    "Euro GDP": "CLVMNACSCAB1GQEA19"
}

def get_macro():
    lines = ["\n🌐 Macro Radar:"]
    for k, code in macro.items():
        try:
            series = fred.get_series(code).dropna()
            value = series[-1]
            date = series.index[-1].date()
            lines.append(f"{k}: {value:.2f} (as of {date})")
        except:
            lines.append(f"{k}: Error")
    return lines

def send_email(subject, body):
    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["From"] = Header("MacroBot", "utf-8")
        msg["To"] = Header("Me", "utf-8")
        msg["Subject"] = Header(subject, "utf-8")

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASS)
        server.sendmail(SMTP_EMAIL, TO_EMAIL, msg.as_string())
        server.quit()
        print("✅ Email sent.")
    except Exception as e:
        print(f"❌ Email failed: {e}")

def save_report(text):
    today = datetime.date.today().strftime("%Y-%m-%d")
    path = os.path.join(os.path.dirname(__file__), f"report_{today}.txt")
    with open(path, "w") as f:
        f.write(text)

def main():
    today = datetime.date.today()
    lines = [
        f"📅 {today}",
        f"☁️ Weather Beijing: {get_weather()}",
        "",
        "📈 Market:",
        get_index_price("^GSPC", "S&P500"),
        get_bitcoin_price(),
        ""
    ]
    lines += get_usd_fx_rates()
    lines += get_interest_rates()
    lines += get_macro()

    full_report = "\n".join(lines)
    print(full_report)
    save_report(full_report)
    send_email(f"📊 Macro Report {today}", full_report)

if __name__ == "__main__":
    main()
