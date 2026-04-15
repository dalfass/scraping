NAMA: DIQI ALFAS SALAM

NIM: 241080200114

## Alur Komunikasi WebSocket

```
Client ──── connect ────────────────────► Server
Client ◄─── scrape_log (siap) ──────────  Server
Client ──── start_scrape ───────────────► Server
            Server mulai scraping...
Client ◄─── scrape_log (progres) ───────  Server  (real-time)
Client ◄─── scrape_log (progres) ───────  Server  (real-time)
Client ◄─── scrape_done (data JSON) ────  Server
```

## Struktur File

```
project/
├── server.py             ← Server utama (Flask + WebSocket + Scraper)
├── client_cli.py         ← Client terminal untuk testing
├── data_bbppkupang.json  ← Output hasil scraping (auto-generated)
└── README.md
```

## Cara Menjalankan

### 1. Install Dependensi
```bash
pip install flask flask-socketio requests beautifulsoup4 eventlet
pip install python-socketio[client]   # untuk client_cli.py
```

### 2. Jalankan Server
```bash
python server.py
```
Output:
```
[SERVER] Berjalan di http://0.0.0.0:5000
[SERVER] Target URL: https://bbppkupang.bppsdmp.pertanian.go.id/sejarah-singkat
[SERVER] Output    : data_bbppkupang.json
```

### 3A. Gunakan via Browser
Buka `http://localhost:5000`, klik -> Mulai Scraping.  
Log real-time akan muncul, hasil ditampilkan otomatis.

### 3B. Gunakan via Terminal
```bash
python client_cli.py
```

### 4. Ambil Data via REST API (opsional)
```bash
curl http://localhost:5000/data
```

