import requests
from bs4 import BeautifulSoup
import json
import os
from dotenv import load_dotenv
from time import sleep

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

print("TELEGRAM_BOT_TOKEN:", TELEGRAM_BOT_TOKEN)
print("TELEGRAM_CHAT_ID:", TELEGRAM_CHAT_ID)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Language": "en-US,en;q=0.9"
}

def get_amazon_price(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        price_tag = soup.find("span", {"class": "a-price-whole"})

        if not price_tag:
            print("⚠️ Price tag not found. Amazon might've changed the page layout.")
            return None

        price = price_tag.get_text().replace(",", "").strip()
        return float(price)
    except Exception as e:
        print(f"❌ Error while fetching price: {e}")
        return None

def send_telegram_alert(product_url, current_price):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    message = f"🔥 Grab fast! Price dropped!\n\nProduct: {product_url}\nCurrent Price: ₹{current_price} 🚀"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    try:
        r = requests.post(url, data=payload)
        print(r.text)  # Print the error message from Telegram
        if r.status_code == 200:
            print("✅ Telegram alert sent.")
        else:
            print("⚠️ Failed to send Telegram alert.")
    except Exception as e:
        print(f"❌ Error sending message: {e}")

def main():
    with open("products.json", "r") as file:
        products = json.load(file)

    for product in products:
        url = product["url"]
        target_price = product["target_price"]
        
        print(f"\n🔍 Checking product: {url}")
        current_price = get_amazon_price(url)
        
        if current_price is None:
            print("Skipping due to fetch error.")
            continue
        
        print(f"💰 Current Price: ₹{current_price} | Target Price: ₹{target_price}")
        if current_price <= target_price:
            send_telegram_alert(url, current_price)
        else:
            print("📉 No price drop.")
        
        sleep(2)  # Delay to avoid bot detection

if __name__ == "__main__":
    main() 