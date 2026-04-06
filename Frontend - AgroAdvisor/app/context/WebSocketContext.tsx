"use client";

import React, { createContext, useContext, useEffect, useRef, useState, useCallback, ReactNode } from 'react';

const getWsUrl = () => {
  if (typeof window !== 'undefined') {
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const port = window.location.port;
    // Jika diakses melalui Nginx (port 80/8080/kosong), WebSocket lewat proxy
    if (port === '' || port === '80' || port === '8080' || port === '443') {
      return `${protocol}://${window.location.host}/ws`;
    }
    // Development mode — langsung ke backend
    return `ws://${window.location.hostname}:8001/ws`;
  }
  return 'ws://localhost:8001/ws';
};

const WS_URL = getWsUrl();

type Alert = {
  id: number;
  level: 'info' | 'warning' | 'error' | 'success' | string;
  pesan: string;
  tipe?: string;
};

interface WebSocketContextType {
  connected: boolean;
  sensor: any;
  pompa: any;
  stats: any;
  riwayatPupuk: any[];
  setRiwayatPupuk: React.Dispatch<React.SetStateAction<any[]>>;
  riwayatPestisida: any[];
  setRiwayatPestisida: React.Dispatch<React.SetStateAction<any[]>>;
  alerts: Alert[];
  addAlert: (alert: Omit<Alert, 'id'>) => void;
  dismissAlert: (id: number) => void;
  lastEvent: any;
  send: (data: any) => void;
}

const WebSocketContext = createContext<WebSocketContextType | null>(null);

export function WebSocketProvider({ children }: { children: ReactNode }) {
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<NodeJS.Timeout | null>(null);
  const [connected, setConnected] = useState(false);
  const [sensor, setSensor] = useState<any>(null);
  const [pompa, setPompa] = useState<any>(null);
  const [stats, setStats] = useState<any>(null);
  const [riwayatPupuk, setRiwayatPupuk] = useState<any[]>([]);
  const [riwayatPestisida, setRiwayatPestisida] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [lastEvent, setLastEvent] = useState<any>(null);

  const addAlert = useCallback((alert: Omit<Alert, 'id'>) => {
    const id = Date.now();
    setAlerts(prev => [{ ...alert, id }, ...prev].slice(0, 10));
    // Auto dismiss setelah 5 detik (5000ms) untuk semua level
    setTimeout(() => setAlerts(prev => prev.filter(a => a.id !== id)), 5000);
  }, []);

  const dismissAlert = useCallback((id: number) => {
    setAlerts(prev => prev.filter(a => a.id !== id));
  }, []);

  const connect = useCallback(() => {
    if (typeof window === 'undefined') return;
    if (ws.current?.readyState === WebSocket.OPEN) return;

    ws.current = new WebSocket(WS_URL);

    ws.current.onopen = () => {
      setConnected(true);
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
    };

    ws.current.onclose = () => {
      setConnected(false);
      // Reconnect setelah 4 detik
      reconnectTimer.current = setTimeout(connect, 4000);
    };

    ws.current.onerror = () => {
      ws.current?.close();
    };

    ws.current.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data);
        setLastEvent(msg);

        switch (msg.tipe) {
          case 'snapshot':
            if (msg.data.sensor)           setSensor(msg.data.sensor);
            if (msg.data.pompa)            setPompa(msg.data.pompa);
            if (msg.data.statistik)        setStats(msg.data.statistik);
            if (msg.data.riwayat_pupuk)    setRiwayatPupuk(msg.data.riwayat_pupuk);
            if (msg.data.riwayat_pestisida) setRiwayatPestisida(msg.data.riwayat_pestisida);
            break;

          case 'sensor_update':
            setSensor((prev: any) => ({ ...prev, ...msg.data }));
            break;

          case 'pompa_update':
            setPompa((prev: any) => ({ ...prev, ...msg.data }));
            addAlert({ level: 'info', pesan: `Pompa: ${msg.data.alasan}` });
            break;

          case 'rekomendasi_pupuk':
            addAlert({ level: 'info', pesan: msg.data.pesan, tipe: 'pupuk' });
            setRiwayatPupuk((prev) => [{
              jenis_tanaman: msg.data.jenis_tanaman,
              kondisi_tanah_ringkasan: msg.data.ringkasan,
              estimasi_peningkatan: msg.data.estimasi,
              dibuat_pada: msg.timestamp,
            }, ...prev].slice(0, 20));
            break;

          case 'rekomendasi_pestisida':
            addAlert({ level: 'info', pesan: msg.data.pesan, tipe: 'pestisida' });
            setRiwayatPestisida((prev) => [{
              jenis_tanaman: msg.data.jenis_tanaman,
              jenis_hama: msg.data.jenis_hama,
              tingkat_serangan: msg.data.tingkat_serangan,
              dibuat_pada: msg.timestamp,
            }, ...prev].slice(0, 20));
            break;

          case 'alert':
            addAlert({ level: msg.data.level, pesan: msg.data.pesan });
            break;

          default:
            break;
        }
      } catch (_) {}
    };
  }, [addAlert]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      ws.current?.close();
    };
  }, [connect]);

  const send = useCallback((data: any) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(data));
    }
  }, []);

  return (
    <WebSocketContext.Provider value={{
      connected, sensor, pompa, stats,
      riwayatPupuk, setRiwayatPupuk,
      riwayatPestisida, setRiwayatPestisida,
      alerts, addAlert, dismissAlert,
      lastEvent, send,
    }}>
      {children}
    </WebSocketContext.Provider>
  );
}

export const useWS = () => {
  const context = useContext(WebSocketContext);
  if (!context) throw new Error("useWS must be used within a WebSocketProvider");
  return context;
};
