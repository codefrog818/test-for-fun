
import os
import datetime
import requests
import yfinance as yf
import smtplib
import logging
import sys
from fredapi import Fred
from email.mime.text import MIMEText
from email.header import Header
from dotenv import load_dotenv

class MacroBot:
    def __init__(self):
        load_dotenv()
        self.fred = Fred(api_key=os.getenv("FRED_API_KEY"))
        self.smtp_email = os.getenv("SMTP_EMAIL")
        self.smtp_pass = os.getenv("SMTP_PASS")
        self.to_email = os.getenv("TO_EMAIL", "").split(",")
        self.newsapi_key = os.getenv("NEWSAPI_KEY")
        self.today = datetime.date.today()
        self.report_lines = []

        log_path = os.path.join(os.path.dirname(__file__), "simple_info.log")
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[
                logging.FileHandler(log_path),
                logging.StreamHandler(sys.stdout)
            ]
        )

    def get_weather(self, city="Beijing"):
        try:
            url = f"https://wttr.in/{city}?format=%C+%t"
            res = requests.get(url, timeout=5)
            return res.text.strip()
        except Exception as e:
            logging.error(f"Weather error: {e}")
            return "Weather fetch error"

    def get_index_price(self, ticker, name):
        try:
            data = yf.Ticker(ticker).history(period="2d")
            today = data.iloc[-1]["Close"]
            yesterday = data.iloc[-2]["Close"]
            pct = (today - yesterday) / yesterday * 100
            return f"{name}: {today:.2f} ({pct:+.2f}%)"
        except Exception as e:
            logging.error(f"{name} error: {e}")
            return f"{name} fetch error"

    def get_bitcoin_price(self):
        try:
            url = "https://api.coingecko.com/api/v3/coins/bitcoin?localization=false&tickers=false&market_data=true"
            data = requests.get(url).json()
            price = data["market_data"]["current_price"]["usd"]
            change = data["market_data"]["price_change_percentage_24h"]
            return f"Bitcoin: {price:.2f} USD ({change:+.2f}%)"
        except Exception as e:
            logging.error(f"Bitcoin error: {e}")
            return "Bitcoin fetch error"

    def get_fx_rates(self):
        try:
            url = "https://api.frankfurter.app/latest?from=USD&to=GBP,EUR,JPY,CNY"
            res = requests.get(url).json()
            lines = ["\n📊 FX (USD base):"]
            for k, v in res["rates"].items():
                lines.append(f"USD/{k}: {v:.4f}")
            return lines
        except Exception as e:
            logging.error(f"FX error: {e}")
            return ["FX fetch error"]

    def get_interest_rates(self):
        lines = ["\n📉 US Interest Rates:"]
        try:
            sofr = self.fred.get_series("SOFR").dropna()
            effr = self.fred.get_series("EFFR").dropna()
            lines.append(f"SOFR: {sofr[-1]:.2f}% (as of {sofr.index[-1].date()})")
            lines.append(f"EFFR: {effr[-1]:.2f}% (as of {effr.index[-1].date()})")
        except Exception as e:
            logging.error(f"Rates error: {e}")
            lines.append("Rates fetch error")
        return lines

    def get_macro_indicators(self):
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
        lines = ["\n🌐 Macro Radar:"]
        for name, code in macro.items():
            try:
                series = self.fred.get_series(code).dropna()
                val = series[-1]
                date = series.index[-1].date()
                lines.append(f"{name}: {val:.2f} (as of {date})")
            except Exception as e:
                logging.error(f"{name} error: {e}")
                lines.append(f"{name} fetch error")
        return lines

    def get_macro_news(self):
        try:
            url = "https://newsapi.org/v2/top-headlines"
            params = {
                "category": "business",
                "language": "en",
                "apiKey": self.newsapi_key,
                "pageSize": 3
            }
            res = requests.get(url, params=params).json()
            articles = res.get("articles", [])
            lines = ["\n📰 Macro Market News:"]
            for art in articles:
                lines.append(f"- {art['title']}")
            return lines
        except Exception as e:
            logging.error(f"News error: {e}")
            return ["News fetch error"]

    def save_report(self, text):
        filename = f"report_{self.today}.txt"
        path = os.path.join(os.path.dirname(__file__), filename)
        with open(path, "w") as f:
            f.write(text)

    def send_email(self, subject, body):
        try:
            msg = MIMEText(body, "plain", "utf-8")
            msg["From"] = Header("MacroBot", "utf-8")
            msg["To"] = Header(", ".join(self.to_email), "utf-8")
            msg["Subject"] = Header(subject, "utf-8")

            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(self.smtp_email, self.smtp_pass)
            server.sendmail(self.smtp_email, self.to_email, msg.as_string())
            server.quit()
            logging.info("Email sent successfully.")
            return "✅ Email sent."
        except Exception as e:
            logging.error(f"Email error: {e}")
            return f"❌ Email failed: {e}"

    def run(self):
        self.report_lines = [
            f"📅 {self.today}",
            f"☁️ Weather Beijing: {self.get_weather()}",
            "",
            "📈 Market:",
            self.get_index_price("^GSPC", "S&P500"),
            self.get_bitcoin_price(),
            ""
        ]
        self.report_lines += self.get_fx_rates()
        self.report_lines += self.get_interest_rates()
        self.report_lines += self.get_macro_indicators()
        self.report_lines += self.get_macro_news()

        full_report = "\n".join(self.report_lines)
        self.save_report(full_report)
        status = self.send_email(f"📊 Macro Report {self.today}", full_report)

        print(status)
        print("✅ Script completed.")

if __name__ == "__main__":
    bot = MacroBot()
    bot.run()
