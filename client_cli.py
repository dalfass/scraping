"""
client_cli.py  —  Client WebSocket berbasis Terminal
=====================================================
Menguji server WebSocket tanpa membuka browser.
Sesuai konsep 'Socket Programming' dari Pertemuan 3.

Cara install:
    pip install python-socketio[client] eventlet

Cara menjalankan (pastikan server.py sudah aktif):
    python client_cli.py
"""

import json
import time
import socketio

SERVER_URL = "http://localhost:5000"

sio = socketio.Client()


@sio.event
def connect():
    print("[✓] Terhubung ke server WebSocket!")
    print("[→] Mengirim perintah scrape...")
    sio.emit("start_scrape")


@sio.event
def disconnect():
    print("[✗] Koneksi terputus.")


@sio.on("scrape_log")
def on_log(data):
    level = data.get("level", "info").upper()
    icons = {"INFO": "ℹ", "OK": "✓", "WARN": "⚠", "ERROR": "✗"}
    icon  = icons.get(level, "·")
    print(f"  {icon} [{level}] {data['message']}")


@sio.on("scrape_done")
def on_done(data):
    page = data["page"]
    meta = data["metadata"]

    print("\n" + "="*55)
    print("  SCRAPING SELESAI")
    print("="*55)
    print(f"  Judul      : {page['title'] or '(kosong)'}")
    print(f"  Paragraf   : {page['total_paragraphs']}")
    print(f"  Gambar     : {len(page['images'])}")
    print(f"  HTTP Status: {meta['http_status']}")
    print(f"  Waktu      : {meta['scraped_at']}")
    print("="*55)

    if page["paragraphs"]:
        print("\n[Cuplikan Paragraf Pertama]")
        print(page["paragraphs"][0][:300] + "...")

    print("\n[✓] Data lengkap tersedia di: data_bbppkupang.json")
    print("[→] Menutup koneksi...\n")

    sio.disconnect()


@sio.on("scrape_error")
def on_error(data):
    print(f"\n[✗] ERROR: {data['message']}")
    sio.disconnect()


if __name__ == "__main__":
    print(f"[→] Menghubungkan ke {SERVER_URL} ...")
    try:
        sio.connect(SERVER_URL)
        sio.wait()
    except ConnectionRefusedError:
        print("[✗] Tidak bisa terhubung. Pastikan server.py sudah berjalan!")