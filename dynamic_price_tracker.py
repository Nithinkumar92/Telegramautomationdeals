import requests
from bs4 import BeautifulSoup
import os
import json
from dotenv import load_dotenv
from urllib.parse import quote_plus
from time import sleep
import re
from datetime import datetime

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9"
}

def get_search_results(keyword, max_products=5):
    search_url = f"https://www.amazon.in/s?k={quote_plus(keyword)}"
    response = requests.get(search_url, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")

    product_links = []
    for tag in soup.select("a.a-link-normal.s-no-outline")[:max_products]:
        relative_link = tag.get("href")
        if relative_link:
            full_link = "https://www.amazon.in" + relative_link.split("?")[0]
            if full_link not in product_links:
                product_links.append(full_link)
    return product_links

def get_amazon_price(url):
    try:
        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.content, "html.parser")
        price_tag = soup.find("span", {"class": "a-price-whole"})
        if not price_tag:
            return None
        price = price_tag.get_text().replace(",", "").strip()
        return float(price)
    except:
        return None

def get_amazon_rating(url):
    try:
        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.content, "html.parser")
        rating_tag = soup.find("span", {"class": "a-icon-alt"})
        if rating_tag:
            rating_text = rating_tag.get_text().split()[0]  # e.g., "4.3 out of 5 stars"
            try:
                return float(rating_text)
            except ValueError:
                return None
        return None
    except:
        return None

def get_amazon_title(url):
    try:
        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.content, "html.parser")
        title_tag = soup.find("span", {"id": "productTitle"})
        if title_tag:
            return title_tag.get_text().strip()
        return None
    except:
        return None

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    requests.post(url, data=payload)

def update_products_json(new_links):
    try:
        if os.path.exists("products.json"):
            with open("products.json", "r") as f:
                products = json.load(f)
        else:
            products = []
        # Add new links if not already present
        for link in new_links:
            if not any(p.get("url") == link for p in products):
                products.append({"url": link, "target_price": 1500})
        with open("products.json", "w") as f:
            json.dump(products, f, indent=2)
    except Exception as e:
        print(f"Error updating products.json: {e}")

def load_alerted_prices():
    if os.path.exists("alerted_prices.json"):
        with open("alerted_prices.json", "r") as f:
            return json.load(f)
    return {}

def save_alerted_prices(data):
    with open("alerted_prices.json", "w") as f:
        json.dump(data, f, indent=2)

def main():
    print(f"Script run at {datetime.now()}")
    with open("keywords.txt", "r") as file:
        keywords = [
            line.strip() for line in file
            if line.strip() and re.match(r'^[A-Za-z0-9 ]+$', line.strip())
        ]
    all_new_links = []
    alerted_prices = load_alerted_prices()
    for keyword in keywords:
        print(f"\n🔎 Searching for: {keyword}")
        product_links = get_search_results(keyword)
        all_new_links.extend(product_links)
        for link in product_links:
            print(f"Checking: {link}")
            price = get_amazon_price(link)
            rating = get_amazon_rating(link)
            title = get_amazon_title(link)
            if price and rating:
                if price < 1500 and rating >= 4.0:
                    last_alerted = alerted_prices.get(link)
                    if last_alerted != price:
                        alert_title = title if title else "(No Title Found)"
                        send_telegram_alert(
                            f"💸 Grab fast! Price drop!\n{alert_title}\n{link}\nCurrent Price: ₹{price} 🚀\n⭐ Rating: {rating}"
                        )
                        alerted_prices[link] = price
                        save_alerted_prices(alerted_prices)
                    else:
                        print(f"🔁 Already alerted for this price: ₹{price}")
                else:
                    print(f"🟡 No drop or rating too low. ₹{price}, ⭐ {rating}")
            else:
                print(f"⚠️ Couldn't fetch price or rating for keyword: {keyword} and link: {link}")
            sleep(2)
    update_products_json(all_new_links)

if __name__ == "__main__":
    main() 