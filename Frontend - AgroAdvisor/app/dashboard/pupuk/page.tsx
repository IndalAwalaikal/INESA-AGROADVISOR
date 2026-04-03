"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { useWS } from "@/app/context/WebSocketContext"
import { 
  getDaftarTanaman, 
  postRekomendasiPupuk, 
  postAlur2Saran, 
  getPupukPDF,
  postFeedback 
} from "@/app/utils/api"
import { ChevronDown, ChevronUp } from "lucide-react"

export default function PupukPage() {
  const { sensor, addAlert } = useWS()
  
  const [mode, setMode] = useState<'otomatis'|'manual'>('otomatis')
  const [daftarTanaman, setDaftarTanaman] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [rekomendasi, setRekomendasi] = useState<any>(null)
  const [isExpanded, setIsExpanded] = useState(false)
  
  // Forms
  const [form, setForm] = useState({
    jenis_tanaman: '',
    fase_pertumbuhan: 'vegetatif',
    luas_lahan_m2: 1000,
    catatan_tambahan: ''
  })
  
  // Feedback
  const [feedback, setFeedback] = useState({ rating: 5, catatan: '', submitted: false })

  useEffect(() => {
    getDaftarTanaman().then(res => {
      if (res.data && res.data.tanaman) {
        setDaftarTanaman(res.data.tanaman.map((t: any) => t.nama));
      } else if (res.data && res.data.daftar_tanaman) {
        setDaftarTanaman(res.data.daftar_tanaman);
      }
    }).catch(() => {})
    
    const savedRec = localStorage.getItem('last_rekomendasi_pupuk')
    const savedForm = localStorage.getItem('last_form_pupuk')
    const savedMode = localStorage.getItem('last_mode_pupuk')
    
    if (savedRec) setRekomendasi(JSON.parse(savedRec))
    if (savedForm) setForm(JSON.parse(savedForm))
    if (savedMode === 'otomatis' || savedMode === 'manual') setMode(savedMode)
  }, [])

  useEffect(() => {
    localStorage.setItem('last_mode_pupuk', mode)
  }, [mode])

  function handleReset() {
    setRekomendasi(null)
    localStorage.removeItem('last_rekomendasi_pupuk')
  }

  async function handleAnalyze(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setRekomendasi(null)
    setFeedback({ rating: 5, catatan: '', submitted: false })
    try {
      let res;
      if (mode === 'otomatis') {
        res = await postAlur2Saran({ 
          luas_lahan: form.luas_lahan_m2 / 10000, 
          catatan_tambahan: form.catatan_tambahan || undefined,
          gunakan_sensor_live: true
        })
      } else {
        res = await postRekomendasiPupuk({
          jenis_tanaman: form.jenis_tanaman,
          fase_tumbuh: form.fase_pertumbuhan,
          luas_lahan: form.luas_lahan_m2 / 10000,
          catatan_tambahan: form.catatan_tambahan || undefined,
          gunakan_sensor_live: true
        })
      }
      setRekomendasi(res.data)
      localStorage.setItem('last_rekomendasi_pupuk', JSON.stringify(res.data))
      localStorage.setItem('last_form_pupuk', JSON.stringify(form))
      addAlert({ level: 'success', pesan: 'Rekomendasi pupuk sukses diberikan.' })
    } catch (err) {
      addAlert({ level: 'error', pesan: 'Gagal mendapatkan rekomendasi pupuk.' })
    } finally {
      setLoading(false)
    }
  }

  async function submitFeedback() {
    if (!rekomendasi) return
    try {
      await postFeedback({
        rekomendasi_id: rekomendasi.id,
        rating: feedback.rating,
        catatan_hasil: feedback.catatan
      })
      setFeedback(prev => ({ ...prev, submitted: true }))
    } catch (_) {
      addAlert({ level: "error", pesan: "Gagal mengirim feedback" })
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white">Rekomendasi Pupuk AI</h1>
        <p className="text-white/40 mt-1">
          Analisis cerdas berdasarkan data sensor real-time atau input manual.
        </p>
      </div>

      <div className="grid lg:grid-cols-12 gap-6">
        {/* Form Column */}
        <div className="lg:col-span-5 space-y-6">
          <Card className="border-white/[0.06] bg-white/[0.03] shadow-none backdrop-blur-sm">
            <CardHeader className="pb-3 border-b border-white/[0.04]">
              <div className="flex bg-black/40 p-1 rounded-lg">
                <button 
                  onClick={() => setMode('otomatis')}
                  className={`flex-1 py-2 text-sm font-medium rounded-md transition-all ${
                    mode === 'otomatis' ? 'bg-primary text-white shadow-sm' : 'text-white/40 hover:text-white/80'
                  }`}
                >
                  Mode Otomatis (Sensor)
                </button>
                <button 
                  onClick={() => setMode('manual')}
                  className={`flex-1 py-2 text-sm font-medium rounded-md transition-all ${
                    mode === 'manual' ? 'bg-primary text-white shadow-sm' : 'text-white/40 hover:text-white/80'
                  }`}
                >
                  Mode Manual
                </button>
              </div>
            </CardHeader>
            <CardContent className="pt-5">
               <form onSubmit={handleAnalyze} className="space-y-4">
                  {mode === 'otomatis' ? (
                    <div className="p-4 rounded-lg bg-green-500/10 border border-green-500/20 mb-4">
                      <div className="flex items-center gap-2 mb-2">
                        <div className="h-2 w-2 bg-green-500 rounded-full animate-pulse" />
                        <span className="text-sm font-semibold text-green-400">Sensor Tanah Aktif</span>
                      </div>
                      <p className="text-xs text-white/60 leading-relaxed">
                        AI akan secara otomatis membaca nilai pH ({sensor?.ph_tanah || '-'}), Nitrogen ({sensor?.nitrogen || '-'} mg/kg), Fosfor ({sensor?.fosfor || '-'} mg/kg), dan Kalium ({sensor?.kalium || '-'} mg/kg) untuk menyarankan tanaman yang cocok sekaligus dosis pupuknya.
                      </p>
                    </div>
                  ) : (
                    <>
                      <div>
                        <label className="text-xs font-medium text-white/50 uppercase tracking-wider">Jenis Tanaman</label>
                        <select 
                          required
                          value={form.jenis_tanaman || ''}
                          onChange={e => setForm({...form, jenis_tanaman: e.target.value})}
                          className="mt-1 w-full rounded-md border border-white/[0.08] bg-black/40 px-3 py-2 text-sm text-white focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                        >
                          <option value="" disabled>-- Pilih Tanaman --</option>
                          {daftarTanaman.map(t => <option key={t} value={t}>{t}</option>)}
                          <option value="lainnya">Lainnya...</option>
                        </select>
                      </div>
                      <div>
                        <label className="text-xs font-medium text-white/50 uppercase tracking-wider">Umur / Fase Tumbuh Tanaman</label>
                        <select 
                          value={form.fase_pertumbuhan || 'Minggu 3-4 (pertumbuhan awal)'}
                          onChange={e => setForm({...form, fase_pertumbuhan: e.target.value})}
                          className="mt-1 w-full rounded-md border border-white/[0.08] bg-black/40 px-3 py-2 text-sm text-white focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                        >
                          <option value="Minggu 1-2 (awal tanam / persemaian)">Minggu 1-2 (awal tanam / persemaian)</option>
                          <option value="Minggu 3-4 (pertumbuhan awal)">Minggu 3-4 (pertumbuhan awal)</option>
                          <option value="Minggu 5-6 (pertumbuhan aktif)">Minggu 5-6 (pertumbuhan aktif)</option>
                          <option value="Minggu 7-8 (menjelang berbunga)">Minggu 7-8 (menjelang berbunga)</option>
                          <option value="Minggu 9-10 (berbunga / pembentukan buah)">Minggu 9-10 (berbunga / pembentukan buah)</option>
                          <option value="Minggu 11-12 (pembesaran buah / pengisian biji)">Minggu 11-12 (pembesaran buah / pengisian biji)</option>
                          <option value="Minggu 13+ (menjelang panen)">Minggu 13+ (menjelang panen)</option>
                        </select>
                      </div>
                    </>
                  )}

                  <div className="grid grid-cols-2 gap-4">
                    <div className="col-span-2">
                      <label className="text-xs font-medium text-white/50 uppercase tracking-wider">Luas Lahan (m²)</label>
                      <input 
                        type="number" min="10" 
                        value={form.luas_lahan_m2 || ''}
                        onChange={e => setForm({...form, luas_lahan_m2: parseInt(e.target.value) || 0})}
                        className="mt-1 w-full rounded-md border border-white/[0.08] bg-black/40 px-3 py-2 text-sm text-white focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="text-xs font-medium text-white/50 uppercase tracking-wider">Catatan Tambahan (Opsional)</label>
                    <textarea 
                      placeholder="Contoh: Daun terlihat sedikit menguning..."
                      value={form.catatan_tambahan || ''}
                      onChange={e => setForm({...form, catatan_tambahan: e.target.value})}
                      className="mt-1 w-full rounded-md border border-white/[0.08] bg-black/40 px-3 py-2 text-sm text-white focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary min-h-[80px]"
                    />
                  </div>

                  <div className="flex gap-3">
                    <Button 
                      type="button" 
                      onClick={handleReset}
                      variant="outline" 
                      className="border-white/[0.08] text-white/60 hover:bg-white/[0.05] hover:text-white"
                    >
                      Reset
                    </Button>
                    <Button type="submit" className="flex-1 bg-primary text-white hover:bg-primary/90" disabled={loading || (mode === 'otomatis' && !sensor)}>
                      {loading ? "AI Sedang Menganalisis..." : mode === 'otomatis' && !sensor ? "Menunggu Sensor..." : "Mulai Analisis AI"}
                    </Button>
                  </div>
               </form>
            </CardContent>
          </Card>
        </div>

        {/* Results Column */}
        <div className="lg:col-span-7">
          {!rekomendasi && !loading && (
            <div className="h-full min-h-[400px] flex flex-col items-center justify-center border border-white/[0.04] border-dashed rounded-xl bg-white/[0.01]">
              <span className="text-sm font-bold tracking-widest text-white/20 mb-4 px-4 py-1 border border-white/10 rounded-full">SISTEM AI SIAP</span>
              <p className="text-white/40 text-sm">Isi form dan jalankan analisis untuk melihat hasil AI</p>
            </div>
          )}

          {loading && (
            <div className="h-full min-h-[400px] flex flex-col items-center justify-center border border-white/[0.04] rounded-xl bg-white/[0.01]">
              <div className="h-8 w-8 rounded-full border-2 border-primary border-t-transparent animate-spin mb-4" />
              <p className="text-primary text-sm font-medium animate-pulse">Menghitung dosis presisi...</p>
            </div>
          )}

          {rekomendasi && !loading && mode === 'otomatis' && (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
              <div className="p-4 rounded-lg border border-white/[0.06] bg-black/20">
                <div className="text-xs font-semibold text-white/60 uppercase tracking-widest mb-3">
                  GAMBARAN TANAH SAAT INI
                </div>
                <p className="text-sm text-white/80 leading-relaxed">
                  {rekomendasi.saran_alur2?.kondisi_ringkasan}
                </p>
              </div>

              {(() => {
                const items = rekomendasi.saran_alur2?.rekomendasi || []
                if (items.length === 0) return null

                const visibleItems = isExpanded ? items : items.slice(0, 3)
                const showMoreButton = items.length > 3

                return (
                  <div className="space-y-6">
                    {visibleItems.map((rek: any, idx: number) => (
                      <Card key={idx} className={`border-white/[0.06] shadow-none backdrop-blur-md ${idx === 0 ? 'bg-primary/[0.03] border-primary/30' : 'bg-white/[0.03]'}`}>
                        <CardHeader className="pb-3 border-b border-white/[0.04]">
                          <div className="flex items-center gap-3">
                            <span className="text-2xl font-bold text-primary">{idx + 1}.</span>
                            <CardTitle className="text-xl font-bold text-white tracking-wide capitalize">
                              {rek.jenis_tanaman}
                            </CardTitle>
                          </div>
                        </CardHeader>
                        <CardContent className="pt-4 space-y-4">
                          <p className="text-sm text-white/70 leading-relaxed">
                            {rek.alasan_cocok}
                          </p>
      
                          <div className="p-4 rounded-lg bg-black/30 border border-white/[0.03]">
                            <div className="text-[10px] text-white/40 uppercase tracking-widest mb-3">
                              DOSIS PUPUK TOTAL SEMUSIM ({form.luas_lahan_m2 / 10000} Ha)
                            </div>
                            <div className="space-y-2">
                              {rek.daftar_pupuk?.length > 0 ? (
                                rek.daftar_pupuk.map((p: any, pIdx: number) => (
                                  <div key={pIdx} className={`flex justify-between items-center py-2 ${pIdx < rek.daftar_pupuk.length - 1 ? 'border-b border-white/[0.04]' : ''}`}>
                                    <span className="text-sm text-white font-medium">{p.nama_pupuk}</span>
                                    <span className="text-sm text-green-400 font-mono">{p.takaran_total}</span>
                                  </div>
                                ))
                              ) : (
                                <div className="text-sm text-white/40 italic flex items-center gap-2">
                                   <span className="font-bold text-green-500">IDEAL</span> Tanah sudah ideal, tidak perlu pupuk tambahan.
                                </div>
                              )}
                            </div>
                          </div>
      
                          <div className="flex items-center gap-3 p-3 rounded-md bg-primary/10 border border-primary/20">
                            <div className="text-sm text-white/80">
                              <strong className="text-primary font-medium block mb-0.5">Potensi Peningkatan:</strong>
                              {rek.estimasi_peningkatan}
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                    
                    {showMoreButton && (
                      <div className="flex justify-center pt-2">
                        <Button 
                          variant="ghost" 
                          size="sm" 
                          className="text-white/50 hover:text-white hover:bg-white/5 w-full max-w-md flex items-center gap-2 border border-white/[0.05]"
                          onClick={() => setIsExpanded(!isExpanded)}
                        >
                          {isExpanded ? (
                            <>Tutup Tampilan <ChevronUp className="w-4 h-4" /></>
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

          {rekomendasi && !loading && mode === 'manual' && (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
              <Card className="border-white/[0.06] bg-gradient-to-br from-white/[0.04] to-transparent shadow-none backdrop-blur-md">
                <CardHeader className="pb-2 border-b border-white/[0.04] flex flex-row items-start justify-between">
                  <div>
                    <CardTitle className="text-lg font-bold text-white uppercase tracking-wide">
                      {rekomendasi.jenis_tanaman}
                    </CardTitle>
                    <p className="text-xs text-white/40 mt-1">
                      Fase: {rekomendasi.fase_tumbuh} • Target Area: {rekomendasi.luas_lahan_m2} m² • ID: {rekomendasi.rekomendasi_id}
                    </p>
                  </div>
                  <a 
                    href={getPupukPDF(rekomendasi.rekomendasi_id)} 
                    target="_blank" 
                    rel="noreferrer"
                    className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-white/[0.05] border border-white/[0.1] text-xs font-semibold hover:bg-white/[0.1] transition-colors"
                  >
                    <span>UNDUH PDF</span>
                  </a>
                </CardHeader>
                <CardContent className="pt-4 space-y-6">
                  
                  {/* Summary Box */}
                  <div className="grid sm:grid-cols-2 gap-4">
                    <div className="p-4 rounded-lg bg-black/30 border border-white/[0.03]">
                      <div className="text-[10px] text-white/40 uppercase tracking-widest mb-1">Kesesuaian Tanaman</div>
                      <div className="flex justify-between items-start">
                        <p className="text-sm font-medium text-white/80">{rekomendasi.kesesuaian_tanaman?.skor}</p>
                      </div>
                      <p className="text-xs text-white/50 mt-2">{rekomendasi.kesesuaian_tanaman?.penjelasan}</p>
                    </div>
                    <div className="p-4 rounded-lg bg-primary/10 border border-primary/20">
                      <div className="text-[10px] text-primary/60 uppercase tracking-widest mb-1">Estimasi Peningkatan</div>
                      <p className="text-lg font-bold text-primary">{rekomendasi.estimasi_peningkatan}</p>
                    </div>
                  </div>

                  {/* Analisis GAP */}
                  {rekomendasi.analisis_gap && (
                     <div className="p-4 rounded-lg border border-white/[0.06] bg-black/20">
                        <div className="text-xs font-semibold text-white/60 uppercase tracking-widest mb-3">Analisis Gap Kondisi vs Kebutuhan</div>
                        <div className="grid sm:grid-cols-2 gap-4">
                           {Object.entries(rekomendasi.analisis_gap).map(([unsur, gap]: any) => (
                              <div key={unsur} className="p-3 rounded bg-white/[0.02] border border-white/[0.03]">
                                 <div className="text-[10px] text-primary font-mono uppercase tracking-widest mb-1">{unsur}</div>
                                 <div className="text-xs text-white/70 leading-relaxed">{gap}</div>
                              </div>
                           ))}
                        </div>
                     </div>
                  )}

                  {/* Fertilizer List */}
                  <div>
                    <div className="text-xs font-semibold text-white/60 uppercase tracking-widest mb-3 flex items-center gap-2">
                       <div className="h-1.5 w-1.5 rounded-full bg-primary" />
                       Rekomendasi Pupuk Bersubsidi/Mudah Didapat
                    </div>
                    <div className="space-y-3">
                      {rekomendasi.daftar_pupuk?.map((p: any, idx: number) => (
                        <div key={idx} className="p-4 rounded-lg border-l-2 border-primary border-t border-r border-b border-t-white/[0.06] border-r-white/[0.06] border-b-white/[0.06] bg-white/[0.02]">
                           <div className="flex justify-between items-start mb-2">
                             <div>
                               <span className="text-[10px] text-primary font-mono mr-2">#{p.urutan}</span>
                               <span className="font-semibold text-white">{p.nama_pupuk}</span>
                               <span className="text-xs ml-2 text-white/40">{p.bahan_aktif}</span>
                             </div>
                             <div className="text-right">
                               <div className="text-sm text-green-400 font-mono font-bold">{p.takaran_total}</div>
                               <div className="text-[10px] text-white/40">{p.takaran_per_ha}</div>
                             </div>
                           </div>
                           
                           <div className="grid grid-cols-2 gap-4 border-t border-white/[0.04] pt-3 mt-3">
                              <div>
                                 <span className="text-[10px] text-white/40 block mb-0.5">Metode Aplikasi</span>
                                 <div className="text-xs text-white/80">{p.metode_aplikasi}</div>
                              </div>
                              <div>
                                 <span className="text-[10px] text-white/40 block mb-0.5">Waktu Aplikasi</span>
                                 <div className="text-xs text-white/80">{p.waktu_aplikasi}</div>
                              </div>
                           </div>
                           <div className="mt-3 text-[11px] text-white/50 italic">{p.tujuan}</div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Jadwal Aplikasi Box */}
                  <div className="p-4 rounded-lg bg-white/[0.02] border border-white/[0.06]">
                     <div className="text-[10px] text-white/50 uppercase tracking-widest mb-2 font-mono">JADWAL APLIKASI KESELURUHAN</div>
                     <p className="text-sm text-white/80 leading-relaxed">{rekomendasi.jadwal_aplikasi}</p>
                  </div>

                  {/* Warning Box */}
                  {(rekomendasi.catatan_penting || rekomendasi.peringatan?.length > 0) && (
                     <div className="p-4 rounded-lg bg-orange-500/10 border border-orange-500/20 text-sm text-orange-400">
                        {rekomendasi.catatan_penting && (
                          <div className="mb-3">
                            <strong className="block mb-1 text-orange-500 font-bold tracking-wider">CATATAN PENTING DR. AGRO:</strong>
                            {rekomendasi.catatan_penting}
                          </div>
                        )}
                        {rekomendasi.peringatan?.map((w: string, i: number) => (
                          <div key={i} className="flex gap-2 text-xs mt-2 p-2 rounded bg-orange-500/10 border border-orange-500/10">
                            <span className="font-bold">PERINGATAN:</span> <span>{w}</span>
                          </div>
                        ))}
                     </div>
                  )}

                  {/* Feedback Section */}
                  <div className="pt-4 border-t border-white/[0.06]">
                     <h3 className="text-sm font-medium text-white mb-3 text-center">FEEDBACK HASIL REKOMENDASI</h3>
                     {feedback.submitted ? (
                       <div className="p-3 bg-green-500/10 border border-green-500/20 rounded-md text-green-400 text-sm text-center font-bold">
                         TERIMA KASIH! Feedback membantu AI semakin akurat.
                       </div>
                     ) : (
                       <div className="flex flex-col sm:flex-row items-center gap-4 bg-black/20 p-4 rounded-lg">
                          <div className="flex gap-2">
                            {[1, 2, 3, 4, 5].map(star => (
                               <button 
                                 key={star} 
                                 onClick={() => setFeedback({...feedback, rating: star})}
                                 className={`w-8 h-8 rounded-md text-xs font-bold transition-all ${star <= feedback.rating ? 'bg-primary text-white border border-primary' : 'bg-white/5 text-white/40 border border-white/10 hover:bg-white/10'}`}
                               >
                                 {star}
                               </button>
                            ))}
                          </div>
                          <div className="flex flex-1 gap-2 w-full">
                             <input 
                               type="text" 
                               value={feedback.catatan}
                               onChange={e => setFeedback({...feedback, catatan: e.target.value})}
                               placeholder="Catatan hasil aplikasi di lapangan... (Opsional)"
                               className="flex-1 rounded-md border border-white/[0.08] bg-black/60 px-3 py-2 text-sm text-white focus:border-primary focus:outline-none"
                             />
                             <Button onClick={submitFeedback} disabled={!feedback.rating} className="bg-primary hover:bg-primary/90 text-white font-medium px-6">
                               Kirim
                             </Button>
                          </div>
                       </div>
                     )}
                  </div>

                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
