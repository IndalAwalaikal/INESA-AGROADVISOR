"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Image from "next/image"
import { Eye, EyeOff } from "lucide-react"

export default function LoginPage() {
  const router = useRouter()
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError("")

    try {
      // In development, the backend runs on port 8001
      const baseUrl = typeof window !== 'undefined' ? `http://${window.location.hostname}:8001` : 'http://localhost:8001';
      
      const res = await fetch(`${baseUrl}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password })
      })

      const data = await res.json()

      if (res.ok && data.sukses) {
        // Set cookie directly from client for simplicity in this single-user dashboard
        document.cookie = `auth_token=${data.token}; path=/; max-age=86400; samesite=strict`
        
        // Wait briefly to ensure cookie is written before redirecting
        setTimeout(() => {
          router.push("/dashboard")
          router.refresh()
        }, 300)
      } else {
        setError(data.detail || data.pesan || "Username atau password salah")
      }
    } catch (err) {
      setError("Gagal terhubung ke server otentikasi.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#0a0f0b] flex items-center justify-center p-4">
      {/* Visual background elements */}
      <div className="absolute inset-0 z-0 flex items-center justify-center overflow-hidden pointer-events-none">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-primary/20 rounded-full blur-[120px] opacity-30 animate-pulse-slow"></div>
        <div className="absolute bottom-0 right-0 w-[400px] h-[400px] bg-secondary/20 rounded-full blur-[100px] opacity-20"></div>
      </div>

      <div className="w-full max-w-md relative z-10">
        <div className="p-8 rounded-2xl bg-[#141b16]/80 backdrop-blur-xl border border-white/[0.08] shadow-2xl">
          <div className="flex flex-col items-center mb-8">
            <div className="h-16 w-16 relative mb-4">
              <Image 
                src="/inesa.png" 
                alt="Logo AgroAdvisor" 
                fill 
                className="object-contain" 
                priority
              />
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-white mb-1">AGROADVISOR</h1>
            <p className="text-sm font-medium text-white/40 uppercase tracking-widest">Akses Manajemen</p>
          </div>

          {error && (
            <div className="mb-6 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm text-center font-medium">
              {error}
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-5">
            <div>
              <label className="text-xs font-bold text-white/50 uppercase tracking-widest block mb-2">Username</label>
              <input
                type="text"
                required
                value={username}
                onChange={e => setUsername(e.target.value)}
                className="w-full rounded-lg border border-white/[0.08] bg-black/40 px-4 py-3 text-sm text-white focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary transition-all placeholder:text-white/20"
                placeholder="Masukkan username"
                autoComplete="username"
              />
            </div>
            
            <div>
              <div className="flex justify-between items-end mb-2">
                <label className="text-xs font-bold text-white/50 uppercase tracking-widest block">Password</label>
              </div>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  required
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  className="w-full rounded-lg border border-white/[0.08] bg-black/40 pl-4 pr-24 py-3 text-sm text-white focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary transition-all placeholder:text-white/20"
                  placeholder="••••••••"
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-white/40 hover:text-white transition-colors"
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full mt-2 rounded-lg bg-primary py-3 px-4 text-sm font-bold text-white transition-all hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:ring-offset-2 focus:ring-offset-[#141b16] disabled:opacity-70 disabled:cursor-not-allowed shadow-[0_0_20px_rgba(74,222,128,0.2)]"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="h-4 w-4 rounded-full border-2 border-white border-t-transparent animate-spin" />
                  MEMVERIFIKASI...
                </span>
              ) : (
                'MASUK DASHBOARD'
              )}
            </button>
            <div className="pt-2">
              <button
                type="button"
                onClick={() => router.push('/')}
                className="w-full rounded-lg bg-transparent border border-white/[0.08] py-3 px-4 text-sm font-bold text-white/50 transition-all hover:bg-white/5 hover:text-white focus:outline-none focus:ring-2 focus:ring-white/20 uppercase tracking-widest"
              >
                KEMBALI KE BERANDA
              </button>
            </div>
          </form>

          <div className="mt-8 text-center border-t border-white/[0.06] pt-6">
            <p className="text-[10px] text-white/30 uppercase tracking-widest">Sistem Keamanan Pribadi AgroAdvisor</p>
          </div>
        </div>
      </div>
    </div>
  )
}
