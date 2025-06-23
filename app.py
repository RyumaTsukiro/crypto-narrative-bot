import os
import requests
import time
import json

# ==============================================================================
# KONFIGURASI
# ==============================================================================
# Di sini kita akan menyimpan daftar repositori crypto yang ingin kita pantau.
# Anda bisa menambahkan atau mengubah daftar ini kapan saja.
CRYPTO_REPOS = {
    "SOL": "https://github.com/solana-labs/solana",
    "ETH": "https://github.com/ethereum/go-ethereum",
    "ATOM": "https://github.com/cosmos/cosmos-sdk",
    "DOT": "https://github.com/paritytech/polkadot-sdk"
}

# Mengambil token dan kunci API dari Replit Secrets
# BARU: Kita tambahkan GITHUB_PAT
GITHUB_PAT = os.getenv("GITHUB_PAT")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")


# ==============================================================================
# FUNGSI PENGAMBIL DATA
# ==============================================================================

def get_github_weekly_commits(repo_url):
    """
    Fungsi untuk mengambil jumlah commit dalam seminggu terakhir.
    VERSI BARU: Menggunakan Personal Access Token (PAT) untuk otentikasi.
    """
    try:
        parts = repo_url.strip('/').split('/')
        owner = parts[-2]
        repo = parts[-1]
        
        api_url = f"https://api.github.com/repos/{owner}/{repo}/stats/commit_activity"
        
        # BARU: Menambahkan PAT ke header permintaan kita.
        # Ini adalah "Kunci VIP" kita untuk GitHub.
        headers = {
            "Authorization": f"token {GITHUB_PAT}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        print(f"Menghubungi API GitHub untuk repo {owner}/{repo} (dengan otentikasi)...")
        
        # Melakukan permintaan dengan header otentikasi
        response = requests.get(api_url, headers=headers)
        
        # Tunggu jika GitHub sedang memproses
        if response.status_code == 202:
            print("GitHub sedang memproses data, menunggu 3 detik...")
            time.sleep(3)
            response = requests.get(api_url, headers=headers)

        # DEBUG: Cetak status code untuk memastikan semuanya lancar
        print(f"DEBUG: Status Code dari {repo}: {response.status_code}")

        # Pastikan permintaan berhasil (status code 200)
        if response.status_code == 200:
            data = response.json()
            if data and isinstance(data, list) and len(data) > 0:
                # Ambil data minggu terakhir
                last_week_commits = data[-1]['total']
                return last_week_commits
            else:
                return 0 # Repo mungkin baru atau tidak ada data aktivitas
        else:
            # Jika gagal, cetak pesan error dari GitHub
            print(f"Error: Gagal mengambil data untuk {repo}. Pesan: {response.text}")
            return None
            
    except Exception as e:
        print(f"Terjadi error yang tidak terduga: {e}")
        return None


# ==============================================================================
# BLOK UNTUK PENGUJIAN
# ==============================================================================
# Bagian ini akan menguji semua fungsi kita.
if __name__ == "__main__":
    
    print("Memulai Tes Pengambilan Data Narasi...\n")
    
    # Menguji fungsi GitHub commit untuk semua repo di daftar kita
    for ticker, url in CRYPTO_REPOS.items():
        commits = get_github_weekly_commits(url)
        
        if commits is not None:
            print(f"-> Aktivitas Developer [{ticker}]: {commits} commits/minggu")
        else:
            print(f"-> Gagal mengambil data untuk [{ticker}]")
        
        print("-" * 20)
        
    print("\nTes Selesai.")
