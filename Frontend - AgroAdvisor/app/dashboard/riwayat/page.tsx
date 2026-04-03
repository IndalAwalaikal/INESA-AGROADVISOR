"use client"

import { useState, useEffect } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { 
  getRiwayatPupuk, getRiwayatPestisida, getRiwayatPompa, 
  getPupukPDF, getPestisidaPDF, postFeedback, postPestisidaFeedback,
  getExportPupukCSV, getExportPestisidaCSV, getExportPompaCSV
} from "@/app/utils/api"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"

type Category = "pupuk" | "pestisida" | "pompa"

function capitalize(s: string) {
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : ''
}

function formatTanggal(d: string | undefined) {
  if (!d) return '—'
  try { return new Date(d).toLocaleString('id-ID') } catch { return d }
}

export default function RiwayatPage() {
  const [category, setCategory] = useState<Category>("pupuk")
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedDetail, setSelectedDetail] = useState<any>(null)
  const [feedback, setFeedback] = useState({ rating: 5, catatan: '', submitting: false, submitted: false })

  useEffect(() => {
    fetchHistory()
  }, [category])

  useEffect(() => {
    if (selectedDetail) {
      setFeedback({ rating: 5, catatan: '', submitting: false, submitted: false })
    }
  }, [selectedDetail])

  async function fetchHistory() {
    setLoading(true)
    try {
      let res;
      if (category === 'pupuk') res = await getRiwayatPupuk(1, 50)
      else if (category === 'pestisida') res = await getRiwayatPestisida(1, 50)
      else res = await getRiwayatPompa(1, 50)
      setData(res.data.data || [])
    } catch (err) {
      console.error("Gagal mengambil riwayat", err)
    } finally {
      setLoading(false)
    }
  }

  async function handleSubmitFeedback() {
    if (!selectedDetail) return
    setFeedback(f => ({ ...f, submitting: true }))
    try {
      const payload = {
        rekomendasi_id: selectedDetail.id,
        rating: feedback.rating,
        catatan_hasil: feedback.catatan
      }
      if (category === 'pupuk') await postFeedback(payload)
      else await postPestisidaFeedback(payload)
      setFeedback(f => ({ ...f, submitted: true }))
    } catch (err) {
      alert("Gagal mengirim feedback")
    } finally {
      setFeedback(f => ({ ...f, submitting: false }))
    }
  }

  function renderTable() {
    if (loading) return <div className="py-20 text-center animate-pulse text-white/20">Memuat data riwayat...</div>
    if (data.length === 0) return <div className="py-20 text-center text-white/20 italic tracking-wide">Belum ada riwayat tercatat untuk kategori ini.</div>

    if (category === 'pupuk') {
      return (
        <table className="w-full text-left text-sm">
          <thead className="text-[10px] uppercase tracking-widest text-white/30 border-b border-white/[0.04]">
            <tr>
              <th className="px-4 py-3 lg:px-6 lg:py-4">#</th>
              <th className="px-4 py-3 lg:px-6 lg:py-4">Tanaman</th>
              <th className="px-4 py-3 lg:px-6 lg:py-4 hidden sm:table-cell">Ringkasan</th>
              <th className="px-4 py-3 lg:px-6 lg:py-4 hidden md:table-cell">Estimasi</th>
              <th className="px-4 py-3 lg:px-6 lg:py-4">Aksi</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.04]">
            {data.map((item, index) => (
              <tr key={`pupuk-${item.id || index}`} className="text-white/70 hover:bg-white/[0.02] transition-colors">
                <td className="px-4 py-3 lg:px-6 lg:py-4 text-xs font-mono text-white/30">{item.id}</td>
                <td className="px-4 py-3 lg:px-6 lg:py-4 text-xs font-semibold text-primary">{capitalize(item.jenis_tanaman)}</td>
                <td className="px-4 py-3 lg:px-6 lg:py-4 text-xs max-w-[200px] truncate hidden sm:table-cell text-white/50">{item.kondisi_tanah_ringkasan || '-'}</td>
                <td className="px-4 py-3 lg:px-6 lg:py-4 text-xs font-mono text-green-400 hidden md:table-cell">{item.estimasi_peningkatan || '-'}</td>
                <td className="px-4 py-3 lg:px-6 lg:py-4">
                  <Button size="sm" variant="outline" className="h-7 text-[10px] border-white/10 text-white/60 hover:bg-white/10 hover:text-white" onClick={() => setSelectedDetail(item)}>Detail</Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )
    }

    if (category === 'pestisida') {
      return (
        <table className="w-full text-left text-sm">
          <thead className="text-[10px] uppercase tracking-widest text-white/30 border-b border-white/[0.04]">
            <tr>
              <th className="px-4 py-3 lg:px-6 lg:py-4">#</th>
              <th className="px-4 py-3 lg:px-6 lg:py-4">Tanaman</th>
              <th className="px-4 py-3 lg:px-6 lg:py-4">Hama</th>
              <th className="px-4 py-3 lg:px-6 lg:py-4 hidden sm:table-cell">Tingkat</th>
              <th className="px-4 py-3 lg:px-6 lg:py-4 hidden md:table-cell">Efektivitas</th>
              <th className="px-4 py-3 lg:px-6 lg:py-4">Aksi</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.04]">
            {data.map((item, index) => (
              <tr key={`pestisida-${item.id || index}`} className="text-white/70 hover:bg-white/[0.02] transition-colors">
                <td className="px-4 py-3 lg:px-6 lg:py-4 text-xs font-mono text-white/30">{item.id}</td>
                <td className="px-4 py-3 lg:px-6 lg:py-4 text-xs font-semibold text-primary">{capitalize(item.jenis_tanaman)}</td>
                <td className="px-4 py-3 lg:px-6 lg:py-4 text-xs text-amber-500 max-w-[150px] truncate">{item.jenis_hama}</td>
                <td className="px-4 py-3 lg:px-6 lg:py-4 hidden sm:table-cell">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                    item.tingkat_serangan === 'berat' ? 'bg-red-500/10 text-red-400 border-red-500/20' :
                    item.tingkat_serangan === 'sedang' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' :
                    'bg-green-500/10 text-green-400 border-green-500/20'
                  }`}>
                    {item.tingkat_serangan}
                  </span>
                </td>
                <td className="px-4 py-3 lg:px-6 lg:py-4 text-xs font-mono text-cyan-400 hidden md:table-cell">{item.estimasi_efektivitas || '-'}</td>
                <td className="px-4 py-3 lg:px-6 lg:py-4">
                  <Button size="sm" variant="outline" className="h-7 text-[10px] border-white/10 text-white/60 hover:bg-white/10 hover:text-white" onClick={() => setSelectedDetail(item)}>Detail</Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )
    }

    if (category === 'pompa') {
      return (
        <table className="w-full text-left text-sm">
          <thead className="text-[10px] uppercase tracking-widest text-white/30 border-b border-white/[0.04]">
            <tr>
              <th className="px-4 py-3 lg:px-6 lg:py-4">Status</th>
              <th className="px-4 py-3 lg:px-6 lg:py-4">Trigger</th>
              <th className="px-4 py-3 lg:px-6 lg:py-4 hidden sm:table-cell">Alasan</th>
              <th className="px-4 py-3 lg:px-6 lg:py-4 hidden md:table-cell">Durasi</th>
              <th className="px-4 py-3 lg:px-6 lg:py-4">Waktu</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.04]">
            {data.map((item, idx) => (
              <tr key={item.id || idx} className="text-white/70 hover:bg-white/[0.02] transition-colors">
                <td className="px-4 py-3 lg:px-6 lg:py-4">
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                    (item.aksi === 'on' || item.status?.includes('nyala')) ? 'bg-primary/10 text-primary border border-primary/20' : 'bg-white/5 text-white/40 border border-white/10'
                  }`}>
                    {item.aksi?.toUpperCase() || item.status || '-'}
                  </span>
                </td>
                <td className="px-4 py-3 lg:px-6 lg:py-4 text-xs font-mono">{item.trigger_by || item.trigger_oleh || '-'}</td>
                <td className="px-4 py-3 lg:px-6 lg:py-4 text-xs max-w-[200px] truncate hidden sm:table-cell text-white/50">{item.alasan || '-'}</td>
                <td className="px-4 py-3 lg:px-6 lg:py-4 text-xs font-mono text-blue-400 hidden md:table-cell">
                  {item.durasi_detik ? `${item.durasi_detik}s` : item.durasi_menit ? `${item.durasi_menit} mnt` : '-'}
                </td>
                <td className="px-4 py-3 lg:px-6 lg:py-4 text-xs text-white/40">
                  {formatTanggal(item.timestamp || item.dicatat_pada)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Riwayat & Histori</h1>
          <p className="text-white/40 mt-1 text-sm">Semua data tersimpan sebagai bahan pembelajaran AI</p>
        </div>
        <Button 
          onClick={() => {
            const url = category === 'pupuk' ? getExportPupukCSV() : 
                        category === 'pestisida' ? getExportPestisidaCSV() : 
                        getExportPompaCSV();
            window.open(url, '_blank');
          }}
          className="bg-white/10 text-white hover:bg-white/20 border border-white/20"
        >
          ↓ Ekspor CSV
        </Button>
      </div>

      <div className="flex gap-1 p-1 bg-white/[0.02] border border-white/[0.06] rounded-xl w-fit">
        {(['pupuk', 'pestisida', 'pompa'] as Category[]).map((cat) => (
          <button
            key={cat}
            onClick={() => setCategory(cat)}
            className={`px-5 py-2 rounded-lg text-xs font-bold uppercase tracking-widest transition-all ${
              category === cat
                ? 'bg-primary text-white shadow-lg shadow-primary/20'
                : 'text-white/30 hover:text-white/60'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      <Card className="border-white/[0.06] bg-white/[0.03] shadow-none overflow-hidden">
        <div className="p-0">
          <div className="overflow-x-auto">
            {renderTable()}
          </div>
        </div>
      </Card>

      {/* ══════ Detail Modal ══════ */}
      <Dialog open={!!selectedDetail} onOpenChange={() => setSelectedDetail(null)}>
        <DialogContent className="bg-[#0a0f0b] border-white/[0.08] text-white max-w-3xl max-h-[85vh] overflow-y-auto custom-scrollbar">
          <DialogHeader>
            <DialogTitle className="text-primary flex items-center gap-2">
              Detail Rekomendasi AI
            </DialogTitle>
            <div className="text-xs text-white/40 flex items-center gap-3 flex-wrap">
              <span>{capitalize(selectedDetail?.jenis_tanaman || '')} · {formatTanggal(selectedDetail?.dibuat_pada || selectedDetail?.timestamp)}</span>
              {category !== 'pompa' && selectedDetail && (
                <a
                  href={category === 'pupuk' ? getPupukPDF(selectedDetail.id) : getPestisidaPDF(selectedDetail.id)}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-1 px-2 py-0.5 rounded bg-white/[0.05] border border-white/[0.1] text-[10px] font-medium text-white/60 hover:bg-white/[0.1] transition-colors"
                >
                  UNDUH PDF
                </a>
              )}
            </div>
          </DialogHeader>

          <div className="mt-4 space-y-5">
            {/* Summary Cards */}
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.04]">
                <div className="text-[10px] text-white/30 uppercase mb-1">Kondisi Tanah</div>
                <div className="text-sm text-white/80 leading-relaxed">{selectedDetail?.kondisi_tanah_ringkasan || selectedDetail?.rekomendasi_json?.kondisi_ringkasan || '-'}</div>
              </div>
              <div className="p-3 rounded-lg bg-primary/10 border border-primary/20">
                <div className="text-[10px] text-primary/60 uppercase mb-1">Estimasi Hasil</div>
                <div className="text-lg font-bold text-primary">{selectedDetail?.estimasi_peningkatan || selectedDetail?.estimasi_efektivitas || '-'}</div>
              </div>
            </div>

            {/* Pupuk Detail */}
            {selectedDetail?.rekomendasi_json?.daftar_pupuk && (
              <div>
                <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                  <div className="h-1.5 w-1.5 rounded-full bg-green-400" />
                  Rencana Pemupukan
                </h3>
                <div className="space-y-3">
                  {selectedDetail.rekomendasi_json.daftar_pupuk.map((p: any, idx: number) => (
                    <div key={idx} className="p-4 rounded-lg bg-white/[0.02] border border-white/[0.06] border-l-2 border-l-green-400">
                      <div className="font-semibold text-white text-sm mb-1">{p.nama_pupuk}</div>
                      <div className="text-[11px] text-white/40 mb-3">{p.bahan_aktif}</div>
                      <div className="flex flex-wrap gap-4 text-xs">
                        <div><span className="text-white/40">Takaran:</span> <strong className="text-white">{p.takaran_total}</strong></div>
                        <div><span className="text-white/40">Waktu:</span> <strong className="text-white">{p.waktu_aplikasi}</strong></div>
                      </div>
                      {p.alasan_penggunaan && <div className="mt-2 text-[10px] text-white/40 italic">{p.alasan_penggunaan}</div>}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Pestisida Detail */}
            {selectedDetail?.rekomendasi_json?.daftar_pestisida && (
              <div>
                <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                  <div className="h-1.5 w-1.5 rounded-full bg-red-400" />
                  Rencana Pengendalian Hama
                </h3>
                <div className="space-y-3">
                  {selectedDetail.rekomendasi_json.daftar_pestisida.map((p: any, idx: number) => (
                    <div key={idx} className="p-4 rounded-lg bg-white/[0.02] border border-white/[0.06] border-l-2 border-l-red-400">
                      <div className="font-semibold text-white text-sm mb-1">{p.nama_pestisida}</div>
                      <div className="text-[11px] text-white/40 mb-3">{p.bahan_aktif} ({p.jenis_pestisida})</div>
                      <div className="flex flex-wrap gap-4 text-xs">
                        <div><span className="text-white/40">Dosis:</span> <strong className="text-white">{p.dosis_per_liter_air}</strong></div>
                        <div><span className="text-white/40">Interval:</span> <strong className="text-white">{p.interval_semprot}</strong></div>
                        <div><span className="text-white/40">PHI:</span> <strong className="text-red-400">{p.phi}</strong></div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Catatan penting */}
            {(selectedDetail?.rekomendasi_json?.catatan_penting || selectedDetail?.rekomendasi_json?.jadwal_pengendalian) && (
              <div className="p-4 rounded-lg bg-white/[0.02] border border-white/[0.06]">
                <div className="text-xs text-white/60 leading-relaxed">
                  <strong className="text-white/80">Catatan Dr. Agro:</strong><br/>
                  {selectedDetail.rekomendasi_json.catatan_penting || selectedDetail.rekomendasi_json.jadwal_pengendalian}
                </div>
              </div>
            )}

            {/* Feedback Section */}
            {category !== 'pompa' && (
              <div className="pt-4 border-t border-white/[0.06]">
                <h3 className="text-sm font-medium text-white mb-3 flex items-center gap-2">
                  BERIKAN FEEDBACK HASIL
                </h3>
                {feedback.submitted ? (
                  <div className="p-3 bg-green-500/10 border border-green-500/20 rounded-md text-green-400 text-sm text-center font-bold">
                    TERIMA KASIH! Feedback Anda telah tersimpan.
                  </div>
                ) : (
                  <div className="space-y-3">
                    <div className="flex items-center gap-3">
                      <span className="text-xs text-white/50">Rating hasil:</span>
                      <div className="flex gap-2">
                        {[1, 2, 3, 4, 5].map(r => (
                          <button
                            key={r}
                            onClick={() => setFeedback(f => ({ ...f, rating: r }))}
                            className={`w-8 h-8 rounded-md text-xs font-bold transition-all ${feedback.rating >= r ? 'bg-primary text-white border border-primary' : 'bg-white/5 text-white/40 border border-white/10 hover:bg-white/10'}`}
                          >
                            {r}
                          </button>
                        ))}
                      </div>
                    </div>
                    <textarea
                      placeholder="Bagaimana hasil di lapangan? (Opsional)"
                      value={feedback.catatan}
                      onChange={e => setFeedback(f => ({ ...f, catatan: e.target.value }))}
                      rows={2}
                      className="w-full rounded-md border border-white/[0.08] bg-black/40 px-3 py-2 text-sm text-white focus:border-primary/50 focus:outline-none resize-y"
                    />
                    <div className="flex justify-end">
                      <Button
                        onClick={handleSubmitFeedback}
                        disabled={feedback.submitting}
                        className="bg-primary text-white hover:bg-primary/90 text-xs px-4"
                      >
                        {feedback.submitting ? 'Mengirim...' : 'Simpan Feedback'}
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            )}

            <div className="flex justify-end pt-2">
              <Button variant="outline" className="border-white/10 text-white/60 hover:bg-white/10 hover:text-white" onClick={() => setSelectedDetail(null)}>
                TUTUP
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
