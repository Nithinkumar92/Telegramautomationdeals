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

PRICE_THRESHOLD = 150000  # Set your global price threshold here

def get_search_results(keyword, max_products=5):
    search_url = f"https://www.amazon.in/s?k={quote_plus(keyword)}"
    response = requests.get(search_url, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")

    product_links = []
    for tag in soup.select("a.a-link-normal.s-no-outline"):
        relative_link = tag.get("href")
        if relative_link:
            full_link = "https://www.amazon.in" + relative_link.split("?")[0]
            if '/dp/' in full_link and full_link not in product_links:
                product_links.append(full_link)
        if len(product_links) >= max_products:
            break
    return product_links

def get_amazon_price(url):
    try:
        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.content, "html.parser")
        # Extract current price
        price = None
        price_whole = soup.find("span", {"class": "a-price-whole"})
        price_fraction = soup.find("span", {"class": "a-price-fraction"})
        if price_whole:
            price_text = price_whole.get_text().replace(",", "").replace("₹", "").strip()
            if price_fraction:
                price_text += "." + price_fraction.get_text().strip()
            try:
                price = float(price_text)
            except ValueError:
                pass
        # Fallback to other selectors for current price
        if price is None:
            selectors = [
                ("span", {"id": "priceblock_ourprice"}),
                ("span", {"id": "priceblock_dealprice"}),
                ("span", {"id": "priceblock_saleprice"}),
                ("span", {"class": "a-offscreen"}),
            ]
            for tag, attrs in selectors:
                price_tag = soup.find(tag, attrs)
                if price_tag:
                    price_text = price_tag.get_text().replace(",", "").replace("₹", "").strip()
                    try:
                        price = float(price_text.split()[0])
                        break
                    except ValueError:
                        continue
        # Extract actual/list price (original price)
        actual_price = None
        list_price_selectors = [
            ("span", {"id": "priceblock_listprice"}),
            ("span", {"class": "priceBlockStrikePriceString"}),
            ("span", {"class": "a-text-strike"}),
        ]
        for tag, attrs in list_price_selectors:
            list_price_tag = soup.find(tag, attrs)
            if list_price_tag:
                list_price_text = list_price_tag.get_text().replace(",", "").replace("₹", "").strip()
                try:
                    actual_price = float(list_price_text.split()[0])
                    break
                except ValueError:
                    continue
        if price is None and actual_price is None:
            print("DEBUG: Price not found. HTML snippet:")
            print(soup.prettify()[:500])
        return price, actual_price
    except Exception as e:
        print(f"Error fetching price: {e}")
        return None, None

def get_amazon_rating(url):
    try:
        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.content, "html.parser")
        selectors = [
            ("span", {"class": "a-icon-alt"}),
            ("span", {"data-asin": True, "class": "a-size-base a-color-base"}),
        ]
        for tag, attrs in selectors:
            rating_tag = soup.find(tag, attrs)
            if rating_tag:
                rating_text = rating_tag.get_text().split()[0]
                try:
                    return float(rating_text)
                except ValueError:
                    continue
        print("DEBUG: Rating not found. HTML snippet:")
        print(soup.prettify()[:500])
        return None
    except Exception as e:
        print(f"Error fetching rating: {e}")
        return None

def get_amazon_title(url):
    try:
        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.content, "html.parser")
        selectors = [
            ("span", {"id": "productTitle"}),
            ("h1", {"id": "title"}),
            ("span", {"class": "a-size-large product-title-word-break"}),
        ]
        for tag, attrs in selectors:
            title_tag = soup.find(tag, attrs)
            if title_tag:
                return title_tag.get_text().strip()
        print("DEBUG: Title not found. HTML snippet:")
        print(soup.prettify()[:500])
        return None
    except Exception as e:
        print(f"Error fetching title: {e}")
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
        keywords = [line.strip() for line in file if line.strip()]
    all_new_links = []
    alerted_prices = load_alerted_prices()
    for keyword in keywords:
        print(f"\n🔎 Searching for: {keyword}")
        product_links = get_search_results(keyword)
        all_new_links.extend(product_links)
        for link in product_links:
            print(f"Checking: {link}")
            price, actual_price = get_amazon_price(link)
            title = get_amazon_title(link)
            rating = get_amazon_rating(link)
            
            alert_title = title if title else "(Title not found)"
            price_info = f"Current Price: ₹{price}" if price else "Price not found"
            actual_price_info = f"Actual Price: ₹{actual_price}" if actual_price else ""
            rating_info = f"Rating: {rating}" if rating else "Rating not found"
            print(price_info, actual_price_info)
            print(rating_info)
            if price is not None and rating is not None:
                if price < PRICE_THRESHOLD and rating >= 4.0:
                    last_alerted = alerted_prices.get(link)
                    if last_alerted != price:
                        send_telegram_alert(
                            f"🔥🎉 HOT DEAL ALERT! 🎉🔥\n\n🛒 {alert_title}\n🔗 {link}\n💰 {price_info} ✅\n💰 {actual_price_info} ❌\n⭐️ {rating_info}\n\nHurry, before it's gone! 🚀🤑"
                        )
                        alerted_prices[link] = price
                        save_alerted_prices(alerted_prices)
                    else:
                        print(f"🔁 Already alerted for this price: ₹{price}")
                else:
                    print(f"🟡 No drop. ₹{price}, Rating: {rating}")
            else:
                print(f"⚠️ Couldn't fetch price or rating for keyword: {keyword} and link: {link}")
            sleep(2)
    update_products_json(all_new_links)

if __name__ == "__main__":
    main() 