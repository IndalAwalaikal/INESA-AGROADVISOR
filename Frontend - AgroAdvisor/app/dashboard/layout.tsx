"use client"

import { usePathname, useRouter } from "next/navigation"
import Link from "next/link"
import Image from "next/image"
import { ArrowLeft } from "lucide-react"

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarTrigger,
  SidebarSeparator,
} from "@/components/ui/sidebar"
import { WebSocketProvider } from "@/app/context/WebSocketContext"
import AlertBar from "@/components/AlertBar"
import { useWS } from "@/app/context/WebSocketContext"

const menuItems = [
  {
    title: "Dashboard",
    href: "/dashboard",
  },
  {
    title: "Pupuk",
    href: "/dashboard/pupuk",
  },
  {
    title: "Pestisida",
    href: "/dashboard/pestisida",
  },
  {
    title: "Pompa Air",
    href: "/dashboard/pompa",
  },
  {
    title: "Riwayat",
    href: "/dashboard/riwayat",
  },
]

function TopHeader() {
  const { connected } = useWS();
  
  return (
    <header className="sticky top-0 z-40 flex h-14 items-center justify-between border-b border-white/[0.06] bg-[#142118] px-4 lg:px-6">
      {/* Kiri: Menu & Logo Mobile */}
      <div className="flex items-center gap-3">
        <SidebarTrigger className="text-white/50 hover:text-white hover:bg-white/[0.06] font-bold text-xs tracking-widest px-2">
          MENU
        </SidebarTrigger>
        
        <div className="flex lg:hidden items-center gap-2">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg overflow-hidden">
            <Image src="/inesa.png" alt="AgroAdvisor Logo" width={32} height={32} className="h-full w-full object-contain" />
          </div>
          <div className="hidden sm:flex flex-col">
            <span className="text-xs font-bold text-white leading-none">AgroAdvisor</span>
            <span className="text-[10px] text-white/50 uppercase tracking-tighter mt-0.5">Desa Rajang</span>
          </div>
        </div>
      </div>
      
      {/* Kanan: Status Koneksi */}
      <div className="flex items-center">
        {connected ? (
          <div className="flex items-center gap-2 rounded-full bg-primary/10 border border-primary/20 px-2.5 sm:px-3 py-1.5" title="Sistem Aktif">
            <div className="h-2 w-2 rounded-full bg-primary animate-pulse shrink-0" />
            <span className="hidden sm:inline text-xs font-medium text-primary whitespace-nowrap">Sistem Aktif</span>
          </div>
        ) : (
          <div className="flex items-center gap-2 rounded-full bg-white/5 border border-white/10 px-2.5 sm:px-3 py-1.5 opacity-50" title="Terputus">
            <div className="h-2 w-2 rounded-full bg-white/40 shrink-0" />
            <span className="hidden sm:inline text-xs font-medium text-white/60 whitespace-nowrap">Terputus</span>
          </div>
        )}
      </div>
    </header>
  )
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const pathname = usePathname()
  const router = useRouter()

  function handleLogout() {
    // Clear the auth cookie by expiring it
    document.cookie = 'auth_token=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT;';
    router.push('/')
    router.refresh()
  }

  return (
    <WebSocketProvider>
      <SidebarProvider defaultOpen={true}>
        <Sidebar collapsible="icon" className="border-r border-white/[0.1]" style={{ background: "linear-gradient(180deg, #142118 0%, #111c14 100%)" }}>
          <SidebarHeader className="p-4 group-data-[collapsible=icon]:p-2" style={{ background: "transparent" }}>
            <Link href="/" className="flex items-center gap-3 group-data-[collapsible=icon]:justify-center flex-1">
              <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-lg overflow-hidden group-data-[collapsible=icon]:w-8 group-data-[collapsible=icon]:h-8 transition-all">
                <Image src="/inesa.png" alt="AgroAdvisor Logo" width={56} height={56} className="h-full w-full object-contain" />
              </div>
              <div className="flex flex-col group-data-[collapsible=icon]:hidden">
                <span className="text-sm font-semibold text-white">AgroAdvisor</span>
                <span className="text-xs text-white/50">Desa Rajang</span>
              </div>
            </Link>
          </SidebarHeader>

          <SidebarSeparator className="bg-white/[0.2] ml-0 mr-4 h-[4px] group-data-[collapsible=icon]:hidden" />

          <SidebarContent className="p-2 group-data-[collapsible=icon]:p-1.5" style={{ background: "transparent" }}>
            {/* Tombol Kembali ke Beranda */}
            <div className="px-2 mb-2">
              <Link
                href="/"
                className="group/back flex items-center gap-2.5 rounded-xl bg-gradient-to-r from-primary/15 to-primary/5 px-3 py-2 text-[13px] font-medium text-primary/90 transition-all duration-300 hover:from-primary/25 hover:to-primary/10 hover:text-primary hover:shadow-[0_0_16px_rgba(34,197,94,0.1)] active:scale-[0.97] group-data-[collapsible=icon]:justify-center group-data-[collapsible=icon]:px-2 group-data-[collapsible=icon]:py-2"
              >
                <ArrowLeft className="h-4 w-4 shrink-0 transition-transform duration-300 group-hover/back:-translate-x-0.5" />
                <span className="group-data-[collapsible=icon]:hidden">Kembali ke Beranda</span>
              </Link>
            </div>

            <SidebarGroup>
              <SidebarGroupLabel className="text-white/40 text-xs uppercase tracking-wider px-3 font-medium">
                Menu Utama
              </SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  {menuItems.map((item) => {
                    const isActive = pathname === item.href
                    return (
                      <SidebarMenuItem key={item.href}>
                        <SidebarMenuButton
                          asChild
                          isActive={isActive}
                          tooltip={item.title}
                          className={`transition-all duration-200 ${
                            isActive
                              ? "bg-primary text-white hover:bg-primary/90 shadow-md shadow-primary/20"
                              : "text-white/60 hover:bg-white/[0.08] hover:text-white"
                          }`}
                        >
                          <Link href={item.href} className="flex items-center">
                            {isActive ? (
                              <span className="w-1.5 h-1.5 rounded-full bg-white mr-3 opacity-100 transition-all duration-300" />
                            ) : (
                              <span className="w-1.5 h-1.5 rounded-full bg-white mr-3 opacity-0 transition-all duration-300" />
                            )}
                            <span className="font-semibold tracking-wide">{item.title}</span>
                          </Link>
                        </SidebarMenuButton>
                      </SidebarMenuItem>
                    )
                  })}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>
          </SidebarContent>

          <SidebarFooter className="p-4 group-data-[collapsible=icon]:p-2 relative" style={{ background: "transparent" }}>
            <SidebarSeparator className="bg-white/[0.2] h-[2px] mb-4 group-data-[collapsible=icon]:hidden" />
            <div className="flex items-center gap-3 group-data-[collapsible=icon]:justify-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/15 border border-primary/20">
                  <span className="text-xs font-medium text-primary">AR</span>
                </div>
                <div className="flex flex-col group-data-[collapsible=icon]:hidden">
                  <span className="text-sm font-medium text-white">Admin Rajang</span>
                  <span className="text-xs text-white/50">Operator</span>
                </div>
              </div>
              
              <button 
                onClick={handleLogout}
                className="group-data-[collapsible=icon]:hidden text-[10px] text-red-500 font-bold tracking-widest px-2 py-1 rounded bg-red-500/10 border border-red-500/20 hover:bg-red-500/20 transition-colors"
                title="Keluar / Logout"
              >
                KELUAR
              </button>
            </div>
          </SidebarFooter>
        </Sidebar>

        <main className="flex-1" style={{ background: "#131618" }}>
          <TopHeader />
          {/* Main Content */}
          <div className="p-4 lg:p-6 relative">
            {children}
            <AlertBar />
          </div>
        </main>
      </SidebarProvider>
    </WebSocketProvider>
  )
}
