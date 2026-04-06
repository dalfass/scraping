import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime


def scrape_sejarah_singkat(url: str) -> dict:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    print(f"[INFO] Mengakses URL: {url}")
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    print(f"[INFO] Status HTTP: {response.status_code}")

    soup = BeautifulSoup(response.text, "html.parser")

    # ── Judul halaman ──────────────────────────────────────────────
    title = ""
    title_tag = (
        soup.find("h1")
        or soup.find("h2")
        or soup.find(class_=lambda c: c and "title" in c.lower())
    )
    if title_tag:
        title = title_tag.get_text(strip=True)

    # ── Konten utama ───────────────────────────────────────────────
    # Coba beberapa selektor umum CMS (Joomla / WordPress / custom)
    content_selectors = [
        {"class": "item-page"},        # Joomla default
        {"class": "article-content"},
        {"class": "entry-content"},
        {"id": "content"},
        {"class": "content"},
        {"class": "post-content"},
    ]

    content_div = None
    for sel in content_selectors:
        content_div = soup.find("div", sel)
        if content_div:
            print(f"[INFO] Konten ditemukan dengan selektor: {sel}")
            break

    # Fallback: ambil <main> atau <article>
    if not content_div:
        content_div = soup.find("main") or soup.find("article")

    # ── Paragraf teks ──────────────────────────────────────────────
    paragraphs = []
    if content_div:
        for p in content_div.find_all("p"):
            text = p.get_text(separator=" ", strip=True)
            if text:
                paragraphs.append(text)
    else:
        # Ambil semua <p> di halaman sebagai fallback terakhir
        print("[WARN] Konten utama tidak ditemukan, mengambil semua <p>")
        for p in soup.find_all("p"):
            text = p.get_text(separator=" ", strip=True)
            if text and len(text) > 30:   # abaikan teks sangat pendek
                paragraphs.append(text)

    full_text = "\n\n".join(paragraphs)

    # ── Gambar ────────────────────────────────────────────────────
    images = []
    if content_div:
        for img in content_div.find_all("img"):
            src = img.get("src", "")
            alt = img.get("alt", "")
            if src:
                # Lengkapi URL relatif
                if src.startswith("/"):
                    base = "/".join(url.split("/")[:3])
                    src = base + src
                images.append({"src": src, "alt": alt})

    # ── Meta SEO ──────────────────────────────────────────────────
    meta_desc = ""
    meta_tag = soup.find("meta", attrs={"name": "description"})
    if meta_tag:
        meta_desc = meta_tag.get("content", "")

    # ── Rakitan data ──────────────────────────────────────────────
    data = {
        "metadata": {
            "url": url,
            "scraped_at": datetime.now().isoformat(),
            "http_status": response.status_code,
            "encoding": response.encoding,
        },
        "page": {
            "title": title,
            "meta_description": meta_desc,
            "paragraphs": paragraphs,
            "full_text": full_text,
            "total_paragraphs": len(paragraphs),
            "images": images,
        },
    }

    return data


def main():
    url = "https://bbppkupang.bppsdmp.pertanian.go.id/sejarah-singkat"
    output_file = "data_bbppkupang.json"

    try:
        data = scrape_sejarah_singkat(url)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"\n[OK] Data berhasil disimpan ke: {output_file}")
        print(f"     Judul    : {data['page']['title']}")
        print(f"     Paragraf : {data['page']['total_paragraphs']}")
        print(f"     Gambar   : {len(data['page']['images'])}")

    except requests.exceptions.ConnectionError:
        print("[ERROR] Tidak dapat terhubung ke server. Periksa koneksi internet.")
    except requests.exceptions.Timeout:
        print("[ERROR] Koneksi timeout. Coba lagi nanti.")
    except requests.exceptions.HTTPError as e:
        print(f"[ERROR] HTTP Error: {e}")
    except Exception as e:
        print(f"[ERROR] Terjadi kesalahan: {e}")
        raise


if __name__ == "__main__":
    main()