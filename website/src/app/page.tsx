import Link from "next/link";
import { Zap, ShieldCheck, Cpu, Smartphone, LayoutDashboard, Globe } from "lucide-react";

export default function HomePage() {
  const features = [
    {
      title: "Sub-Millisecond Cache",
      desc: "Redis 8.1 connection pool with distributed locks and instant token revocation.",
      icon: Zap,
    },
    {
      title: "Asynchronous ODM",
      desc: "Native PyMongo 4.9+ & Beanie 2.x handling 200k-300k+ records with strict IXSCAN indexing.",
      icon: Cpu,
    },
    {
      title: "Universal Mobile Client",
      desc: "React Native Expo SDK 52 with file-based Expo Router and real-time Socket.IO chat.",
      icon: Smartphone,
    },
    {
      title: "Operations Dashboard",
      desc: "Next.js 15 App Router administration portal with user moderation and metrics.",
      icon: LayoutDashboard,
    },
    {
      title: "Global Cloud Storage",
      desc: "AWS S3 primary object storage via aioboto3 with automated lifecycle retention.",
      icon: ShieldCheck,
    },
    {
      title: "Marketing & SEO Web",
      desc: "Fast static and server-rendered landing pages with rich OpenGraph metadata.",
      icon: Globe,
    },
  ];

  return (
    <div>
      {/* Hero Section */}
      <section className="relative overflow-hidden py-24 sm:py-32 bg-gradient-to-b from-sky-50/50 to-white">
        <div className="max-w-7xl mx-auto px-6 text-center">
          <span className="inline-block px-3 py-1 rounded-full text-xs font-semibold bg-sky-100 text-sky-800 mb-6">
            Enterprise Architecture Platform
          </span>
          <h1 className="text-4xl sm:text-6xl font-extrabold text-slate-900 tracking-tight max-w-4xl mx-auto leading-tight">
            Next-Generation Monorepo with Extreme Concurrency
          </h1>
          <p className="mt-6 text-lg text-slate-600 max-w-2xl mx-auto leading-relaxed">
            FastAPI, Redis, Beanie ODM, React Native Expo, and Next.js 15 — fully harmonized into an asynchronous multi-service ecosystem.
          </p>

          <div className="mt-10 flex items-center justify-center gap-4">
            <Link
              href="/contact"
              className="px-6 py-3.5 bg-sky-600 hover:bg-sky-700 text-white font-semibold rounded-xl shadow-md transition"
            >
              Get In Touch
            </Link>
            <a
              href="https://github.com/SHAxSOURAV/start"
              target="_blank"
              rel="noreferrer"
              className="px-6 py-3.5 bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold rounded-xl transition"
            >
              View on GitHub
            </a>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" className="py-24 bg-white border-t border-slate-100">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-3xl font-bold text-slate-900">
              Engineered for Production Scale
            </h2>
            <p className="text-slate-500 mt-3 text-sm">
              Every layer adheres strictly to zero-blocking asynchronous I/O and isolated service boundaries.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((item) => {
              const Icon = item.icon;
              return (
                <div
                  key={item.title}
                  className="p-8 rounded-2xl border border-slate-200 hover:border-sky-300 hover:shadow-lg transition bg-white"
                >
                  <div className="w-12 h-12 rounded-xl bg-sky-50 text-sky-600 flex items-center justify-center mb-6">
                    <Icon className="w-6 h-6" />
                  </div>
                  <h3 className="text-lg font-bold text-slate-900 mb-2">{item.title}</h3>
                  <p className="text-sm text-slate-600 leading-relaxed">{item.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>
    </div>
  );
}
