"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import Image from "next/image";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

const navItems = [
  { name: "Profile", href: "#profile" },
  { name: "About", href: "#tentang" },
  { name: "Features", href: "#fitur" },
  { name: "Mechanism", href: "#mekanisme" },
  { name: "Contact", href: "#kontak" },
];

export default function LandingPage() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);
  const [activeSection, setActiveSection] = useState("");

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // IntersectionObserver for active section tracking
  useEffect(() => {
    const sectionIds = navItems.map((item) => item.href.replace("#", ""));
    const observers: IntersectionObserver[] = [];

    sectionIds.forEach((id) => {
      const element = document.getElementById(id);
      if (element) {
        const observer = new IntersectionObserver(
          (entries) => {
            entries.forEach((entry) => {
              if (entry.isIntersecting) {
                setActiveSection(`#${id}`);
              }
            });
          },
          { rootMargin: "-30% 0px -60% 0px", threshold: 0 },
        );
        observer.observe(element);
        observers.push(observer);
      }
    });

    return () => {
      observers.forEach((observer) => observer.disconnect());
    };
  }, []);

  const handleNavClick = useCallback(
    (e: React.MouseEvent<HTMLAnchorElement>, href: string) => {
      e.preventDefault();
      const targetId = href.replace("#", "");
      const element = document.getElementById(targetId);
      if (element) {
        element.scrollIntoView({ behavior: "smooth", block: "start" });
      }
      setIsMenuOpen(false);
    },
    [],
  );

  return (
    <div
      className="min-h-screen bg-fixed bg-cover bg-center"
      style={{ backgroundImage: "url('/images/farm-bg.jpg')" }}
    >
      {/* Overlay */}
      <div className="min-h-screen bg-neutral-900/80">
        {/* Navbar */}
        <header
          className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
            isScrolled
              ? "bg-neutral-800/95 backdrop-blur-md shadow-lg"
              : "bg-neutral-700/60 backdrop-blur-sm"
          }`}
        >
          <nav className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="flex h-16 items-center justify-between">
              {/* Logo */}
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 sm:h-14 sm:w-14 shrink-0 items-center justify-center rounded-lg overflow-hidden">
                  <Image
                    src="/inesa.png"
                    alt="AgroAdvisor Logo"
                    width={56}
                    height={56}
                    className="h-full w-full object-contain"
                  />
                </div>
                <div className="flex flex-col">
                  <span className="text-base font-bold text-white">
                    AgroAdvisor
                  </span>
                  <span className="text-[10px] sm:text-xs text-white/60 -mt-1 sm:mt-0">
                    Desa Rajang
                  </span>
                </div>
              </div>

              {/* Desktop Navigation */}
              <div className="hidden lg:flex lg:items-center lg:gap-1">
                {navItems.map((item) => (
                  <a
                    key={item.name}
                    href={item.href}
                    onClick={(e) => handleNavClick(e, item.href)}
                    className={`relative px-4 py-2 text-sm font-medium transition-all duration-300 rounded-lg ${
                      activeSection === item.href
                        ? "text-white bg-white/10"
                        : "text-white/70 hover:text-white hover:bg-white/10"
                    }`}
                  >
                    {item.name}
                    {activeSection === item.href && (
                      <span className="absolute bottom-0 left-1/2 -translate-x-1/2 w-6 h-0.5 bg-primary rounded-full" />
                    )}
                  </a>
                ))}
                <Link href="/dashboard" className="ml-4">
                  <Button className="bg-primary text-white hover:bg-primary/90 font-bold px-6 shadow-lg">
                    Dashboard
                  </Button>
                </Link>
              </div>

              {/* Mobile Menu Button */}
              <div className="flex lg:hidden">
                <button
                  onClick={() => setIsMenuOpen(!isMenuOpen)}
                  className="inline-flex items-center justify-center rounded-lg px-3 py-2 text-xs font-bold tracking-widest text-white hover:bg-white/10 transition-colors"
                >
                  {isMenuOpen ? "TUTUP" : "MENU"}
                </button>
              </div>
            </div>

            {/* Mobile Navigation */}
            {isMenuOpen && (
              <div className="lg:hidden pb-4">
                <div className="space-y-1 rounded-xl bg-neutral-800/90 backdrop-blur-sm p-3">
                  {navItems.map((item) => (
                    <a
                      key={item.name}
                      href={item.href}
                      className={`block rounded-lg px-4 py-3 text-sm font-medium transition-colors ${
                        activeSection === item.href
                          ? "bg-primary/20 text-primary border-l-2 border-primary"
                          : "text-white/70 hover:bg-white/10 hover:text-white"
                      }`}
                      onClick={(e) => handleNavClick(e, item.href)}
                    >
                      {item.name}
                    </a>
                  ))}
                  <Link href="/dashboard" className="block pt-2">
                    <Button className="w-full bg-primary text-white hover:bg-primary/90 font-bold">
                      Dashboard
                    </Button>
                  </Link>
                </div>
              </div>
            )}
          </nav>
        </header>

        {/* Hero Section - Centered */}
        <section className="relative flex items-center justify-center min-h-screen pt-16">
          <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 text-center">
            <div className="inline-flex items-center rounded-full bg-primary/20 border border-primary/40 px-5 py-2 text-sm font-medium text-primary mb-8">
              Sistem Berbasis IoT & AI
            </div>
            <h1 className="text-4xl font-bold tracking-tight text-white sm:text-5xl lg:text-6xl xl:text-7xl text-balance leading-tight">
              Pertanian Cerdas untuk
              <span className="text-primary block mt-2">Desa Rajang</span>
            </h1>
            <p className="mt-8 text-lg sm:text-xl text-white/60 leading-relaxed max-w-2xl mx-auto">
              AgroAdvisor merupakan sistem rekomendasi dan monitoring pertanian berbasis IoT yang membantu petani mengelola pupuk, pestisida, dan irigasi secara optimal berdasarkan data kondisi lingkungan secara real-time di Jl. Mongsidi No.17, Desa Rajang, Kec. Lembang, Kabupaten Pinrang, Sulawesi Selatan, Indonesia.
            </p>
            <div className="mt-12 flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/dashboard">
                <Button
                  size="lg"
                  className="bg-primary hover:bg-primary/90 text-white text-lg font-bold px-12 h-16 w-full sm:w-auto shadow-2xl shadow-primary/30 group"
                >
                  Masuk Dashboard
                  <span className="ml-3 text-xl transition-transform group-hover:translate-x-1">&rarr;</span>
                </Button>
              </Link>
              <a href="#tentang" onClick={(e) => handleNavClick(e, "#tentang")}>
                <Button
                  variant="outline"
                  size="lg"
                  className="bg-transparent border-2 border-white/30 text-white hover:bg-white/10 hover:border-white/50 text-lg px-10 h-16 w-full sm:w-auto"
                >
                  Pelajari Lebih Lanjut
                </Button>
              </a>
            </div>
          </div>
        </section>

        {/* Profile Desa Section */}
        <section
          id="profile"
          className="py-20 sm:py-24 bg-neutral-800/60 backdrop-blur-sm"
        >
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="grid gap-12 lg:grid-cols-2 lg:items-center">
              <div>
                <span className="text-sm font-semibold text-primary uppercase tracking-wider">
                  Tentang Kami
                </span>
                <h2 className="mt-3 text-3xl font-bold tracking-tight text-white sm:text-4xl">
                  Profile Desa Rajang
                </h2>
                <p className="mt-6 text-lg text-white/60 leading-relaxed text-justify">
                  Desa Rajang merupakan salah satu desa yang berada di wilayah Kecamatan Lembang, Kabupaten Pinrang, dengan kondisi wilayah yang didominasi oleh lahan pertanian dan perkebunan. Sebagian besar masyarakat desa bermata pencaharian sebagai petani, sehingga sektor pertanian menjadi potensi utama dalam menunjang perekonomian masyarakat. Komoditas yang banyak dibudidayakan antara lain jagung serta beberapa tanaman hortikultura yang memanfaatkan kondisi tanah yang subur dan iklim yang mendukung. Dengan potensi sumber daya alam yang dimiliki, sektor pertanian di Desa Rajang terus dikembangkan sebagai pilar utama dalam meningkatkan kesejahteraan masyarakat dan pembangunan desa.
                </p>
                <div className="mt-8 space-y-4">
                  {[
                    {
                      title: "Lokasi Strategis",
                      text: "Akses irigasi yang baik dan tanah subur",
                    },
                    {
                      title: "Produktivitas Tinggi",
                      text: "Lahan pertanian produktif sepanjang tahun",
                    },
                    {
                      title: "Berkelanjutan",
                      text: "Komitmen pada pertanian ramah lingkungan",
                    },
                  ].map((item, index) => (
                    <div
                      key={index}
                      className="flex items-start gap-4 p-4 rounded-xl bg-white/5 border border-white/10"
                    >
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary text-white text-sm font-bold">
                        {index + 1}
                      </div>
                      <div>
                        <h4 className="font-semibold text-white">
                          {item.title}
                        </h4>
                        <span className="text-sm text-white/50">
                          {item.text}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="relative">
                <div className="aspect-[4/3] overflow-hidden rounded-2xl border border-white/10 shadow-2xl">
                  <Image
                    src="/images/desa-rajang.png"
                    alt="Pemandangan Desa Rajang - sawah dan perkampungan tradisional"
                    width={800}
                    height={600}
                    className="h-full w-full object-cover"
                    priority
                  />
                </div>
                {/* Floating label */}
                <div className="absolute bottom-4 left-4 right-4 rounded-xl bg-black/60 backdrop-blur-md px-4 py-3 border border-white/10">
                  <p className="text-sm font-medium text-white">
                    📍 Desa Rajang, Kecematan Lembang, Pinrang
                  </p>
                  <p className="text-xs text-white/50">
                    Kawasan pertanian produktif sepanjang tahun
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Tentang AgroAdvisor Section */}
        <section id="tentang" className="py-20 sm:py-24">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="mx-auto max-w-3xl text-center">
              <span className="text-sm font-semibold text-primary uppercase tracking-wider">
                Teknologi Kami
              </span>
              <h2 className="mt-3 text-3xl font-bold tracking-tight text-white sm:text-4xl">
                Tentang AgroAdvisor
              </h2>
              <p className="mt-6 text-lg text-white/60 leading-relaxed">
                Platform terintegrasi yang menggabungkan teknologi IoT dan
                kecerdasan buatan untuk memberikan rekomendasi pertanian yang
                akurat dan real-time.
              </p>
            </div>

            <div className="mt-12 grid gap-6 md:grid-cols-2">
              <Card className="border-white/10 bg-white/5 backdrop-blur-sm">
                <CardContent className="p-8">
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary text-white text-xl font-bold">
                    1
                  </div>
                  <h3 className="mt-6 text-xl font-bold text-white">
                    Teknologi IoT Terintegrasi
                  </h3>
                  <p className="mt-4 text-white/50 leading-relaxed">
                    Sensor-sensor canggih yang terpasang di lapangan
                    mengumpulkan data secara real-time tentang kondisi tanah,
                    kelembaban, dan parameter lingkungan lainnya untuk analisis
                    yang akurat.
                  </p>
                </CardContent>
              </Card>

              <Card className="border-white/10 bg-white/5 backdrop-blur-sm">
                <CardContent className="p-8">
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary text-white text-xl font-bold">
                    2
                  </div>
                  <h3 className="mt-6 text-xl font-bold text-white">
                    Analisis AI Cerdas
                  </h3>
                  <p className="mt-4 text-white/50 leading-relaxed">
                    Algoritma machine learning menganalisis data yang
                    dikumpulkan untuk memberikan rekomendasi yang disesuaikan
                    dengan kondisi spesifik lahan pertanian Anda.
                  </p>
                </CardContent>
              </Card>
            </div>
          </div>
        </section>

        {/* Fitur Section */}
        <section
          id="fitur"
          className="py-20 sm:py-24 bg-neutral-800/60 backdrop-blur-sm"
        >
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="mx-auto max-w-3xl text-center">
              <span className="text-sm font-semibold text-primary uppercase tracking-wider">
                Fitur Unggulan
              </span>
              <h2 className="mt-3 text-3xl font-bold tracking-tight text-white sm:text-4xl">
                Fitur AgroAdvisor
              </h2>
              <p className="mt-6 text-lg text-white/60">
                Solusi lengkap untuk kebutuhan pertanian modern Desa Rajang
              </p>
            </div>

            <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
              {[
                {
                  title: "Rekomendasi Pupuk",
                  description:
                    "Dapatkan rekomendasi jenis dan takaran pupuk yang optimal berdasarkan kondisi tanah.",
                },
                {
                  title: "Rekomendasi Pestisida",
                  description:
                    "Identifikasi hama dan dapatkan rekomendasi pestisida yang tepat dan ramah lingkungan.",
                },
                {
                  title: "Monitoring Pompa",
                  description:
                    "Kontrol dan pantau sistem irigasi secara manual atau otomatis dari mana saja.",
                },
                {
                  title: "Riwayat & Analitik",
                  description:
                    "Lacak semua aktivitas dan analisis tren untuk pengambilan keputusan yang lebih baik.",
                },
              ].map((feature, index) => (
                <Card
                  key={index}
                  className="border-white/10 bg-white/5 backdrop-blur-sm hover:bg-white/10 transition-colors"
                >
                  <CardContent className="p-6">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-white font-bold">
                      {index + 1}
                    </div>
                    <h3 className="mt-4 text-lg font-bold text-white">
                      {feature.title}
                    </h3>
                    <p className="mt-2 text-sm text-white/50 leading-relaxed">
                      {feature.description}
                    </p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* Mekanisme Section */}
        <section id="mekanisme" className="py-20 sm:py-24">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="mx-auto max-w-3xl text-center">
              <span className="text-sm font-semibold text-primary uppercase tracking-wider">
                Cara Kerja
              </span>
              <h2 className="mt-3 text-3xl font-bold tracking-tight text-white sm:text-4xl">
                Mekanisme Penggunaan Alat
              </h2>
              <p className="mt-6 text-lg text-white/60">
                Langkah-langkah mudah untuk memulai menggunakan sistem
                AgroAdvisor
              </p>
            </div>

            <div className="mt-16 relative">
              {/* Connection Line */}
              <div className="absolute top-20 left-0 right-0 h-0.5 bg-primary/30 hidden lg:block" />

              <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
                {[
                  {
                    step: "01",
                    title: "Aktivasi Perangkat",
                    description:
                      "Nyalakan sakelar alat IoT Desa Rajang. Perangkat akan otomatis terhubung ke cloud melalui jaringan internet.",
                  },
                  {
                    step: "02",
                    title: "Uji Kondisi Tanah",
                    description:
                      "Sensor NPK dan pH akan memindai unsur hara tanah secara real-time untuk mendapatkan data lahan yang akurat.",
                  },
                  {
                    step: "03",
                    title: "Saran Rekomendasi",
                    description:
                      "AI menganalisis data tanah untuk memberikan rekomendasi tanaman, takaran pupuk, dan pestisida yang paling tepat.",
                  },
                  {
                    step: "04",
                    title: "Implementasi Aksi",
                    description:
                      "Terapkan rekomendasi secara otomatis melalui kontrol pompa pintar atau ambil tindakan manual sesuai saran AI.",
                  },
                  {
                    step: "05",
                    title: "Evaluasi & Feedback",
                    description:
                      "Berikan rating atau feedback terhadap saran AI agar algoritma rekomendasi semakin presisi untuk lahan Anda.",
                  },
                  {
                    step: "06",
                    title: "Unduh Laporan",
                    description:
                      "Unduh seluruh data riwayat sensor dan aksi irigasi dalam format CSV untuk arsip digital yang rapi.",
                  },
                ].map((item, index) => (
                  <div key={index} className="relative text-center">
                    <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-primary text-white text-xl font-bold relative z-10 border-4 border-neutral-900">
                      {item.step}
                    </div>
                    <h3 className="mt-6 text-lg font-bold text-white">
                      {item.title}
                    </h3>
                    <p className="mt-3 text-sm text-white/50 leading-relaxed">
                      {item.description}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Kontak Section - dengan Peta */}
        <section
          id="kontak"
          className="py-20 sm:py-24 bg-neutral-800/60 backdrop-blur-sm"
        >
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="grid gap-12 lg:grid-cols-2">
              <div>
                <span className="text-sm font-semibold text-primary uppercase tracking-wider">
                  Hubungi Kami
                </span>
                <h2 className="mt-3 text-3xl font-bold tracking-tight text-white sm:text-4xl">
                  Kontak
                </h2>
                <p className="mt-6 text-lg text-white/60 leading-relaxed">
                  Tertarik menggunakan AgroAdvisor untuk pertanian Anda? Hubungi
                  kami untuk konsultasi gratis dan demo sistem.
                </p>
                <div className="mt-10 space-y-6">
                  <div className="flex items-start gap-4">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/20 text-primary font-bold">
                      A
                    </div>
                    <div>
                      <h4 className="font-semibold text-white">Alamat</h4>
                      <p className="mt-1 text-white/50">
                        Kantor Desa Rajang, Jl. Mongsidi No.17, Rajang, Kec.
                        Lembang, Kabupaten Pinrang, Sulawesi Selatan
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start gap-4">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/20 text-primary font-bold">
                      T
                    </div>
                    <div>
                      <h4 className="font-semibold text-white">Telepon</h4>
                      <p className="mt-1 text-white/50">+62 812 3456 7890</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-4">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/20 text-primary font-bold">
                      E
                    </div>
                    <div>
                      <h4 className="font-semibold text-white">Email</h4>
                      <p className="mt-1 text-white/50">
                        agroadvisor@desarajang.id
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Peta Lokasi */}
              <div className="rounded-2xl overflow-hidden border border-white/10">
                <iframe
                  src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d5257.581466893842!2d119.57491767607722!3d-3.5705570964036273!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x2d945d719081fb81%3A0xb326f45c7ec9a44a!2sKantor%20Desa%20Rajang!5e1!3m2!1sen!2sid!4v1773405360118!5m2!1sen!2sid"
                  className="w-full h-[450px]"
                  style={{ border: 0 }}
                  allowFullScreen
                  loading="lazy"
                  referrerPolicy="no-referrer-when-downgrade"
                />
              </div>
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="bg-neutral-700/60 backdrop-blur-sm border-t border-white/10">
          <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
            <div className="grid gap-8 md:grid-cols-3">
              <div>
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 sm:h-14 sm:w-14 shrink-0 items-center justify-center rounded-lg overflow-hidden">
                    <Image
                      src="/inesa.png"
                      alt="AgroAdvisor Logo"
                      width={56}
                      height={56}
                      className="h-full w-full object-contain"
                    />
                  </div>
                  <div>
                    <span className="text-base font-bold text-white">
                      AgroAdvisor
                    </span>
                    <span className="block text-xs text-white/50">
                      Desa Rajang
                    </span>
                  </div>
                </div>
                <p className="mt-4 text-sm text-white/50 leading-relaxed">
                  Sistem rekomendasi dan monitoring pertanian berbasis IoT untuk
                  mendukung pertanian cerdas di Desa Rajang.
                </p>
              </div>

              <div>
                <h4 className="font-semibold text-white mb-4">Menu</h4>
                <ul className="space-y-2">
                  {navItems.map((item) => (
                    <li key={item.name}>
                      <a
                        href={item.href}
                        onClick={(e) => handleNavClick(e, item.href)}
                        className="text-sm text-white/50 hover:text-white transition-colors"
                      >
                        {item.name}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>

              <div>
                <h4 className="font-semibold text-white mb-4">Kontak</h4>
                <ul className="space-y-2 text-sm text-white/50">
                  <li>Kantor Desa Rajang</li>
                  <li>
                    Jl. Mongsidi No.17, Rajang, Kec. Lembang, Kabupaten Pinrang,
                    Sulawesi Selatan
                  </li>
                  <li>+62 812 3456 7890</li>
                  <li>agroadvisor@desarajang.id</li>
                </ul>
              </div>
            </div>

            <div className="mt-8 pt-8 border-t border-white/10">
              <p className="text-center text-sm text-white/40">
                © 2026 COCONUT. All Rights Reserved.
              </p>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
