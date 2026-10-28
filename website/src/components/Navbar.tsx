import Link from "next/link";
import { Mountain } from "lucide-react";

export function Navbar() {
  return (
    <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-slate-100">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 font-bold text-lg text-slate-900">
          <Mountain className="w-6 h-6 text-sky-600" />
          <span>Mount Fuji</span>
        </Link>

        <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-600">
          <Link href="/#features" className="hover:text-slate-900 transition">Features</Link>
          <Link href="/#pricing" className="hover:text-slate-900 transition">Pricing</Link>
          <Link href="/contact" className="hover:text-slate-900 transition">Contact Us</Link>
        </nav>

        <div className="flex items-center gap-4">
          <Link
            href="/contact"
            className="px-4 py-2 text-sm font-semibold text-white bg-sky-600 hover:bg-sky-700 rounded-lg shadow-sm transition"
          >
            Get Started
          </Link>
        </div>
      </div>
    </header>
  );
}

