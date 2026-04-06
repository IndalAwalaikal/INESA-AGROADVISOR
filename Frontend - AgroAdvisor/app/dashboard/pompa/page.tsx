"use client"

import { useState, useEffect, useRef } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import { useWS } from "@/app/context/WebSocketContext"
import { 
  getConfigPompa, 
  postUpdateConfigPompa, 
  postKontrolPompa, 
  getRiwayatPompa,
  getJadwalPompa,
  postJadwalPompa,
  deleteJadwalPompa,
  toggleJadwalPompa,
  getHujanAlert,
} from "@/app/utils/api"

export default function PompaPage() {
  const { sensor, pompa, stats, addAlert } = useWS()
  
  const [config, setConfig] = useState({
    mode: 'otomatis',
    kelembaban_nyala: 40,
    kelembaban_mati: 60,
    maks_durasi_menit: 45
  })
  const [history, setHistory] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [updatingConfig, setUpdatingConfig] = useState(false)
  const [currentTime, setCurrentTime] = useState<string>('')

  // Jadwal state
  const [jadwalList, setJadwalList] = useState<any[]>([])
  const [newJam, setNewJam] = useState('06:00')
  const [newDurasi, setNewDurasi] = useState(15)
  const [addingJadwal, setAddingJadwal] = useState(false)

  // Weather alert
  const [weatherAlert, setWeatherAlert] = useState<any>(null)

  // Track previous pump status to detect changes
  const prevPompaStatus = useRef<string | null>(null)

  useEffect(() => {
    setCurrentTime(new Date().toLocaleTimeString())
    const interval = setInterval(() => {
      setCurrentTime(new Date().toLocaleTimeString())
    }, 1000)
    return () => clearInterval(interval)
  }, [])

  // Show notification when pump turns on/off
  useEffect(() => {
    if (pompa?.status) {
      if (prevPompaStatus.current && prevPompaStatus.current !== pompa.status) {
        if (pompa.status === 'nyala' || pompa.status === 'manual_nyala') {
          addAlert({ level: "success", pesan: `Pompa baru saja MENYALA (${pompa.alasan_terakhir})` })
        } else if (pompa.status === 'mati' || pompa.status === 'manual_mati') {
          addAlert({ level: "info", pesan: `Pompa baru saja MATI (${pompa.alasan_terakhir})` })
        }
      }
      prevPompaStatus.current = pompa.status
    }
  }, [pompa?.status, pompa?.alasan_terakhir, addAlert])

  useEffect(() => {
    fetchInitialData()
  }, [])

  async function fetchInitialData() {
    try {
      const [confRes, histRes, jadwalRes] = await Promise.all([
        getConfigPompa(),
        getRiwayatPompa(1, 10),
        getJadwalPompa(),
      ])
      if (confRes.data.konfigurasi) {
        setConfig(confRes.data.konfigurasi)
      }
      setHistory(histRes.data.data)
      setJadwalList(jadwalRes.data.data || [])
    } catch (err) {
      console.error("Gagal mengambil data pompa", err)
    }
    // Fetch weather alert (non-blocking)
    try {
      const alertRes = await getHujanAlert()
      setWeatherAlert(alertRes.data)
    } catch {}
  }

  async function handleSetMode(newMode: string) {
    setUpdatingConfig(true)
    try {
      await postUpdateConfigPompa({ ...config, mode: newMode })
      setConfig(prev => ({ ...prev, mode: newMode }))
    } catch (err) {
      addAlert({ level: "error", pesan: "Gagal merubah mode pompa" })
    } finally {
      setUpdatingConfig(false)
    }
  }

  async function handleAddJadwal() {
    setAddingJadwal(true)
    try {
      await postJadwalPompa({ jam: newJam, durasi_menit: newDurasi })
      const res = await getJadwalPompa()
      setJadwalList(res.data.data || [])
      addAlert({ level: "success", pesan: `Jadwal ${newJam} (${newDurasi}m) ditambahkan` })
    } catch {
      addAlert({ level: "error", pesan: "Gagal menambahkan jadwal" })
    } finally {
      setAddingJadwal(false)
    }
  }

  async function handleDeleteJadwal(id: number) {
    try {
      await deleteJadwalPompa(id)
      setJadwalList(prev => prev.filter(j => j.id !== id))
    } catch {
      addAlert({ level: "error", pesan: "Gagal menghapus jadwal" })
    }
  }

  async function handleToggleJadwal(id: number, aktif: boolean) {
    try {
      await toggleJadwalPompa(id, aktif)
      setJadwalList(prev => prev.map(j => j.id === id ? { ...j, aktif } : j))
    } catch {
      addAlert({ level: "error", pesan: "Gagal mengubah status jadwal" })
    }
  }

  async function handleManualControl(turnOn: boolean) {
    if (config.mode !== 'manual') {
      addAlert({ level: "warning", pesan: "Pilih Mode Manual terlebih dahulu." })
      return
    }
    setLoading(true)
    try {
      await postKontrolPompa(turnOn ? 'on' : 'off')
      // UI akan terupdate via WebSocket
    } catch (err) {
      addAlert({ level: "error", pesan: "Gagal mengirim perintah ke pompa" })
    } finally {
      setLoading(false)
    }
  }

  async function handleSaveSettings(e: React.FormEvent) {
    e.preventDefault()
    setUpdatingConfig(true)
    try {
      await postUpdateConfigPompa(config)
      addAlert({ level: "success", pesan: "Pengaturan pompa berhasil disimpan" })
    } catch (err) {
      addAlert({ level: "error", pesan: "Gagal menyimpan pengaturan" })
    } finally {
      setUpdatingConfig(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white">Manajemen Pompa & Irigasi</h1>
        <p className="text-white/40 mt-1">
          Kontrol presisi sistem pengairan berbasis IoT.
        </p>
      </div>

      {/* Weather Alert Banner */}
      {weatherAlert?.akan_hujan && (
        <div className="p-3 bg-blue-500/10 border border-blue-500/20 rounded-xl flex items-center gap-3 animate-in fade-in">
          <span className="text-xl">🌧️</span>
          <div className="flex-1">
            <p className="text-sm font-medium text-blue-300">{weatherAlert.pesan}</p>
            <p className="text-[10px] text-blue-300/60">Pompa otomatis akan ditunda untuk menghemat air.</p>
          </div>
        </div>
      )}

      <div className="grid lg:grid-cols-12 gap-6">
        {/* Monitoring & Status */}
        <div className="lg:col-span-8 space-y-6">
          <div className="grid sm:grid-cols-2 gap-4">
            {/* Real-time Status Card */}
            <Card className="border-white/[0.06] bg-white/[0.03] shadow-none overflow-hidden">
               <div className={`h-1.5 w-full ${(pompa?.status === 'on' || pompa?.status === 'nyala' || pompa?.status === 'manual_nyala') ? 'bg-primary animate-pulse' : 'bg-white/10'}`} />
               <CardContent className="pt-6">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="text-white/60 text-xs font-medium uppercase tracking-widest">Status Saat Ini</h3>
                      <div className="flex items-baseline gap-2 mt-1">
                        <span className={`text-3xl font-bold ${(pompa?.status === 'on' || pompa?.status === 'nyala' || pompa?.status === 'manual_nyala') ? 'text-primary' : 'text-white/40'}`}>
                          {(pompa?.status === 'on' || pompa?.status === 'nyala' || pompa?.status === 'manual_nyala') ? 'MENYALA' : 'MATI'}
                        </span>
                      </div>
                    </div>
                    <div className={`p-3 rounded-xl ${(pompa?.status === 'on' || pompa?.status === 'nyala' || pompa?.status === 'manual_nyala') ? 'bg-primary/10 text-primary' : 'bg-white/5 text-white/20'}`}>
                       <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                         <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                       </svg>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-white/40">
                    <span className="flex h-2 w-2 rounded-full bg-primary animate-pulse" />
                    Last update: {currentTime}
                  </div>
               </CardContent>
            </Card>

            {/* Sensor Context */}
            <Card className="border-white/[0.06] bg-white/[0.03] shadow-none">
               <CardContent className="pt-6">
                  <h3 className="text-white/60 text-xs font-medium uppercase tracking-widest mb-4">Kondisi Tanah (Live)</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-2xl font-bold text-white">{sensor?.kelembaban_tanah || '-'}%</div>
                      <div className="text-[10px] text-white/30 uppercase">Kelembaban</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-white">{sensor?.suhu_udara || '-'}°C</div>
                      <div className="text-[10px] text-white/30 uppercase">Suhu Tanah</div>
                    </div>
                  </div>
                  <div className="mt-4 pt-4 border-t border-white/[0.04]">
                     <div className="flex justify-between text-[10px]">
                        <span className="text-white/30">AMBIENT</span>
                        <span className="text-white/60">{sensor?.kelembapan_udara || '-'}% RH / {sensor?.suhu_udara || '-'}°C</span>
                     </div>
                  </div>
               </CardContent>
            </Card>
          </div>

          {/* History Log */}
          <Card className="border-white/[0.06] bg-white/[0.03] shadow-none overflow-hidden">
            <CardHeader className="pb-3 border-b border-white/[0.04] bg-white/[0.01]">
              <CardTitle className="text-sm font-semibold text-white uppercase tracking-wider">Log Aktivitas Terbaru</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-white/[0.04] text-white/30 text-[10px] uppercase tracking-widest">
                      <th className="px-6 py-3 font-medium">Waktu</th>
                      <th className="px-6 py-3 font-medium">Aksi</th>
                      <th className="px-6 py-3 font-medium">Trigger</th>
                      <th className="px-6 py-3 font-medium">Durasi</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/[0.04]">
                    {history.length > 0 ? history.map((log, i) => (
                      <tr key={i} className="text-white/70 hover:bg-white/[0.02] transition-colors">
                        <td className="px-6 py-4 whitespace-nowrap text-xs">
                          {new Date(log.dicatat_pada).toLocaleString('id-ID', { hour: '2-digit', minute: '2-digit', second: '2-digit', day: '2-digit', month: 'short' })}
                        </td>
                        <td className="px-6 py-4">
                           <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${log.status === 'nyala' || log.status === 'manual_nyala' ? 'bg-primary/10 text-primary border border-primary/20' : 'bg-white/5 text-white/40 border border-white/10'}`}>
                             {(log.status || '').toUpperCase()}
                           </span>
                        </td>
                        <td className="px-6 py-4 text-xs font-mono">{log.trigger_oleh}</td>
                        <td className="px-6 py-4 text-xs">{log.durasi_menit ? `${log.durasi_menit}m` : '-'}</td>
                      </tr>
                    )) : (
                      <tr>
                        <td colSpan={4} className="px-6 py-10 text-center text-white/20 italic">Belum ada data riwayat</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Configuration Column */}
        <div className="lg:col-span-4 space-y-6">
           <Card className="border-white/[0.06] bg-white/[0.03] shadow-none">
              <CardHeader className="pb-3 border-b border-white/[0.04]">
                 <CardTitle className="text-sm font-semibold text-white">KONTROL SISTEM</CardTitle>
              </CardHeader>
              <CardContent className="pt-5 space-y-6">
                 {/* Mode Toggle — 3 state */}
                 <div className="space-y-2">
                    <div className="text-[10px] font-medium text-white/40 uppercase tracking-widest">Mode Pompa</div>
                    <div className="grid grid-cols-3 gap-1 p-1 bg-black/40 rounded-lg border border-white/[0.04]">
                       {['otomatis', 'manual', 'terjadwal'].map(m => (
                          <button
                            key={m}
                            onClick={() => handleSetMode(m)}
                            disabled={updatingConfig}
                            className={`py-2 px-2 rounded-md text-[10px] font-bold uppercase tracking-wider transition-all ${
                              config.mode === m 
                                ? 'bg-primary text-white shadow-lg shadow-primary/20' 
                                : 'text-white/40 hover:text-white/60 hover:bg-white/5'
                            }`}
                          >
                            {m === 'otomatis' ? 'Auto' : m === 'manual' ? 'Manual' : 'Jadwal'}
                          </button>
                       ))}
                    </div>
                 </div>

                 {/* Manual Override (Only if manual mode) */}
                 {config.mode === 'manual' && (
                    <div className="p-4 rounded-xl bg-primary/5 border border-primary/10 space-y-4 animate-in fade-in slide-in-from-top-2">
                       <h4 className="text-[10px] font-bold text-primary uppercase tracking-widest">Manual Override</h4>
                       <div className="flex gap-2">
                          <Button 
                            onClick={() => handleManualControl(true)}
                            disabled={loading || (pompa?.status === 'on' || pompa?.status === 'nyala' || pompa?.status === 'manual_nyala')}
                            className="flex-1 bg-primary text-white hover:bg-primary/90 shadow-lg shadow-primary/20"
                          >
                             NYALAKAN
                          </Button>
                          <Button 
                            onClick={() => handleManualControl(false)}
                            disabled={loading || (!pompa?.status) || (pompa?.status === 'off' || pompa?.status === 'mati' || pompa?.status === 'manual_mati' || pompa?.status === 'nonaktif')}
                            variant="secondary"
                            className="flex-1 bg-white/10 text-white hover:bg-white/20"
                          >
                             MATIKAN
                          </Button>
                       </div>
                       <p className="text-[10px] text-white/40 italic text-center">Kontrol ini langsung mengirim sinyal ke hardware.</p>
                    </div>
                 )}

                 {/* Config Form */}
                 <form onSubmit={handleSaveSettings} className="space-y-4 pt-4 border-t border-white/[0.04]">
                    <div className="space-y-4">
                       <label className="text-[10px] font-medium text-white/40 uppercase tracking-widest">Ambang Batas Nyala (%)</label>
                       <div className="flex items-center gap-4">
                          <input 
                            type="range" min="0" max="100" 
                            value={config.kelembaban_nyala || 0}
                            onChange={e => setConfig({...config, kelembaban_nyala: parseInt(e.target.value)})}
                            className="flex-1 accent-primary"
                          />
                          <span className="text-sm font-bold text-white w-10 text-center">{config.kelembaban_nyala}%</span>
                       </div>
                    </div>

                    <div className="space-y-4">
                       <label className="text-[10px] font-medium text-white/40 uppercase tracking-widest">Ambang Batas Mati (Target %)</label>
                       <div className="flex items-center gap-4">
                          <input 
                            type="range" min="0" max="100" 
                            value={config.kelembaban_mati || 0}
                            onChange={e => setConfig({...config, kelembaban_mati: parseInt(e.target.value)})}
                            className="flex-1 accent-blue-500"
                          />
                          <span className="text-sm font-bold text-blue-400 w-10 text-center">{config.kelembaban_mati}%</span>
                       </div>
                       <p className="text-[9px] text-white/30 italic">Pompa akan terus menyala hingga kelembaban mencapai target ini.</p>
                    </div>

                    <div>
                       <label className="text-[10px] font-medium text-white/40 uppercase tracking-widest block mb-2">Maks Durasi Siram (Menit)</label>
                       <input 
                         type="number" 
                         value={config.maks_durasi_menit || 0}
                         onChange={e => setConfig({...config, maks_durasi_menit: parseInt(e.target.value) || 0})}
                         className="w-full bg-black/40 border border-white/[0.08] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-primary"
                       />
                    </div>

                    <Button 
                      type="submit" 
                      disabled={updatingConfig}
                      className="w-full bg-white/5 border border-white/10 text-white hover:bg-white/10"
                    >
                       {updatingConfig ? 'Menyimpan...' : 'Simpan Pengaturan'}
                    </Button>
                 </form>

                 {/* Jadwal Terjadwal Section */}
                 {config.mode === 'terjadwal' && (
                   <div className="space-y-4 pt-4 border-t border-white/[0.04] animate-in fade-in slide-in-from-top-2">
                     <h4 className="text-[10px] font-bold text-primary uppercase tracking-widest">Jadwal Penyiraman</h4>
                     <div className="flex gap-2">
                       <input type="time" value={newJam} onChange={e => setNewJam(e.target.value)}
                         className="flex-1 bg-black/40 border border-white/[0.08] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-primary" />
                       <input type="number" min={1} max={120} value={newDurasi} onChange={e => setNewDurasi(parseInt(e.target.value) || 15)} placeholder="menit"
                         className="w-20 bg-black/40 border border-white/[0.08] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-primary" />
                       <Button onClick={handleAddJadwal} disabled={addingJadwal} className="bg-primary text-white px-3" size="sm">+</Button>
                     </div>
                     {jadwalList.length > 0 ? (
                       <div className="space-y-2">
                         {jadwalList.map(j => (
                           <div key={j.id} className="flex items-center justify-between p-3 rounded-lg bg-black/30 border border-white/[0.06]">
                             <div className="flex items-center gap-3">
                               <Switch checked={j.aktif} onCheckedChange={(v) => handleToggleJadwal(j.id, v)} />
                               <div>
                                 <div className={`text-sm font-mono font-bold ${j.aktif ? 'text-primary' : 'text-white/30'}`}>{j.jam?.substring(0, 5)}</div>
                                 <div className="text-[9px] text-white/30">{j.durasi_menit} menit</div>
                               </div>
                             </div>
                             <button onClick={() => handleDeleteJadwal(j.id)} className="text-white/20 hover:text-red-400 transition-colors text-lg">✕</button>
                           </div>
                         ))}
                       </div>
                     ) : (
                       <p className="text-[10px] text-white/30 italic text-center py-2">Belum ada jadwal. Tambahkan jadwal di atas.</p>
                     )}
                   </div>
                 )}
              </CardContent>
           </Card>

           {/* Stats Summary */}
           <Card className="border-white/[0.06] bg-white/[0.03] shadow-none">
              <CardContent className="pt-6 space-y-4">
                 <div className="flex justify-between items-end">
                    <div>
                       <div className="text-[10px] text-white/40 uppercase font-medium">Total Siram Hari Ini</div>
                       <div className="text-2xl font-bold text-white">{stats?.total_siram || 0} Kali</div>
                    </div>
                    <div className="text-[10px] text-primary font-bold">EST. 150L</div>
                 </div>
                 <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                    <div className="h-full bg-primary/40 w-2/3" />
                 </div>
              </CardContent>
           </Card>
        </div>
      </div>
    </div>
  )
}
