"use client"

import { useState, useRef, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { postRekomendasiPestisida, getPestisidaPDF, postPestisidaFeedback } from "@/app/utils/api"
import { useWS } from "@/app/context/WebSocketContext"

/* ── Katalog Hama — 3 kategori, foto lokal di public/images/hama/ ── */
const KATALOG_HAMA: Record<string, { nama: string; deskripsi: string; value: string; img: string }[]> = {
  'Hama Serangga': [
    { nama: 'Wereng Coklat', deskripsi: 'Hama utama padi, menyedot cairan batang hingga padi menjadi kuning dan mati', value: 'Wereng coklat', img: '/images/hama/wereng.jpg' },
    { nama: 'Ulat Grayak', deskripsi: 'Ulat berbulu pemakan daun massal, aktif malam hari', value: 'Ulat grayak (Spodoptera)', img: '/images/hama/ulat_grayak.jpg' },
    { nama: 'Penggerek Batang', deskripsi: 'Larva masuk ke dalam batang, tanaman layu mendadak (sundep)', value: 'Penggerek batang padi', img: '/images/hama/penggerek.jpg' },
    { nama: 'Kutu Daun (Aphid)', deskripsi: 'Koloni serangga hijau/hitam di bawah daun muda, daun keriting', value: 'Kutu daun / Aphid', img: '/images/hama/kutu_daun.jpg' },
    { nama: 'Thrips', deskripsi: 'Serangga sangat kecil, daun menggulung berwarna keperakan', value: 'Thrips', img: '/images/hama/thrips.webp' },
    { nama: 'Walang Sangit', deskripsi: 'Kepik berbau menyengat, mengisap bulir padi saat masak susu', value: 'Walang sangit', img: '/images/hama/walang_sangit.jpg' },
    { nama: 'Lalat Buah', deskripsi: 'Bertelur di dalam buah, buah membusuk dari dalam', value: 'Lalat buah', img: '/images/hama/lalat_buah.jpg' },
    { nama: 'Tungau Merah', deskripsi: 'Tungau sangat kecil, daun berbercak putih-kuning lalu rontok', value: 'Tungau merah (Tetranychus)', img: '/images/hama/tungau_merah.jpg' },
  ],
  'Penyakit Tanaman': [
    { nama: 'Blas / Busuk Leher', deskripsi: 'Bercak coklat lonjong pada daun padi, leher malai patah', value: 'Blas padi (Pyricularia)', img: '/images/hama/blas_padi.jpg' },
    { nama: 'Antraknosa / Patek', deskripsi: 'Buah cabai/tomat berbercak hitam lekuk, busuk berair', value: 'Antraknosa (Colletotrichum)', img: '/images/hama/antraknosa.webp' },
    { nama: 'Layu Fusarium', deskripsi: 'Tanaman layu mendadak, batang dalam berwarna coklat', value: 'Layu fusarium', img: '/images/hama/layu_fusarium.jpg' },
    { nama: 'Karat Daun', deskripsi: 'Bercak oranye/coklat seperti karat di bawah daun', value: 'Karat daun (Puccinia)', img: '/images/hama/karat_daun.jpg' },
    { nama: 'Hawar Daun / Kresek', deskripsi: 'Tepi daun padi mengering melebar dari atas', value: 'Hawar daun bakteri / kresek padi', img: '/images/hama/hawar_daun.jpg' },
    { nama: 'Busuk Buah', deskripsi: 'Buah/batang membusuk lunak berair setelah hujan', value: 'Busuk buah (Phytophthora)', img: '/images/hama/busuk_buah.jpg' },
  ],
  'Gulma / Rumput Liar': [
    { nama: 'Alang-alang', deskripsi: 'Rumput tinggi berdaun tajam, berakar dalam, cepat menyebar', value: 'Alang-alang (Imperata cylindrica)', img: '/images/hama/alang_alang.jpg' },
    { nama: 'Rumput Belulang', deskripsi: 'Rumput tipis rendah sangat padat di lahan kering', value: 'Rumput belulang (Eleusine indica)', img: '/images/hama/rumput_belulang.webp' },
    { nama: 'Teki Ladang', deskripsi: 'Mirip rumput tapi berumbi kecil, sangat bandel', value: 'Teki ladang (Cyperus rotundus)', img: '/images/hama/teki_ladang.jpg' },
    { nama: 'Bayam Liar / Duri', deskripsi: 'Gulma berdaun lebar tumbuh tegak dan cepat', value: 'Bayam liar / bayam duri (Amaranthus)', img: '/images/hama/bayam_liar.jpg' },
    { nama: 'Putri Malu', deskripsi: 'Daun menutup jika disentuh, menjalar dengan duri kecil', value: 'Putri malu (Mimosa pudica)', img: '/images/hama/putri_malu.webp' },
    { nama: 'Gulma Sawah', deskripsi: 'Gulma campuran di lahan sawah yang basah/tergenang', value: 'Gulma sawah campuran', img: '/images/hama/gulma_sawah.jpg' },
  ],
}

const TANAMAN_LIST = ['Padi', 'Jagung', 'Cabai', 'Tomat', 'Kedelai', 'Singkong', 'Bawang Merah', 'Kentang', 'Semangka', 'Kangkung']
const TINGKAT = ['ringan', 'sedang', 'berat'] as const

export default function PestisidaPage() {
  const { addAlert } = useWS()
  const [activeKategori, setActiveKategori] = useState('Hama Serangga')
  const [form, setForm] = useState({
    jenis_tanaman: 'Padi',
    jenis_hama: '',
    tingkat_serangan: 'sedang' as string,
    luas_lahan: 1,
    usia_tanaman: '',
    catatan_tambahan: '',
  })

  // Image upload state
  const [imageFile, setImageFile] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const [isIdentifying, setIsIdentifying] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Results
  const [hasil, setHasil] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // Feedback
  const [feedback, setFeedback] = useState({ rating: 5, catatan: '', submitted: false })

  useEffect(() => {
    const savedHasil = localStorage.getItem('last_rekomendasi_pestisida')
    if (savedHasil) try { setHasil(JSON.parse(savedHasil)) } catch (_) {}
    const savedForm = localStorage.getItem('last_form_pestisida')
    if (savedForm) try { setForm(JSON.parse(savedForm)) } catch (_) {}
  }, [])

  useEffect(() => {
    localStorage.setItem('last_form_pestisida', JSON.stringify(form))
  }, [form])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      const file = e.target.files[0]
      setImageFile(file)
      setImagePreview(URL.createObjectURL(file))
    }
  }

  const handleIdentifyImage = async () => {
    if (!imageFile) return
    setIsIdentifying(true)
    try {
      const formData = new FormData()
      formData.append("file", imageFile)
      const baseUrl = typeof window !== 'undefined' ? `http://${window.location.hostname}:8001` : 'http://localhost:8001';
      const response = await fetch(`${baseUrl}/api/pestisida/identifikasi-gambar`, {
        method: "POST", body: formData,
      })
      const data = await response.json()
      if (data.sukses) {
        setForm(f => ({ ...f, jenis_hama: data.nama_hama }))
      } else {
        setError("Gagal menganalisis gambar: " + (data.error || 'Unknown'))
      }
    } catch (err) {
      setError("Terjadi kesalahan jaringan saat analisis gambar.")
    } finally {
      setIsIdentifying(false)
    }
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    if (!form.jenis_tanaman || !form.jenis_hama) {
      setError('Pilih tanaman dan pilih/ketik jenis hama.')
      return
    }
    setLoading(true)
    setError('')
    setHasil(null)
    setFeedback({ rating: 5, catatan: '', submitted: false })
    try {
      const res = await postRekomendasiPestisida({
        ...form,
        gunakan_sensor_live: true,
      })
      setHasil(res.data)
      localStorage.setItem('last_rekomendasi_pestisida', JSON.stringify(res.data))
      addAlert({ level: 'success', pesan: 'Rekomendasi pengendalian hama sukses diberikan.' })
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Gagal mendapatkan rekomendasi.'
      setError(msg)
      addAlert({ level: 'error', pesan: msg })
    } finally {
      setLoading(false)
    }
  }

  async function submitFeedback() {
    if (!hasil) return
    try {
      await postPestisidaFeedback({
        rekomendasi_id: hasil.rekomendasi_id || hasil.id,
        rating: feedback.rating,
        catatan_hasil: feedback.catatan,
      })
      setFeedback(prev => ({ ...prev, submitted: true }))
    } catch (_) {
      addAlert({ level: "error", pesan: "Gagal mengirim feedback" })
    }
  }

  const kategoriKeys = Object.keys(KATALOG_HAMA)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white">Rekomendasi Pestisida & Herbisida</h1>
        <p className="text-white/40 mt-1">
          Pilih jenis hama dari katalog atau upload foto — AI akan memberikan solusi pengendalian
        </p>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1fr_380px]">
        {/* LEFT: Katalog Visual */}
        <div className="space-y-4 min-w-0">
          {/* Kategori Tabs */}
          <div className="flex flex-wrap gap-2">
            {kategoriKeys.map(k => (
              <button
                key={k}
                onClick={() => setActiveKategori(k)}
                className={`px-4 py-2 rounded-lg text-xs font-semibold uppercase tracking-wider transition-all border ${
                  activeKategori === k
                    ? 'bg-primary/15 border-primary/40 text-primary'
                    : 'bg-white/[0.03] border-white/[0.08] text-white/40 hover:text-white/70 hover:border-white/20'
                }`}
              >
                {k}
              </button>
            ))}
          </div>

          {/* Selected pest indicator */}
          {form.jenis_hama && (
            <div className="flex items-center justify-between p-3 rounded-lg bg-primary/10 border border-primary/30">
              <div>
                <span className="text-[10px] text-primary font-mono uppercase tracking-wider">DIPILIH: </span>
                <span className="text-sm font-semibold text-white">{form.jenis_hama}</span>
              </div>
              <button
                onClick={() => setForm(f => ({ ...f, jenis_hama: '' }))}
                className="text-white/40 hover:text-white text-lg leading-none"
              >
                ×
              </button>
            </div>
          )}

          {/* Pest Image Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
            {KATALOG_HAMA[activeKategori].map(hama => {
              const selected = form.jenis_hama === hama.value
              return (
                <div
                  key={hama.nama}
                  onClick={() => setForm(f => ({ ...f, jenis_hama: hama.value }))}
                  className={`cursor-pointer rounded-xl overflow-hidden border-2 transition-all duration-200 hover:scale-[1.02] ${
                    selected
                      ? 'border-primary bg-primary/[0.08] shadow-lg shadow-primary/10'
                      : 'border-white/[0.06] bg-white/[0.03] hover:border-white/20'
                  }`}
                >
                  <div className="w-full h-28 sm:h-32 overflow-hidden bg-white/[0.02] relative">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={hama.img}
                      alt={hama.nama}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        const target = e.target as HTMLImageElement
                        target.style.display = 'none'
                        const fallback = target.nextElementSibling as HTMLElement
                        if (fallback) fallback.style.display = 'flex'
                      }}
                    />
                    <div className="hidden w-full h-full items-center justify-center flex-col gap-1 absolute inset-0 bg-white/[0.02]">
                      <span className="text-[12px] font-bold text-white/50 tracking-widest uppercase">FOTO KATALOG</span>
                    </div>
                  </div>
                  <div className="p-3">
                    <div className={`text-xs font-semibold mb-1 ${selected ? 'text-primary' : 'text-white/80'}`}>
                      {hama.nama}
                    </div>
                    <div className="text-[10px] text-white/40 leading-relaxed line-clamp-2">
                      {hama.deskripsi}
                    </div>
                    {selected && (
                      <div className="mt-2 text-[10px] text-primary font-mono">✓ DIPILIH</div>
                    )}
                  </div>
                </div>
              )
            })}

            {/* Manual input card */}
            <div className="rounded-xl border-2 border-dashed border-white/[0.08] bg-white/[0.02] p-3 flex flex-col justify-center">
              <div className="text-[10px] text-white/40 mb-2">Tidak ada di daftar? Ketik manual:</div>
              <input
                placeholder="Misal: belalang, tikus..."
                value={!KATALOG_HAMA[activeKategori].find(h => h.value === form.jenis_hama) ? (form.jenis_hama || '') : ''}
                onChange={e => setForm(f => ({ ...f, jenis_hama: e.target.value }))}
                className="w-full rounded-md border border-white/[0.08] bg-black/40 px-3 py-2 text-xs text-white focus:border-primary/50 focus:outline-none"
              />
            </div>
          </div>

          {/* Image Upload Section */}
          <Card className="border-white/[0.06] bg-white/[0.03] shadow-none">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold text-white flex items-center gap-2">
                UPLOAD FOTO HAMA (OPSIONAL)
                <span className="text-[10px] text-white/30 font-normal">— AI akan identifikasi otomatis</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col sm:flex-row gap-4 items-start">
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileSelect}
                  accept="image/jpeg, image/png, image/webp"
                  className="hidden"
                />
                <div
                  onClick={() => fileInputRef.current?.click()}
                  className="cursor-pointer flex-shrink-0 w-full sm:w-40 h-28 rounded-lg border-2 border-dashed border-white/[0.1] bg-white/[0.02] flex items-center justify-center overflow-hidden hover:border-primary/30 transition-colors"
                >
                  {imagePreview ? (
                    /* eslint-disable-next-line @next/next/no-img-element */
                    <img src={imagePreview} alt="Preview" className="w-full h-full object-cover rounded-md" />
                  ) : (
                    <div className="text-center">
                      <div className="text-2xl text-white/20 mb-1">+</div>
                      <div className="text-[10px] text-white/30">Klik untuk pilih foto</div>
                    </div>
                  )}
                </div>
                <div className="flex-1 space-y-2">
                  <p className="text-xs text-white/40">
                    Upload foto tanaman yang terserang hama. AI akan mengidentifikasi jenis hama lalu otomatis mengisi pilihan di atas.
                  </p>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={handleIdentifyImage}
                      disabled={!imageFile || isIdentifying}
                      className="border-primary/20 text-primary hover:bg-primary/10 hover:text-primary text-xs h-8"
                    >
                      {isIdentifying ? "Menganalisis..." : "Identifikasi AI"}
                    </Button>
                    {imageFile && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => { setImageFile(null); setImagePreview(null) }}
                        className="border-white/[0.1] text-white/40 hover:bg-white/[0.06] hover:text-white text-xs h-8"
                      >
                        Hapus
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* RIGHT: Form & Submit */}
        <div className="space-y-4">
          <Card className="border-white/[0.06] bg-white/[0.03] shadow-none sticky top-20">
            <CardHeader className="pb-3">
              <div className="text-[10px] text-white/30 font-mono uppercase tracking-widest">DATA PERTANIAN</div>
            </CardHeader>
            <CardContent>
              <form onSubmit={submit} className="space-y-4">
                <div>
                  <label className="text-xs text-white/50 mb-1 block">Jenis Tanaman</label>
                  <select
                    value={form.jenis_tanaman || ''}
                    onChange={e => setForm(f => ({ ...f, jenis_tanaman: e.target.value }))}
                    className="w-full rounded-md border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-white focus:border-primary/50 focus:outline-none"
                  >
                    <option value="">— Pilih tanaman —</option>
                    {TANAMAN_LIST.map(t => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>

                <div>
                  <label className="text-xs text-white/50 mb-1 block">Hama / Penyakit / Gulma</label>
                  <div className="px-3 py-2 rounded-md bg-white/[0.02] border border-white/[0.06] text-sm min-h-[36px] flex items-center">
                    {form.jenis_hama ? (
                      <span className="text-white font-medium">{form.jenis_hama}</span>
                    ) : (
                      <span className="text-white/30">← Pilih dari katalog kiri</span>
                    )}
                  </div>
                </div>

                <div>
                  <label className="text-xs text-white/50 mb-1 block">Tingkat Serangan</label>
                  <div className="flex gap-2">
                    {TINGKAT.map(t => {
                      const active = form.tingkat_serangan === t
                      const colorMap: Record<string, string> = {
                        ringan: 'green',
                        sedang: 'amber',
                        berat: 'red'
                      }
                      const c = colorMap[t]
                      return (
                        <button
                          key={t}
                          type="button"
                          onClick={() => setForm(f => ({ ...f, tingkat_serangan: t }))}
                          className={`flex-1 py-2 rounded-md text-xs font-medium border transition-all ${
                            active
                              ? `bg-${c}-500/15 border-${c}-500/40 text-${c}-400`
                              : 'bg-white/[0.02] border-white/[0.06] text-white/40 hover:text-white/60'
                          }`}
                          style={active ? {
                            backgroundColor: t === 'ringan' ? 'rgba(34,197,94,0.12)' : t === 'sedang' ? 'rgba(245,158,11,0.12)' : 'rgba(239,68,68,0.12)',
                            borderColor: t === 'ringan' ? 'rgba(34,197,94,0.4)' : t === 'sedang' ? 'rgba(245,158,11,0.4)' : 'rgba(239,68,68,0.4)',
                            color: t === 'ringan' ? '#4ade80' : t === 'sedang' ? '#f59e0b' : '#ef4444',
                          } : {}}
                        >
                          {t.charAt(0).toUpperCase() + t.slice(1)}
                        </button>
                      )
                    })}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs text-white/50 mb-1 block">Luas Lahan (Ha)</label>
                    <input
                      type="number"
                      min="0.01"
                      step="0.01"
                      value={form.luas_lahan || ''}
                      onChange={e => setForm(f => ({ ...f, luas_lahan: parseFloat(e.target.value) || 0 }))}
                      className="w-full rounded-md border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-white focus:border-primary/50 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-white/50 mb-1 block flex items-center gap-1">
                      Usia Tanaman 
                      <span className="text-[10px] text-white/30 border border-white/10 px-1.5 rounded-sm bg-white/5">HST / MST</span>
                    </label>
                    <input
                      placeholder="Misal: 45 HST (Hari) atau 6 MST (Minggu)"
                      value={form.usia_tanaman || ''}
                      onChange={e => setForm(f => ({ ...f, usia_tanaman: e.target.value }))}
                      className="w-full rounded-md border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-white focus:border-primary/50 focus:outline-none placeholder:text-white/20"
                    />
                  </div>
                </div>

                <div>
                  <label className="text-xs text-white/50 mb-1 block">Catatan Tambahan (Opsional)</label>
                  <textarea
                    placeholder="Gejala lain yang terlihat..."
                    value={form.catatan_tambahan || ''}
                    onChange={e => setForm(f => ({ ...f, catatan_tambahan: e.target.value }))}
                    rows={2}
                    className="w-full rounded-md border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-white focus:border-primary/50 focus:outline-none resize-y"
                  />
                </div>

                {error && (
                  <div className="p-3 rounded-md bg-red-500/10 border border-red-500/20 text-red-400 text-xs">
                    {error}
                  </div>
                )}

                <Button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-primary text-white hover:bg-primary/90 font-semibold"
                >
                  {loading ? (
                    <span className="flex items-center gap-2">
                      <span className="h-4 w-4 rounded-full border-2 border-white border-t-transparent animate-spin" />
                      AI Menganalisis...
                    </span>
                  ) : (
                    'DAPATKAN REKOMENDASI'
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* ══════ RESULTS ══════ */}
      {loading && (
        <Card className="border-white/[0.06] bg-white/[0.03] shadow-none">
          <CardContent className="py-16 text-center">
            <div className="h-8 w-8 mx-auto rounded-full border-2 border-primary border-t-transparent animate-spin mb-4" />
            <p className="text-primary text-sm font-medium animate-pulse">AI sedang menyusun strategi pengendalian...</p>
          </CardContent>
        </Card>
      )}

      {hasil && !loading && (
        <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
          {/* Identifikasi */}
          <Card className="border-white/[0.06] bg-white/[0.03] shadow-none">
            <CardContent className="pt-6">
              <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-4 mb-4">
                <div>
                  <div className="text-[10px] text-white/30 font-mono uppercase tracking-widest mb-2">IDENTIFIKASI</div>
                  <div className="flex items-center gap-3 flex-wrap">
                    <h3 className="text-lg font-bold text-white">{hasil.identifikasi?.nama_hama || hasil.jenis_hama}</h3>
                    {(hasil.rekomendasi_id || hasil.id) && (
                      <a
                        href={getPestisidaPDF(hasil.rekomendasi_id || hasil.id)}
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-center gap-1 px-3 py-1 rounded-md bg-white/[0.05] border border-white/[0.1] text-xs font-medium text-white/70 hover:bg-white/[0.1] transition-colors"
                      >
                        Unduh PDF
                      </a>
                    )}
                  </div>
                  <div className="text-xs text-white/40 mt-1">{hasil.identifikasi?.jenis_organisme}</div>
                </div>
                <div className="text-right">
                  <span className={`inline-block px-3 py-1 rounded-full text-xs font-bold ${
                    hasil.tingkat_serangan === 'berat' ? 'bg-red-500/15 text-red-400 border border-red-500/30' :
                    hasil.tingkat_serangan === 'sedang' ? 'bg-amber-500/15 text-amber-400 border border-amber-500/30' :
                    'bg-green-500/15 text-green-400 border border-green-500/30'
                  }`}>
                    {(hasil.tingkat_serangan || '').charAt(0).toUpperCase() + (hasil.tingkat_serangan || '').slice(1)}
                  </span>
                  {hasil.identifikasi?.potensi_kerugian && (
                    <div className="text-[10px] text-white/30 mt-2 max-w-[180px]">{hasil.identifikasi.potensi_kerugian}</div>
                  )}
                </div>
              </div>

              {hasil.identifikasi?.deskripsi_gejala && (
                <div className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.06] text-sm text-white/60 mb-4">
                  {hasil.identifikasi.deskripsi_gejala}
                </div>
              )}

              {hasil.strategi_pengendalian && (
                <div className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.06]">
                  <strong className="text-white/80 text-xs">Strategi: </strong>
                  <span className="text-xs text-white/50">{hasil.strategi_pengendalian}</span>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Daftar Pestisida */}
          {hasil.daftar_pestisida && hasil.daftar_pestisida.length > 0 && (
            <Card className="border-white/[0.06] bg-white/[0.03] shadow-none">
              <CardHeader className="pb-3">
                <div className="text-[10px] text-white/30 font-mono uppercase tracking-widest">
                  DAFTAR PESTISIDA — {hasil.jenis_tanaman}
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {hasil.daftar_pestisida.map((p: any, idx: number) => (
                  <div key={idx} className="p-4 rounded-lg bg-white/[0.02] border border-white/[0.06] border-l-2" style={{ borderLeftColor: ['#4ade80', '#f59e0b', '#3b82f6', '#ef4444'][idx % 4] }}>
                    <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-2 mb-3">
                      <div>
                        <span className="text-[10px] text-primary font-mono mr-2">#{p.urutan || idx + 1}</span>
                        <span className="text-sm font-bold text-white">{p.nama_pestisida}</span>
                        <div className="text-[10px] text-white/40 mt-1">{p.bahan_aktif}</div>
                      </div>
                      <span className="px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 text-[10px] border border-blue-500/20 font-medium whitespace-nowrap self-start">
                        {p.jenis_pestisida}
                      </span>
                    </div>
                    <div className="grid grid-cols-3 gap-2 mb-3">
                      {[
                        ['Dosis/Liter', p.dosis_per_liter_air, 'text-green-400'],
                        ['Dosis/Ha', p.dosis_per_ha || p.dosis_total, 'text-green-400'],
                        ['PHI', p.phi, 'text-red-400'],
                      ].map(([label, val, color]) => (
                        <div key={label as string} className="p-2 rounded bg-white/[0.02] border border-white/[0.04]">
                          <div className="text-[9px] text-white/30">{label as string}</div>
                          <div className={`text-xs font-mono ${color}`}>{(val as string) || '—'}</div>
                        </div>
                      ))}
                    </div>
                    <div className="text-[10px] text-white/40">
                      {p.waktu_semprot} {p.interval_semprot && `· ${p.interval_semprot}`}
                    </div>
                    {p.tujuan && <div className="text-[10px] text-white/50 italic mt-1">{p.tujuan}</div>}
                    {p.dosis_total && (
                      <div className="mt-2 px-2 py-1 rounded bg-green-500/10 text-green-400 text-[10px] font-semibold inline-block border border-green-500/20">
                        Total untuk lahan: {p.dosis_total}
                      </div>
                    )}
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {/* Kombinasi */}
          {(hasil.kombinasi_diizinkan?.length > 0 || hasil.kombinasi_dilarang?.length > 0) && (
            <div className="grid gap-4 sm:grid-cols-2">
              {[
                { title: 'BOLEH DICAMPUR', items: hasil.kombinasi_diizinkan, color: 'green' },
                { title: 'DILARANG DICAMPUR', items: hasil.kombinasi_dilarang, color: 'red' },
              ].map(({ title, items, color }) => (
                <Card key={title} className="border-white/[0.06] bg-white/[0.03] shadow-none">
                  <CardContent className="pt-5">
                    <div className={`text-[10px] font-mono uppercase tracking-widest mb-3 ${color === 'green' ? 'text-green-400' : 'text-red-400'}`}>{title}</div>
                    {items && items.length > 0 ? items.map((x: string, i: number) => (
                      <div key={i} className="text-xs text-white/60 py-1 border-b border-white/[0.04] last:border-0">{x}</div>
                    )) : <div className="text-xs text-white/30">—</div>}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {/* Alternatif Organik */}
          {hasil.alternatif_organik?.length > 0 && (
            <Card className="border-white/[0.06] bg-white/[0.03] shadow-none">
              <CardContent className="pt-5">
                <div className="text-[10px] text-green-400 font-mono uppercase tracking-widest mb-3">ALTERNATIF ORGANIK / ALAMI</div>
                <div className="grid gap-3 sm:grid-cols-2">
                  {hasil.alternatif_organik.map((o: any, idx: number) => (
                    <div key={idx} className="p-3 rounded-lg bg-green-500/[0.05] border border-green-500/20">
                      <div className="text-sm font-semibold text-green-400 mb-1">{o.nama}</div>
                      <div className="text-xs text-white/60">{o.cara_pakai}</div>
                      {o.efektivitas && <div className="text-[10px] text-green-400/70 mt-2 italic">Efektivitas: {o.efektivitas}</div>}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Keamanan */}
          <Card className="border-red-500/20 bg-white/[0.03] shadow-none">
            <CardContent className="pt-5">
              <div className="text-[10px] text-red-400 font-mono uppercase tracking-widest mb-3 font-bold">CATATAN KEAMANAN</div>
              {hasil.catatan_keamanan && (
                <p className="text-xs text-white/60 leading-relaxed mb-3">{hasil.catatan_keamanan}</p>
              )}
              {hasil.peringatan?.map((w: string, i: number) => (
                <div key={i} className="mt-2 p-3 rounded-md bg-red-500/10 border border-red-500/20 text-xs text-red-400">{w}</div>
              ))}
            </CardContent>
          </Card>

          {/* Feedback */}
          {(hasil.rekomendasi_id || hasil.id) && (
            <Card className="border-white/[0.06] bg-white/[0.03] shadow-none">
              <CardContent className="pt-5">
                <h3 className="text-sm font-medium text-white mb-3 flex gap-2 items-center tracking-wide">
                  BERI NILAI REKOMENDASI INI
                </h3>
                {feedback.submitted ? (
                  <div className="p-3 bg-green-500/10 border border-green-500/20 rounded-md text-green-400 text-sm text-center font-bold">
                     TERIMA KASIH ATAS FEEDBACK ANDA!
                  </div>
                ) : (
                  <div className="space-y-3">
                    <div className="flex items-center gap-3">
                      <span className="text-xs text-white/50">Rating: </span>
                      <div className="flex gap-2">
                        {[1, 2, 3, 4, 5].map(star => (
                          <button
                            key={star}
                            onClick={() => setFeedback({ ...feedback, rating: star })}
                            className={`w-8 h-8 rounded-md text-xs font-bold transition-all ${star <= feedback.rating ? 'bg-primary text-white border border-primary' : 'bg-white/5 text-white/40 border border-white/10 hover:bg-white/10'}`}
                          >
                            {star}
                          </button>
                        ))}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={feedback.catatan}
                        onChange={e => setFeedback({ ...feedback, catatan: e.target.value })}
                        placeholder="Hasil di lapangan... (Opsional)"
                        className="flex-1 rounded-md border border-white/[0.08] bg-black/40 px-3 py-2 text-sm text-white focus:border-primary/50 focus:outline-none"
                      />
                      <Button onClick={submitFeedback} className="bg-white/10 hover:bg-white/20 text-white border border-white/[0.1]">
                        Kirim
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  )
}
