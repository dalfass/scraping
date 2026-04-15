"""
server.py  —  Web Scraping + WebSocket (Flask-SocketIO)
========================================================
Arsitektur (sesuai Pertemuan 3):
  Socket Layer  : Flask-SocketIO menangani koneksi WebSocket
  Framework     : Flask sebagai HTTP server + routing
  Scraping      : requests + BeautifulSoup mengambil data BBPP Kupang
  Output        : JSON disimpan ke disk & di-broadcast ke semua client

Cara install:
    pip install flask flask-socketio requests beautifulsoup4 eventlet

Cara menjalankan:
    python server.py

Buka browser: http://localhost:5000
"""

import json
import threading
from datetime import datetime
from pathlib import Path

import eventlet
eventlet.monkey_patch()                          # wajib untuk async SocketIO

import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template_string
from flask_socketio import SocketIO, emit

# ── Konfigurasi ────────────────────────────────────────────────────────────────
TARGET_URL   = "https://bbppkupang.bppsdmp.pertanian.go.id/sejarah-singkat"
OUTPUT_FILE  = "data_bbppkupang.json"
HOST         = "0.0.0.0"
PORT         = 5000

app    = Flask(__name__)
app.config["SECRET_KEY"] = "bbpp-scraper-secret"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

# ── Template HTML Client (satu file, tidak perlu folder templates) ─────────────
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>BBPP Kupang — Real-time Scraper</title>
  <script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Segoe UI', sans-serif;
      background: #f0f2f5;
      color: #333;
      padding: 24px;
    }
    h1 { font-size: 1.6rem; margin-bottom: 4px; color: #1a3c5e; }
    .subtitle { font-size: 0.9rem; color: #666; margin-bottom: 24px; }
    .card {
      background: white;
      border-radius: 10px;
      padding: 20px 24px;
      margin-bottom: 16px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.07);
    }
    .status-bar {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 16px;
    }
    #dot {
      width: 12px; height: 12px;
      border-radius: 50%;
      background: #ccc;
      transition: background 0.3s;
    }
    #dot.connected  { background: #22c55e; }
    #dot.scraping   { background: #f59e0b; animation: pulse 1s infinite; }
    #dot.done       { background: #3b82f6; }
    #dot.error      { background: #ef4444; }
    @keyframes pulse {
      0%,100% { opacity:1; } 50% { opacity:0.3; }
    }
    #status-text { font-weight: 600; font-size: 0.95rem; }
    button {
      padding: 10px 22px;
      background: #1a3c5e;
      color: white;
      border: none;
      border-radius: 8px;
      font-size: 0.95rem;
      cursor: pointer;
      transition: background 0.2s;
    }
    button:hover  { background: #274f7a; }
    button:disabled { background: #94a3b8; cursor: not-allowed; }

    #log-box {
      background: #0f172a;
      color: #94d8ac;
      font-family: 'Courier New', monospace;
      font-size: 0.82rem;
      padding: 14px;
      border-radius: 8px;
      height: 180px;
      overflow-y: auto;
      margin-top: 12px;
    }
    #log-box p { margin: 2px 0; }
    .ts { color: #64748b; }

    #result { display: none; }
    #result h2 { font-size: 1.1rem; margin-bottom: 8px; color: #1a3c5e; }
    .meta-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
      gap: 10px;
      margin-bottom: 16px;
    }
    .meta-item { background: #f8fafc; border-radius: 8px; padding: 10px 14px; }
    .meta-item .label { font-size: 0.75rem; color: #64748b; text-transform: uppercase; }
    .meta-item .value { font-size: 1rem; font-weight: 600; margin-top: 2px; }
    #paragraphs { max-height: 300px; overflow-y: auto; }
    #paragraphs p {
      padding: 8px 0;
      border-bottom: 1px solid #f1f5f9;
      line-height: 1.6;
      font-size: 0.92rem;
    }
    #json-raw {
      background: #0f172a;
      color: #7dd3fc;
      font-family: monospace;
      font-size: 0.78rem;
      padding: 14px;
      border-radius: 8px;
      max-height: 280px;
      overflow: auto;
      white-space: pre;
      display: none;
      margin-top: 12px;
    }
    .toggle-json {
      font-size: 0.82rem;
      background: none;
      color: #3b82f6;
      border: 1px solid #3b82f6;
      padding: 4px 10px;
      margin-top: 8px;
    }
  </style>
</head>
<body>
  <h1>🔌 Real-time Web Scraper</h1>
  <p class="subtitle">Socket Programming + Flask + BeautifulSoup — Pertemuan 3</p>

  <!-- Control Panel -->
  <div class="card">
    <div class="status-bar">
      <div id="dot"></div>
      <span id="status-text">Menghubungkan ke server...</span>
    </div>
    <button id="btn-scrape" disabled onclick="startScrape()">▶ Mulai Scraping</button>

    <div id="log-box"></div>
  </div>

  <!-- Result Panel -->
  <div class="card" id="result">
    <h2>📄 Hasil Scraping</h2>
    <div class="meta-grid">
      <div class="meta-item">
        <div class="label">Judul</div>
        <div class="value" id="r-title">—</div>
      </div>
      <div class="meta-item">
        <div class="label">Paragraf</div>
        <div class="value" id="r-para">—</div>
      </div>
      <div class="meta-item">
        <div class="label">Gambar</div>
        <div class="value" id="r-img">—</div>
      </div>
      <div class="meta-item">
        <div class="label">HTTP Status</div>
        <div class="value" id="r-status">—</div>
      </div>
      <div class="meta-item">
        <div class="label">Waktu Scraping</div>
        <div class="value" id="r-time">—</div>
      </div>
    </div>

    <h2>📝 Isi Konten</h2>
    <div id="paragraphs"></div>

    <button class="toggle-json" onclick="toggleJson()">{ } Lihat JSON Mentah</button>
    <div id="json-raw"></div>
  </div>

  <script>
    const socket = io();
    const log    = document.getElementById('log-box');
    const dot    = document.getElementById('dot');
    const stText = document.getElementById('status-text');
    const btn    = document.getElementById('btn-scrape');

    function addLog(msg, type='info') {
      const colors = { info:'#94d8ac', warn:'#fbbf24', error:'#f87171', ok:'#67e8f9' };
      const ts = new Date().toLocaleTimeString('id-ID');
      log.innerHTML += `<p><span class="ts">[${ts}]</span> <span style="color:${colors[type]||colors.info}">${msg}</span></p>`;
      log.scrollTop = log.scrollHeight;
    }

    function setState(state, text) {
      dot.className = state;
      stText.textContent = text;
    }

    socket.on('connect', () => {
      setState('connected', 'Terhubung ke server WebSocket ✓');
      btn.disabled = false;
      addLog('Koneksi WebSocket berhasil.', 'ok');
    });

    socket.on('disconnect', () => {
      setState('', 'Koneksi terputus');
      btn.disabled = true;
      addLog('WebSocket terputus.', 'error');
    });

    socket.on('scrape_log', data => {
      addLog(data.message, data.level || 'info');
    });

    socket.on('scrape_done', data => {
      setState('done', 'Scraping selesai ✓');
      btn.disabled = false;
      addLog('Data diterima dari server!', 'ok');
      renderResult(data);
    });

    socket.on('scrape_error', data => {
      setState('error', 'Scraping gagal ✗');
      btn.disabled = false;
      addLog('ERROR: ' + data.message, 'error');
    });

    function startScrape() {
      btn.disabled = true;
      document.getElementById('result').style.display = 'none';
      setState('scraping', 'Sedang scraping...');
      addLog('Mengirim perintah scrape ke server...', 'info');
      socket.emit('start_scrape');
    }

    function renderResult(data) {
      const page = data.page;
      const meta = data.metadata;

      document.getElementById('r-title').textContent  = page.title || '(tidak ada judul)';
      document.getElementById('r-para').textContent   = page.total_paragraphs;
      document.getElementById('r-img').textContent    = page.images.length;
      document.getElementById('r-status').textContent = meta.http_status;
      document.getElementById('r-time').textContent   = new Date(meta.scraped_at).toLocaleString('id-ID');

      const paraDiv = document.getElementById('paragraphs');
      paraDiv.innerHTML = '';
      page.paragraphs.forEach(p => {
        const el = document.createElement('p');
        el.textContent = p;
        paraDiv.appendChild(el);
      });

      document.getElementById('json-raw').textContent = JSON.stringify(data, null, 2);
      document.getElementById('result').style.display = 'block';
    }

    function toggleJson() {
      const el = document.getElementById('json-raw');
      el.style.display = el.style.display === 'none' ? 'block' : 'none';
    }
  </script>
</body>
</html>
"""

# ── Fungsi Scraping ─────────────────────────────────────────────────────────────
def scrape_website(url: str, log_fn) -> dict:
    """Scrape URL dan kirim log real-time via callback log_fn."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "id-ID,id;q=0.9",
    }

    log_fn(f"Mengakses: {url}", "info")
    response = requests.get(url, headers=headers, timeout=15)
    log_fn(f"HTTP Status: {response.status_code}", "ok")
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    log_fn("HTML berhasil di-parse oleh BeautifulSoup.", "info")

    # Judul
    title = ""
    for tag in ["h1", "h2", "h3"]:
        el = soup.find(tag)
        if el:
            title = el.get_text(strip=True)
            break

    # Konten utama
    content_selectors = [
        {"class": "item-page"},
        {"class": "article-content"},
        {"class": "entry-content"},
        {"id": "content"},
        {"class": "content"},
    ]
    content_div = None
    for sel in content_selectors:
        content_div = soup.find("div", sel)
        if content_div:
            log_fn(f"Konten ditemukan: selektor {sel}", "info")
            break

    if not content_div:
        content_div = soup.find("main") or soup.find("article")
        log_fn("Menggunakan fallback selektor <main>/<article>.", "warn")

    # Paragraf
    paragraphs = []
    source = content_div if content_div else soup
    for p in source.find_all("p"):
        text = p.get_text(separator=" ", strip=True)
        if text:
            paragraphs.append(text)

    log_fn(f"Ditemukan {len(paragraphs)} paragraf.", "ok")

    # Gambar
    images = []
    if content_div:
        for img in content_div.find_all("img"):
            src = img.get("src", "")
            alt = img.get("alt", "")
            if src:
                if src.startswith("/"):
                    base = "/".join(url.split("/")[:3])
                    src = base + src
                images.append({"src": src, "alt": alt})

    # Meta
    meta_desc = ""
    meta_tag = soup.find("meta", attrs={"name": "description"})
    if meta_tag:
        meta_desc = meta_tag.get("content", "")

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
            "full_text": "\n\n".join(paragraphs),
            "total_paragraphs": len(paragraphs),
            "images": images,
        },
    }

    return data


