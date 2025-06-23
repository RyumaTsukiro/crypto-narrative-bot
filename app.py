import os
import requests
import time
import feedparser
from datetime import datetime, timedelta, timezone
import telebot # Library untuk bot Telegram

# ==============================================================================
# KONFIGURASI
# ==============================================================================
# Daftar koin yang didukung oleh bot
CRYPTO_REPOS = {
    "SOL": "https://github.com/solana-labs/solana",
    "ETH": "https://github.com/ethereum/go-ethereum",
    "ATOM": "https://github.com/cosmos/cosmos-sdk",
    "DOT": "https://github.com/paritytech/polkadot-sdk",
    "BTC": "https://github.com/bitcoin/bitcoin" # Menambahkan Bitcoin sebagai contoh
}
COIN_FULL_NAMES = {
    "SOL": "Solana",
    "ETH": "Ethereum",
    "ATOM": "Cosmos",
    "DOT": "Polkadot",
    "BTC": "Bitcoin"
}

# Mengambil kunci API dari Replit Secrets
GITHUB_PAT = os.getenv("GITHUB_PAT")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Bobot untuk formula Hype Index (bisa diubah sesuai selera)
DEV_WEIGHT = 0.6
MEDIA_WEIGHT = 0.4

# Inisialisasi Bot Telegram
bot = telebot.TeleBot(TELEGRAM_TOKEN)
print("Bot Narrative Index siap menerima perintah...")

# ==============================================================================
# FUNGSI PENGAMBIL DATA
# ==============================================================================
def get_github_last_push_days_ago(repo_url):
    try:
        parts = repo_url.strip('/').split('/')
        owner, repo = parts[-2], parts[-1]
        api_url = f"https://api.github.com/repos/{owner}/{repo}"
        headers = {"Authorization": f"token {GITHUB_PAT}", "Accept": "application/vnd.github.v3+json"}
        response = requests.get(api_url, headers=headers)
        response.raise_for_status() # Akan error jika status bukan 2xx
        data = response.json()
        pushed_at_str = data.get("pushed_at")
        if pushed_at_str:
            pushed_at_dt = datetime.strptime(pushed_at_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            days_ago = (datetime.now(timezone.utc) - pushed_at_dt).days
            return days_ago
        return None
    except Exception: return None

def get_news_mentions(coin_name, days=1):
    try:
        query = f'"{coin_name}"+crypto'
        url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
        feed = feedparser.parse(url)
        mention_count = 0
        now_utc = datetime.now(timezone.utc)
        time_threshold = now_utc - timedelta(days=days)
        if not feed.entries: return 0
        for entry in feed.entries:
            published_dt = datetime.fromtimestamp(time.mktime(entry.published_parsed), tz=timezone.utc)
            if published_dt > time_threshold:
                mention_count += 1
        return mention_count
    except Exception: return None

# ==============================================================================
# FUNGSI ANALISIS & SKOR
# ==============================================================================
def calculate_dev_score(days_ago):
    if days_ago is None: return 0
    if days_ago <= 1: return 100
    if days_ago <= 7: return 75
    if days_ago <= 30: return 40
    return 10

def calculate_media_score(mentions):
    if mentions is None: return 0
    if mentions > 20: return 100
    if mentions >= 10: return 80
    if mentions >= 3: return 60
    if mentions >= 1: return 30
    return 0

def calculate_hype_index(dev_score, media_score):
    final_score = (dev_score * DEV_WEIGHT) + (media_score * MEDIA_WEIGHT)
    return final_score

# ==============================================================================
# LOGIKA BOT TELEGRAM
# ==============================================================================

# Menangani perintah /start dan /help
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    supported_tickers = ", ".join(CRYPTO_REPOS.keys())
    bot.reply_to(message, 
        f"Selamat datang di Bot Indeks Narasi Kripto!\n\n"
        f"Gunakan perintah `/narrative [SIMBOL_KOIN]` untuk mendapatkan analisis.\n\n"
        f"Contoh: `/narrative SOL`\n\n"
        f"Koin yang didukung saat ini: {supported_tickers}"
    )

# Menangani perintah utama /narrative
@bot.message_handler(commands=['narrative'])
def get_narrative_index(message):
    try:
        # Mengambil simbol koin dari pesan pengguna
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "Format perintah salah. Contoh: `/narrative SOL`")
            return
            
        ticker = parts[1].upper()
        
        # Memeriksa apakah koin didukung
        if ticker not in CRYPTO_REPOS:
            bot.reply_to(message, f"Maaf, koin dengan simbol '{ticker}' tidak didukung saat ini.")
            return

        bot.reply_to(message, f"🔍 Menganalisis narasi untuk ${ticker}... Mohon tunggu sebentar.")

        # 1. Mengambil dan Menghitung Skor Developer
        repo_url = CRYPTO_REPOS[ticker]
        days = get_github_last_push_days_ago(repo_url)
        dev_score = calculate_dev_score(days)

        # 2. Mengambil dan Menghitung Skor Media
        full_name = COIN_FULL_NAMES[ticker]
        mentions = get_news_mentions(full_name, days=1)
        media_score = calculate_media_score(mentions)

        # 3. Menghitung Hype Index Final
        hype_index = calculate_hype_index(dev_score, media_score)
        
        # 4. Membuat dan Mengirim Laporan Final
        dev_activity_text = f"Push terakhir ~{days} hari lalu" if days is not None else "Data tidak tersedia"
        media_hype_text = f"{mentions} artikel (24 jam)" if mentions is not None else "Data tidak tersedia"

        report = (
            f"📊 **Laporan Analisis Narasi - ${ticker}** 📊\n\n"
            f"👨‍💻 **Aktivitas Developer:**\n"
            f"   - {dev_activity_text}\n"
            f"   - Skor Dev: *{dev_score}/100*\n\n"
            f"📰 **Hype Media:**\n"
            f"   - {media_hype_text}\n"
            f"   - Skor Media: *{media_score}/100*\n\n"
            f"-----------------------------------\n"
            f"🚀 **HYPE INDEX FINAL: {hype_index:.1f} / 100** 🚀"
        )
        
        bot.send_message(message.chat.id, report, parse_mode='Markdown')

    except Exception as e:
        print(f"Error di handler /narrative: {e}")
        bot.reply_to(message, "Maaf, terjadi kesalahan internal saat memproses permintaan Anda.")


# ==============================================================================
# MENJALANKAN BOT
# ==============================================================================
# Membuat bot terus berjalan dan mendengarkan pesan baru
bot.infinity_polling()
