import os
import requests
import time
import json
import feedparser
from datetime import datetime, timedelta

# ==============================================================================
# KONFIGURASI
# ==============================================================================

# Daftar repositori crypto yang ingin kita pantau.
CRYPTO_REPOS = {
    "SOL": "https://github.com/solana-labs/solana",
    "ETH": "https://github.com/ethereum/go-ethereum",
    "ATOM": "https://github.com/cosmos/cosmos-sdk",
    "DOT": "https://github.com/paritytech/polkadot-sdk"
}

# Daftar nama lengkap koin untuk pencarian berita
COIN_FULL_NAMES = {
    "SOL": "Solana",
    "ETH": "Ethereum",
    "ATOM": "Cosmos",
    "DOT": "Polkadot"
}

# Mengambil token dan kunci API dari Replit Secrets
GITHUB_PAT = os.getenv("GITHUB_PAT")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")


# ==============================================================================
# FUNGSI PENGAMBIL DATA
# ==============================================================================

def get_github_weekly_commits(repo_url):
    """
    Fungsi untuk mengambil jumlah commit dalam seminggu terakhir.
    Menggunakan Personal Access Token (PAT) untuk otentikasi.
    """
    try:
        parts = repo_url.strip('/').split('/')
        owner = parts[-2]
        repo = parts[-1]
        api_url = f"https://api.github.com/repos/{owner}/{repo}/stats/commit_activity"
        headers = {"Authorization": f"token {GITHUB_PAT}", "Accept": "application/vnd.github.v3+json"}
        
        print(f"Mengambil data GitHub untuk [{repo}]...")
        response = requests.get(api_url, headers=headers)
        
        if response.status_code == 202:
            time.sleep(3)
            response = requests.get(api_url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            if data and isinstance(data, list) and len(data) > 0:
                last_week_commits = data[-1]['total']
                return last_week_commits
            else:
                return 0
        else:
            print(f"  -> Gagal (GitHub Status: {response.status_code})")
            return None
            
    except Exception as e:
        print(f"  -> Terjadi error di fungsi GitHub: {e}")
        return None

def get_news_mentions(coin_name, days=1):
    """
    Fungsi untuk menghitung berapa kali sebuah koin disebut di Google News
    dalam beberapa hari terakhir.
    """
    try:
        query = f'"{coin_name}"+crypto' # Pakai tanda kutip untuk pencarian lebih akurat
        url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
        
        print(f"Mengambil berita untuk [{coin_name}]...")
        feed = feedparser.parse(url)
        
        mention_count = 0
        # Dapatkan waktu saat ini dalam zona waktu UTC untuk perbandingan yang konsisten
        now_utc = datetime.utcnow().replace(tzinfo=None)
        time_threshold = now_utc - timedelta(days=days)
        
        if not feed.entries:
             print(f"  -> Tidak ada berita ditemukan untuk [{coin_name}].")
             return 0

        for entry in feed.entries:
            # Struct 'published_parsed' dari feedparser sudah dalam format UTC
            published_time = datetime.fromtimestamp(time.mktime(entry.published_parsed))
            if published_time > time_threshold:
                mention_count += 1
                
        return mention_count
        
    except Exception as e:
        print(f"  -> Terjadi error di fungsi Berita: {e}")
        return None


# ==============================================================================
# BLOK UNTUK PENGUJIAN
# ==============================================================================
if __name__ == "__main__":
    
    print("Memulai Tes Pengambilan Data Narasi v0.2...\n")

    # Menguji kedua fungsi untuk semua repo di daftar kita
    for ticker, repo_url in CRYPTO_REPOS.items():
        print(f"===== Analisis untuk Ticker: {ticker} =====")
        
        # 1. Ambil data commit GitHub
        commits = get_github_weekly_commits(repo_url)
        if commits is not None:
            print(f"  -> Aktivitas Developer: {commits} commits/minggu")
        else:
            print(f"  -> Gagal mengambil data commit.")
        
        # 2. Ambil data berita
        full_name = COIN_FULL_NAMES[ticker]
        mentions = get_news_mentions(full_name, days=1) # Mencari berita 1 hari terakhir
        if mentions is not None:
            print(f"  -> Hype Media: {mentions} artikel berita (24 jam terakhir)")
        else:
            print(f"  -> Gagal mengambil data berita.")
        
        print("-" * 25 + "\n")
        
    print("Tes Selesai.")