# ── Flask Routes ────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/data")
def get_data():
    """Endpoint REST: ambil data JSON terakhir yang di-scrape."""
    path = Path(OUTPUT_FILE)
    if not path.exists():
        return {"error": "Belum ada data. Jalankan scraping terlebih dahulu."}, 404
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ── WebSocket Events ────────────────────────────────────────────────────────────
@socketio.on("connect")
def on_connect():
    print(f"[WS] Client terhubung: {threading.current_thread().name}")
    emit("scrape_log", {"message": "Selamat datang! Server siap.", "level": "ok"})


@socketio.on("disconnect")
def on_disconnect():
    print("[WS] Client terputus.")


@socketio.on("start_scrape")
def handle_scrape():
    """Client meminta scraping; jalankan di thread terpisah agar non-blocking."""
    print("[WS] Perintah scrape diterima.")

    def run():
        def log_fn(msg, level="info"):
            socketio.emit("scrape_log", {"message": msg, "level": level})
            print(f"  [{level.upper()}] {msg}")

        try:
            data = scrape_website(TARGET_URL, log_fn)

            # Simpan ke JSON
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            log_fn(f"Data disimpan ke '{OUTPUT_FILE}'.", "ok")

            # Broadcast hasil ke semua client
            socketio.emit("scrape_done", data)

        except requests.exceptions.ConnectionError:
            socketio.emit("scrape_error", {"message": "Tidak bisa terhubung ke server target."})
        except requests.exceptions.Timeout:
            socketio.emit("scrape_error", {"message": "Koneksi timeout."})
        except Exception as e:
            socketio.emit("scrape_error", {"message": str(e)})

    thread = threading.Thread(target=run, daemon=True)
    thread.start()


# ── Entry Point ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"[SERVER] Berjalan di http://{HOST}:{PORT}")
    print(f"[SERVER] Target URL: {TARGET_URL}")
    print(f"[SERVER] Output    : {OUTPUT_FILE}")
    socketio.run(app, host=HOST, port=PORT, debug=True)