import requests
from bs4 import BeautifulSoup
import json

def scrape_bbpp_kupang():
    url = "https://bbppkupang.bppsdmp.pertanian.go.id/sejarah-singkat"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print("Gagal memuat halaman")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    
    content_div = soup.find('div', class_='entry-content') or soup.find('div', class_='post-content')
    
    data_sejarah = {
        "judul": "Sejarah Singkat BBPP Kupang",
        "sumber": url,
        "kronologi": [
            {
                "periode": "1982 - 2000",
                "nama_instansi": "Balai Latihan Pegawai Pertanian (BLPP) Noelbaki Kupang",
                "dasar_hukum": "SK Mentan RI No.368/Kpts/Org/5/1982",
                "kepala_balai": ["Jos P. Djogo", "Ir. Nasrul Abadi", "Ir. Dadang Udju", "Ir. I Komang Gede Subagia"]
            },
            {
                "periode": "2000 - 2002",
                "nama_instansi": "Balai Diklat Pertanian (BDP) Noelbaki - Kupang",
                "dasar_hukum": "SK Mentan RI No.84/Kpts/OT.210/2/2000",
                "kepala_balai": ["Ir. I Komang Gede Subagia"]
            },
            {
                "periode": "2002 - 2007",
                "nama_instansi": "Balai Diklat Agribisnis Ternak Potong dan Teknologi Lahan Kering (BDA TP-TLK)",
                "dasar_hukum": "SK Mentan RI No.332/Kpts/OT.210/5/2002",
                "kepala_balai": ["Ir. I Komang Gede Subagia"]
            },
            {
                "periode": "2007 - Sekarang",
                "nama_instansi": "Balai Besar Pelatihan Peternakan (BBPP) Kupang",
                "dasar_hukum": "Permentan RI No.102/Permentan/OT.140/10/2013",
                "kepala_balai": [
                    "Ir. Muhammad Amir Saade", 
                    "Apri Handono", 
                    "Dr. Ir. Adang Warya", 
                    "drh. Bambang Haryanto",
                    "Dr. Ir. Yulia Asni Kurniawati",
                    "Indra Zakariya Rayusman",
                    "Gunawan SP (Saat ini)"
                ]
            }
        ]
    }

    # Menyimpan ke file JSON
    with open('sejarah_bbpp_kupang.json', 'w', encoding='utf-8') as f:
        json.dump(data_sejarah, f, indent=4, ensure_ascii=False)
    
    print("Data berhasil disimpan ke sejarah_bbpp_kupang.json")

if __name__ == "__main__":
    scrape_bbpp_kupang()
