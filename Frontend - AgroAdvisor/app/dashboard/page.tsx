"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useWS } from "@/app/context/WebSocketContext"
import { postAlur2Saran, postResetSesi, getCuacaSekarang, getHujanAlert } from "@/app/utils/api"
import { Button } from "@/components/ui/button"
import { BarChart, Bar, XAxis, YAxis, Tooltip as ChartTooltip, ResponsiveContainer, Cell, CartesianGrid } from "recharts"
import { ChevronDown, ChevronUp } from "lucide-react"

export default function DashboardPage() {
  const { sensor, stats, riwayatPupuk, riwayatPestisida, addAlert } = useWS()
  const [saranTanaman, setSaranTanaman] = useState<any>(null)
  const [loadingSaran, setLoadingSaran] = useState(false)
  const [resetting, setResetting] = useState(false)
  const [isExpanded, setIsExpanded] = useState(false)
  const [weather, setWeather] = useState<any>(null)
  const [weatherAlert, setWeatherAlert] = useState<any>(null)

  useEffect(() => {
    // Load saran dari cache agar tidak render ulang lambat
    const cachedSaran = localStorage.getItem('last_saran_tanaman')
    if (cachedSaran) {
      try {
        setSaranTanaman(JSON.parse(cachedSaran))
      } catch (e) {}
    } else if (sensor) {
      fetchSaran()
    }
  }, [sensor])

  useEffect(() => {
    fetchWeather()
  }, [])

  async function fetchWeather() {
    try {
      const [wRes, aRes] = await Promise.allSettled([
        getCuacaSekarang(),
        getHujanAlert()
      ])
      if (wRes.status === 'fulfilled') setWeather(wRes.value.data)
      if (aRes.status === 'fulfilled') setWeatherAlert(aRes.value.data)
    } catch (e) {
      console.error("Gagal load cuaca", e)
    }
  }

  async function fetchSaran() {
    setLoadingSaran(true)
    try {
      // Use the exact same endpoint as the Pupuk page (Otomatis mode)
      const res = await postAlur2Saran({ 
        luas_lahan: 1, // Defaulting to 1 hectare for dashboard preview
        gunakan_sensor_live: true
      })
      
      const alur2 = res.data.saran_alur2
      setSaranTanaman(alur2)
      localStorage.setItem('last_saran_tanaman', JSON.stringify(alur2))
      if (alur2) {
        addAlert({ level: 'info', pesan: 'Rekomendasi tanaman berhasil dianalisis.' })
      }
    } catch (_) {
      addAlert({ level: 'error', pesan: 'Gagal menganalisis saran tanaman.' })
    }
    finally { setLoadingSaran(false) }
  }

  async function handleReset() {
    if (!window.confirm('Reset sesi? Data lama tetap tersimpan untuk pembelajaran AI.')) return
    setResetting(true)
    try {
      await postResetSesi({ catatan_reset: 'Reset dari dashboard AGRO' })
      localStorage.removeItem('last_rekomendasi_pupuk')
      localStorage.removeItem('last_form_pupuk')
      localStorage.removeItem('last_rekomendasi_pestisida')
      localStorage.removeItem('last_form_pestisida')
      localStorage.removeItem('last_saran_tanaman')

      addAlert({ level: 'info', pesan: 'Sesi berhasil direset. Sesi baru dimulai.' })
      fetchSaran()
    } finally { setResetting(false) }
  }

  const s = sensor || {}

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Monitoring Lahan</h1>
          <p className="text-white/40 mt-1">
            {s.lokasi || 'Lahan'} · Device: {s.device_id || 'Menunggu sensor...'}
            {s.timestamp && (
              <span className="ml-2 px-2 py-0.5 rounded-md bg-white/[0.05] text-xs font-mono">
                {new Date(s.timestamp).toLocaleTimeString()}
              </span>
            )}
          </p>
        </div>
        <Button 
          variant="outline" 
          onClick={handleReset} 
          disabled={resetting}
          className="border-white/[0.1] text-white/70 hover:bg-white/[0.05] hover:text-white transition-colors"
        >
          {resetting ? "Resetting..." : "↺ Reset Sesi"}
        </Button>
      </div>

      {/* Stats Grid live */}
      <div className="grid gap-4 grid-cols-2 md:grid-cols-3 lg:grid-cols-6">
        {[
          { label: 'pH Tanah', value: s.ph_tanah, unit: '', status: s.status_ph },
          { label: 'Nitrogen', value: s.nitrogen, unit: 'mg/kg', status: s.status_nitrogen },
          { label: 'Fosfor', value: s.fosfor, unit: 'mg/kg', status: s.status_fosfor },
          { label: 'Kalium', value: s.kalium, unit: 'mg/kg', status: s.status_kalium },
          { label: 'Suhu', value: s.suhu_udara, unit: '°C', status: s.suhu_udara > 35 ? 'tinggi' : 'normal' },
          { label: 'Kelembaban', value: s.kelembaban_tanah, unit: '%', status: s.kelembaban_tanah < 30 ? 'rendah' : 'normal' },
        ].map((stat, idx) => {
          let colorClass = "text-primary"
          if (stat.status === "rendah") colorClass = "text-amber-500"
          if (stat.status === "tinggi") colorClass = "text-red-500"
          
          return (
            <Card key={idx} className="border-white/[0.06] bg-[#141b16] shadow-none backdrop-blur-sm">
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-medium text-white/50">{stat.label}</span>
                  {stat.value && (
                    <div className={`h-1.5 w-1.5 rounded-full ${
                      stat.status === 'optimal' || stat.status === 'normal' ? 'bg-primary' :
                      stat.status === 'rendah' ? 'bg-amber-500' : 'bg-red-500'
                    } animate-pulse`} />
                  )}
                </div>
                <div className="flex items-baseline gap-1">
                  <span className={`text-2xl font-bold font-mono ${colorClass}`}>
                    {stat.value !== undefined ? stat.value : '—'}
                  </span>
                  <span className="text-xs text-white/30">{stat.unit}</span>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Widget Cuaca Lokal */}
        {weather && (
          <Card className="border-white/[0.06] bg-white/[0.03] shadow-none backdrop-blur-sm lg:col-span-2">
            <CardHeader className="pb-2 flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-base font-semibold text-white">Cuaca Lokal</CardTitle>
                <p className="text-xs text-white/40 mt-1">{weather.lokasi || weather.kota || 'Unknown'}</p>
              </div>
              <Button 
                size="sm" variant="outline" onClick={fetchWeather}
                className="border-primary/20 text-primary hover:bg-primary/10 transition-colors h-8 text-xs"
              >
                ↻ Refresh
              </Button>
            </CardHeader>
            <CardContent>
              {weather.tersedia === false ? (
                <div className="p-4 bg-white/5 border border-white/10 rounded-xl text-center">
                  <span className="text-3xl mb-2 block">☁️</span>
                  <div className="text-sm text-white/60">{weather.pesan}</div>
                </div>
              ) : (
                <>
                  <div className="flex flex-col sm:flex-row items-center gap-6">
                    <div className="flex items-center gap-4">
                      <span className="text-4xl">{weather.ikon ? `https://openweathermap.org/img/wn/${weather.ikon}@2x.png` : '☁️'}</span>
                      {/* Note: Ikon string can be used to load image manually if needed, but for now we rely on emoji or image */}
                      <div>
                        <div className="text-3xl font-bold text-white">{weather.suhu}°C</div>
                        <div className="text-sm text-white/60 capitalize">{weather.deskripsi}</div>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4 flex-1 w-full sm:w-auto mt-4 sm:mt-0 pt-4 sm:pt-0 border-t sm:border-t-0 sm:border-l border-white/[0.06] sm:pl-6">
                      <div>
                        <div className="text-[10px] text-white/40 uppercase tracking-wider mb-1">Kelembaban</div>
                        <div className="text-lg font-mono text-white/80">{weather.kelembaban}%</div>
                      </div>
                      <div>
                        <div className="text-[10px] text-white/40 uppercase tracking-wider mb-1">Angin</div>
                        <div className="text-lg font-mono text-white/80">{weather.kecepatan_angin || weather.angin} km/j</div>
                      </div>
                    </div>
                  </div>
                  
                  {weatherAlert?.akan_hujan && (
                    <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/20 rounded-xl flex items-start gap-3 animate-in fade-in">
                      <span className="text-xl">🌧️</span>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-blue-300">{weatherAlert.pesan}</p>
                        <p className="text-[10px] text-blue-300/60 mt-0.5">Sistem irigasi otomatis menunda jadwal penyiraman.</p>
                      </div>
                    </div>
                  )}
                </>
              )}
            </CardContent>
          </Card>
        )}

        {/* Visualisasi Nutrisi (NPK) Chart */}
        <Card className="border-white/[0.06] bg-white/[0.03] shadow-none backdrop-blur-sm lg:col-span-2">
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-semibold text-white">Visualisasi Nutrisi Tanah (NPK)</CardTitle>
            <p className="text-xs text-white/40 mt-1">Estimasi ketersediaan Nitrogen, Fosfor, dan Kalium saat ini (mg/kg)</p>
          </CardHeader>
          <CardContent className="h-[250px] w-full pt-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={[
                  { name: 'Nitrogen (N)', value: s.nitrogen || 0, fill: '#3b82f6' }, // Blue
                  { name: 'Fosfor (P)', value: s.fosfor || 0, fill: '#8b5cf6' },    // Purple
                  { name: 'Kalium (K)', value: s.kalium || 0, fill: '#f59e0b' },    // Amber
                ]}
                margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
                <XAxis dataKey="name" stroke="#ffffff40" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#ffffff40" fontSize={12} tickLine={false} axisLine={false} />
                <ChartTooltip 
                  cursor={{ fill: '#ffffff05' }}
                  contentStyle={{ backgroundColor: '#141b16', borderColor: '#ffffff10', color: '#fff', borderRadius: '8px', fontSize: '12px' }}
                  itemStyle={{ color: '#fff' }}
                />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {
                    [0, 1, 2].map((index) => (
                      <Cell key={`cell-${index}`} />
                    ))
                  }
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Saran Tanaman AI */}
        <Card className="border-white/[0.06] bg-white/[0.03] shadow-none backdrop-blur-sm lg:col-span-2">
          <CardHeader className="pb-3 flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-base font-semibold text-white">Saran Tanaman AI</CardTitle>
              <p className="text-xs text-white/40 mt-1">Berdasarkan kondisi tanah saat ini</p>
            </div>
            <Button 
              size="sm" 
              variant="outline" 
              onClick={fetchSaran} 
              disabled={loadingSaran}
              className="border-primary/20 text-primary hover:bg-primary/10 hover:text-primary transition-colors h-8 text-xs"
            >
              {loadingSaran ? "Menganalisis..." : "↻ Analisis Ulang"}
            </Button>
          </CardHeader>
          <CardContent>
            {loadingSaran && !saranTanaman && (
              <div className="py-8 text-center text-sm text-white/40 animate-pulse">
                AI sedang menganalisis kondisi sensor tanah...
              </div>
            )}
            
            {saranTanaman && (
              <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-500">
                <div className="p-4 rounded-lg border border-white/[0.06] bg-black/20 mb-4">
                  <div className="text-xs font-semibold text-white/60 uppercase tracking-widest mb-3">
                    GAMBARAN TANAH SAAT INI
                  </div>
                  <p className="text-sm text-white/80 leading-relaxed">
                    {saranTanaman.kondisi_ringkasan || "Kondisi tanah sesuai pembacaan sensor."}
                  </p>
                </div>
                
                {(() => {
                  const items = saranTanaman.rekomendasi || []
                  if (items.length === 0) return null

                  const maxVisiblePerColumn = 5
                  const half = Math.ceil(items.length / 2)
                  const leftItemsFull = items.slice(0, half)
                  const rightItemsFull = items.slice(half)
                  
                  const leftItems = isExpanded ? leftItemsFull : leftItemsFull.slice(0, maxVisiblePerColumn)
                  const rightItems = isExpanded ? rightItemsFull : rightItemsFull.slice(0, maxVisiblePerColumn)
                  const showMoreButton = leftItemsFull.length > maxVisiblePerColumn || rightItemsFull.length > maxVisiblePerColumn

                  const renderItem = (rek: any, globalIdx: number) => (
                    <div key={globalIdx} className={`rounded-xl border border-white/[0.06] p-5 shadow-none backdrop-blur-md ${globalIdx === 0 ? 'bg-primary/[0.03] border-primary/30' : 'bg-white/[0.02]'}`}>
                      <div className="flex items-start gap-3 mb-3">
                        <span className="text-xl font-bold text-primary leading-none">{globalIdx + 1}.</span>
                        <div>
                          <h4 className="text-lg font-bold text-white tracking-wide capitalize">{rek.jenis_tanaman}</h4>
                          <p className="text-xs text-white/50 mt-1">{rek.estimasi_peningkatan}</p>
                        </div>
                      </div>
                      <p className="text-sm text-white/70 leading-relaxed bg-black/20 p-3 rounded-lg border border-white/[0.03]">{rek.alasan_cocok}</p>
                    </div>
                  )

                  return (
                    <div className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-4">
                          {leftItems.map((rek: any, idx: number) => renderItem(rek, idx))}
                        </div>
                        <div className="space-y-4">
                          {rightItems.map((rek: any, idx: number) => renderItem(rek, half + idx))}
                        </div>
                      </div>
                      
                      {showMoreButton && (
                        <div className="flex justify-center pt-2">
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            className="text-white/50 hover:text-white hover:bg-white/5 w-full max-w-sm flex items-center gap-2 border border-white/[0.05]"
                            onClick={() => setIsExpanded(!isExpanded)}
                          >
                            {isExpanded ? (
                              <>Lebih Sedikit <ChevronUp className="w-4 h-4" /></>
                            ) : (
                              <>Tampilkan Semua ({items.length} Tanaman) <ChevronDown className="w-4 h-4" /></>
                            )}
                          </Button>
                        </div>
                      )}
                    </div>
                  )
                })()}
              </div>
            )}
            
            {!saranTanaman && !loadingSaran && (
              <div className="py-8 text-center text-sm text-white/40">
                Data belum tersedia. Silakan klik Analisis Ulang.
              </div>
            )}
          </CardContent>
        </Card>

        {/* Statistik */}
        <Card className="border-white/[0.06] bg-white/[0.03] shadow-none backdrop-blur-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-semibold text-white">Statistik Sistem</CardTitle>
          </CardHeader>
          <CardContent>
             <div className="grid grid-cols-2 gap-4">
                {[
                  { label: "Total Sesi", value: stats?.total_sesi ?? "—" },
                  { label: "Total Rekomendasi", value: stats?.total_rekomendasi ?? "—" },
                  { label: "Deteksi Hama", value: stats?.total_pestisida ?? "—" },
                  { label: "Log Sensor", value: stats?.total_log_sensor ?? "—" },
                ].map((s, i) => (
                  <div key={i} className="p-4 rounded-lg bg-white/[0.02] border border-white/[0.04]">
                     <div className="text-xs text-white/40 mb-1">{s.label}</div>
                     <div className="text-xl font-bold font-mono text-white/90">{s.value}</div>
                  </div>
                ))}
             </div>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Card className="border-white/[0.06] bg-white/[0.03] shadow-none backdrop-blur-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-semibold text-white">Aksi Cepat Menu</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 sm:grid-cols-2">
              {[
                { title: "Analisis Pupuk", description: "Dapatkan rekomendasi pupuk AI", href: "/dashboard/pupuk" },
                { title: "Deteksi Pestisida", description: "Upload gambar hama", href: "/dashboard/pestisida" },
                { title: "Pengaturan Pompa", description: "Sistem irigasi otomatis", href: "/dashboard/pompa" },
                { title: "Lihat Riwayat", description: "Rekam jejak AI", href: "/dashboard/riwayat" },
              ].map((action) => (
                <a
                  key={action.title}
                  href={action.href}
                  className="flex flex-col rounded-lg border border-white/[0.06] bg-white/[0.02] p-4 transition-all hover:border-primary/30 hover:bg-primary/[0.05]"
                >
                  <div className="font-medium text-white/80">{action.title}</div>
                  <div className="text-xs text-white/40 mt-1">{action.description}</div>
                </a>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
