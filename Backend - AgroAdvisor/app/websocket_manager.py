"""
WebSocket Connection Manager

Mengelola semua koneksi WebSocket aktif dari client (browser/dashboard).
Saat ada data baru (sensor, pompa, rekomendasi) → broadcast ke semua client.

Arsitektur:
- Satu manager global (_manager) yang hidup selama server berjalan
- Setiap browser yang buka dashboard → satu koneksi WebSocket
- Semua koneksi disimpan dalam set, jika client tutup browser → otomatis dihapus
- Event system: backend tinggal panggil broadcast_event(tipe, data) dari mana saja
"""

import json
import asyncio
from datetime import datetime
from typing import Set
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self):
        # Set semua koneksi aktif
        self.active_connections: Set[WebSocket] = set()

    # ── Koneksi ───────────────────────────────────────────────────────────────

    async def connect(self, websocket: WebSocket):
        """Terima koneksi baru dari client."""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"Client terhubung. Total: {len(self.active_connections)}")

        # Kirim pesan selamat datang
        await self._send_to(websocket, {
            "tipe":    "connected",
            "pesan":   "Terhubung ke AgriSmart AI real-time feed",
            "timestamp": datetime.now().isoformat(),
        })

    def disconnect(self, websocket: WebSocket):
        """Hapus koneksi saat client disconnect."""
        self.active_connections.discard(websocket)
        logger.info(f"Client disconnect. Sisa: {len(self.active_connections)}")

    # ── Kirim ke Satu Client ──────────────────────────────────────────────────

    async def _send_to(self, websocket: WebSocket, data: dict):
        """Kirim data ke satu client. Hapus jika koneksi sudah mati."""
        try:
            await websocket.send_text(json.dumps(data, ensure_ascii=False, default=str))
        except Exception:
            self.active_connections.discard(websocket)

    # ── Broadcast ke Semua Client ─────────────────────────────────────────────

    async def broadcast(self, data: dict):
        """Kirim data ke semua client yang terhubung."""
        if not self.active_connections:
            return

        mati = set()
        pesan = json.dumps(data, ensure_ascii=False, default=str)

        for ws in self.active_connections.copy():
            try:
                await ws.send_text(pesan)
            except Exception:
                mati.add(ws)

        # Bersihkan koneksi yang sudah mati
        self.active_connections -= mati

    async def broadcast_event(self, tipe: str, data: dict):
        """
        Wrapper broadcast dengan format event standar.

        Tipe event yang digunakan sistem:
        - sensor_update     → data sensor IoT terbaru
        - pompa_update      → perubahan status pompa
        - rekomendasi_pupuk → rekomendasi pupuk baru dari AI
        - rekomendasi_pestisida → rekomendasi pestisida baru
        - saran_tanaman     → AI selesai analisis tanaman cocok
        - alert             → peringatan kondisi kritis
        - reset_sesi        → sesi baru dimulai
        """
        await self.broadcast({
            "tipe":      tipe,
            "data":      data,
            "timestamp": datetime.now().isoformat(),
        })

    # ── Broadcast Helper per Modul ────────────────────────────────────────────

    async def kirim_update_sensor(self, sensor_data: dict, status_tanah: dict):
        await self.broadcast_event("sensor_update", {
            **sensor_data,
            **status_tanah,
        })

    async def kirim_update_pompa(self, status: str, alasan: str, data_sensor: dict = None):
        await self.broadcast_event("pompa_update", {
            "status":        status,
            "alasan":        alasan,
            "data_sensor":   data_sensor or {},
        })

    async def kirim_rekomendasi_pupuk(self, jenis_tanaman: str, ringkasan: str, estimasi: str):
        await self.broadcast_event("rekomendasi_pupuk", {
            "jenis_tanaman": jenis_tanaman,
            "ringkasan":     ringkasan,
            "estimasi":      estimasi,
            "pesan":         f"Rekomendasi pupuk baru untuk {jenis_tanaman} tersedia",
        })

    async def kirim_rekomendasi_pestisida(self, jenis_tanaman: str, jenis_hama: str, tingkat: str):
        await self.broadcast_event("rekomendasi_pestisida", {
            "jenis_tanaman": jenis_tanaman,
            "jenis_hama":    jenis_hama,
            "tingkat_serangan": tingkat,
            "pesan":         f"Rekomendasi pestisida untuk {jenis_hama} pada {jenis_tanaman} tersedia",
        })

    async def kirim_alert(self, level: str, pesan: str, data: dict = None):
        """
        Kirim alert ke semua client.
        level: info | warning | critical
        """
        await self.broadcast_event("alert", {
            "level": level,
            "pesan": pesan,
            "data":  data or {},
        })

    @property
    def jumlah_client(self) -> int:
        return len(self.active_connections)


# Instance global — dipakai di seluruh aplikasi
manager = WebSocketManager()