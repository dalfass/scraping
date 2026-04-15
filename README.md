# 🔌 Web Scraping + WebSocket — BBPP Kupang
### Pertemuan 3: Socket Programming + Flask Framework

---

## Arsitektur Sistem

```
┌─────────────────────────────────────────────────────────┐
│                     server.py                           │
│                                                         │
│  ┌──────────┐   ┌─────────────┐   ┌────────────────┐   │
│  │  Flask   │   │ Flask-      │   │  Scraper       │   │
│  │  HTTP    │   │ SocketIO    │   │  (requests +   │   │
│  │  /       │   │ WebSocket   │   │  BeautifulSoup)│   │
│  └──────────┘   └─────────────┘   └────────────────┘   │
│       │               │                   │             │
│       └───────────────┴───────────────────┘             │
│                       │                                 │
│               data_bbppkupang.json                      │
└───────────────────────┬─────────────────────────────────┘
                        │  WebSocket (ws://)
          ┌─────────────┴──────────────┐
          │                            │
   ┌──────▼──────┐             ┌───────▼──────┐
   │  Browser    │             │  client_cli  │
   │  (HTML/JS)  │             │  (Terminal)  │
   └─────────────┘             └──────────────┘
```

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
Buka `http://localhost:5000`, klik **▶ Mulai Scraping**.  
Log real-time akan muncul, hasil ditampilkan otomatis.

### 3B. Gunakan via Terminal
```bash
python client_cli.py
```

### 4. Ambil Data via REST API (opsional)
```bash
curl http://localhost:5000/data
```

---

## Kaitan dengan Materi Pertemuan 3

| Konsep Slide        | Implementasi dalam Kode                          |
|---------------------|--------------------------------------------------|
| Socket (bind/listen/accept) | Flask-SocketIO menangani semua ini otomatis |
| HTTP Request/Response | `requests.get()` untuk scraping target      |
| Framework Flask     | `@app.route("/")` routing halaman utama          |
| Manual → Framework  | Socket murni diganti Flask-SocketIO              |
| Client-Server       | Browser/CLI ↔ server via WebSocket               |

---

## Event WebSocket

| Event             | Arah            | Keterangan                        |
|-------------------|-----------------|-----------------------------------|
| `connect`         | Server → Client | Konfirmasi koneksi berhasil       |
| `start_scrape`    | Client → Server | Perintah mulai scraping           |
| `scrape_log`      | Server → Client | Log real-time progres scraping    |
| `scrape_done`     | Server → Client | Hasil scraping lengkap (JSON)     |
| `scrape_error`    | Server → Client | Notifikasi jika terjadi error     |
