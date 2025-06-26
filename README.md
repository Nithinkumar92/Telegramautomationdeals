# Amazon Price Drop Alert Bot

This script checks prices of products on Amazon and sends a Telegram alert when a price drops below your target.

## ⚙️ Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```
2. Set your secrets in `.env`:
```
TELEGRAM_BOT_TOKEN=your telegram bot token

TELEGRAM_CHAT_ID=@prideautomation
```
3. Add product URLs and target prices in `products.json`.
4. Run the script:
```bash
python price_tracker.py
```

## 🔁 Automate

Use cron (Linux/macOS):

```bash
crontab -e
```
Add a line like:

```
*/30 * * * * /usr/bin/python3 /Users/nithinkumar/Documents/price/price_tracker.py >> /Users/nithinkumar/Documents/price/price_alert.log 2>&1
```
Or use Task Scheduler on Windows.

## 🔐 Notes

- Ensure your Telegram bot is an admin in the channel.
- This script uses HTML scraping. Amazon may change HTML structure—verify periodically.

---

## 🎯 Run

```bash
python price_tracker.py
```

⏱️ Automate (Linux/macOS):
Use `crontab -e` to run every 30 minutes:

```
*/30 * * * * /usr/bin/python3 /Users/nithinkumar/Documents/price/price_tracker.py >> /Users/nithinkumar/Documents/price/price_alert.log 2>&1
```

Let me know if you want a GUI version, email alerts, or to use the Keepa API instead of scraping. 

curl -X POST "https://api.telegram.org/bot7789826926:AAFhwdDpcj_mpBDU11a6UFE6tbRDNXwtF3U/sendMessage" -d "chat_id=@prideautomation" -d "text=Hello from curl"

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{7789826926:AAFhwdDpcj_mpBDU11a6UFE6tbRDNXwtF3U}/sendMessage"
    payload = {
        "chat_id": @prideautomation,
        "text": "Hello from Python (plain text, curl style)"
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


TELEGRAM_BOT_TOKEN = "7789826926:AAFhwdDpcj_mpBDU11a6UFE6tbRDNXwtF3U"
TELEGRAM_CHAT_ID = "@prideautomation" 
print("TELEGRAM_BOT_TOKEN:", os.getenv("TELEGRAM_BOT_TOKEN"))
print("TELEGRAM_CHAT_ID:", TELEGRAM_CHAT_ID)

