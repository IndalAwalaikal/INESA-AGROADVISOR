"use client"

import { usePathname, useRouter } from "next/navigation"
import Link from "next/link"
import Image from "next/image"

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
import { Button } from "@/components/ui/button"
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
    <header className="sticky top-0 z-40 flex h-14 items-center gap-4 border-b border-white/[0.06] bg-[#142118] px-4 lg:px-6">
      <div className="flex items-center gap-3">
        <SidebarTrigger className="text-white/50 hover:text-white hover:bg-white/[0.06] font-bold text-xs tracking-widest px-2">
          MENU
        </SidebarTrigger>
        
        <div className="flex lg:hidden items-center gap-2">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg overflow-hidden">
            <Image src="/inesa.png" alt="AgroAdvisor Logo" width={40} height={40} className="h-full w-full object-contain" />
          </div>
          <div className="flex flex-col">
            <span className="text-xs font-bold text-white leading-none">AgroAdvisor</span>
            <span className="text-[10px] text-white/50 uppercase tracking-tighter">Desa Rajang</span>
          </div>
        </div>
      </div>
      
      <div className="flex items-center gap-2">
        <Link href="/">
          <Button variant="ghost" size="sm" className="text-white/50 hover:text-white hover:bg-white/[0.06] h-8 px-3 font-semibold tracking-wide">
            <span className="sm:inline">&larr; Beranda</span>
          </Button>
        </Link>
      </div>

      <div className="ml-auto flex items-center gap-4">
        {connected ? (
          <div className="flex items-center gap-2 rounded-full bg-primary/10 border border-primary/20 px-3 py-1.5">
            <div className="h-2 w-2 rounded-full bg-primary animate-pulse" />
            <span className="text-xs font-medium text-primary">Sistem Aktif</span>
          </div>
        ) : (
          <div className="flex items-center gap-2 rounded-full bg-white/5 border border-white/10 px-3 py-1.5 opacity-50">
            <div className="h-2 w-2 rounded-full bg-white/40" />
            <span className="text-xs font-medium text-white/60">Terputus</span>
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
