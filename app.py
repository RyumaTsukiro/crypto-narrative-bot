import os
import requests
import time

# Kita siapkan dulu variabel untuk token Telegram, akan dipakai nanti.
# Untuk sekarang, kita tidak perlu mengisinya di Replit Secrets.
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

def get_github_weekly_commits(repo_url):
    """
    Fungsi untuk mengambil jumlah commit dalam seminggu terakhir
    dari sebuah repositori GitHub.
    """
    try:
        # Memecah URL untuk mendapatkan 'owner' dan 'repo'
        # Contoh: https://github.com/solana-labs/solana -> owner=solana-labs, repo=solana
        parts = repo_url.strip('/').split('/')
        owner = parts[-2]
        repo = parts[-1]

        # Menyiapkan URL API GitHub
        api_url = f"https://api.github.com/repos/{owner}/{repo}/stats/commit_activity"
        
        print(f"Menghubungi API GitHub untuk repo {owner}/{repo}...")
        
        # Melakukan permintaan ke API GitHub
        response = requests.get(api_url)
        
        # Menunggu beberapa detik jika API meminta kita untuk menunggu
        if response.status_code == 202:
            print("GitHub sedang memproses data, menunggu 3 detik...")
            time.sleep(3)
            response = requests.get(api_url)

        # Memastikan permintaan berhasil
        response.raise_for_status()
        
        data = response.json()
        
        # Data yang dikembalikan adalah list 52 minggu, kita ambil yang terakhir [-1]
        if data:
            last_week_commits = data[-1]['total']
            return last_week_commits
        else:
            return 0
            
    except requests.exceptions.RequestException as e:
        print(f"Error saat menghubungi API GitHub: {e}")
        return None
    except (KeyError, IndexError):
        print("Format data dari GitHub tidak sesuai atau repo baru.")
        return 0
    except Exception as e:
        print(f"Terjadi error yang tidak terduga: {e}")
        return None


# --- BLOK UNTUK PENGUJIAN ---
# Kode di bawah ini hanya akan berjalan jika kita menjalankan file ini secara langsung
# Ini cara kita menguji fungsi di atas tanpa perlu bot Telegram
if __name__ == "__main__":
    # Ganti dengan URL repo lain jika ingin menguji
    # Pastikan repo tersebut sudah cukup lama ada
    test_repo_url = "https://github.com/solana-labs/solana"
    
    commits = get_github_weekly_commits(test_repo_url)
    
    if commits is not None:
        print("-" * 30)
        print(f"HASIL TES:")
        print(f"Aktivitas commit mingguan di repo {test_repo_url.split('/')[-1]}: {commits} commits")
        print("-" * 30)
    else:
        print("Gagal mengambil data commit.")
