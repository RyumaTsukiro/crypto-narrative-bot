import os
import requests
import time
import json
import feedparser
from datetime import datetime, timedelta, timezone

# ==============================================================================
# KONFIGURASI
# ==============================================================================
CRYPTO_REPOS = {
    "SOL": "https://github.com/solana-labs/solana",
    "ETH": "https://github.com/ethereum/go-ethereum",
    "ATOM": "https://github.com/cosmos/cosmos-sdk",
    "DOT": "https://github.com/paritytech/polkadot-sdk"
}
COIN_FULL_NAMES = {
    "SOL": "Solana",
    "ETH": "Ethereum",
    "ATOM": "Cosmos",
    "DOT": "Polkadot"
}
GITHUB_PAT = os.getenv("GITHUB_PAT")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# ==============================================================================
# FUNGSI PENGAMBIL DATA
# ==============================================================================

def get_github_last_push_days_ago(repo_url):
    """
    FUNGSI BARU: Mengambil kapan terakhir kali ada 'push' ke repo
    dan mengembalikannya dalam format jumlah hari yang lalu.
    Metrik ini jauh lebih stabil daripada commit activity.
    """
    try:
        parts = repo_url.strip('/').split('/')
        owner = parts[-2]
        repo = parts[-1]
        # Menggunakan endpoint utama repo, yang selalu ada datanya
        api_url = f"https://api.github.com/repos/{owner}/{repo}"
        headers = {"Authorization": f"token {GITHUB_PAT}", "Accept": "application/vnd.github.v3+json"}
        
        print(f"Mengambil data GitHub untuk [{repo}]...")
        response = requests.get(api_url, headers=headers)
        response.raise_for_status() # Akan error jika status bukan 2xx

        data = response.json()
        pushed_at_str = data.get("pushed_at")

        if pushed_at_str:
            # Mengubah string timestamp menjadi objek datetime
            pushed_at_dt = datetime.strptime(pushed_at_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            now_utc = datetime.now(timezone.utc)
            days_ago = (now_utc - pushed_at_dt).days
            return days_ago
        else:
            return None # Jika tidak ada data 'pushed_at'
            
    except Exception as e:
        print(f"  -> Terjadi error di fungsi GitHub: {e}")
        return None

def get_news_mentions(coin_name, days=1):
    """
    Fungsi untuk menghitung berapa kali sebuah koin disebut di Google News
    dalam beberapa hari terakhir.
    """
    try:
        query = f'"{coin_name}"+crypto'
        url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
        
        print(f"Mengambil berita untuk [{coin_name}]...")
        feed = feedparser.parse(url)
        
        mention_count = 0
        now_utc = datetime.now(timezone.utc)
        time_threshold = now_utc - timedelta(days=days)
        
        if not feed.entries:
             return 0

        for entry in feed.entries:
            published_dt = datetime.fromtimestamp(time.mktime(entry.published_parsed), tz=timezone.utc)
            if published_dt > time_threshold:
                mention_count += 1
                
        return mention_count
        
    except Exception as e:
        print(f"  -> Terjadi error di fungsi Berita: {e}")
        return None

# ==============================================================================
# BLOK UNTUK PENGUJIAN
# ==============================================================================
if __name__ == "__main__":
    
    print("Memulai Tes Pengambilan Data Narasi v0.3...\n")

    for ticker, repo_url in CRYPTO_REPOS.items():
        print(f"===== Analisis untuk Ticker: {ticker} =====")
        
        # 1. Menggunakan fungsi GitHub yang baru
        days_ago = get_github_last_push_days_ago(repo_url)
        if days_ago is not None:
            print(f"  -> Aktivitas Developer: Push terakhir ~{days_ago} hari yang lalu")
        else:
            print(f"  -> Gagal mengambil data commit.")
        
        # 2. Ambil data berita
        full_name = COIN_FULL_NAMES[ticker]
        mentions = get_news_mentions(full_name, days=1)
        if mentions is not None:
            print(f"  -> Hype Media: {mentions} artikel berita (24 jam terakhir)")
        else:
            print(f"  -> Gagal mengambil data berita.")
        
        print("-" * 25 + "\n")
        
    print("Tes Selesai.")

