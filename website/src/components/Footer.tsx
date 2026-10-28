import Link from "next/link";
import { Mountain } from "lucide-react";

export function Footer() {
  return (
    <footer className="bg-slate-900 text-slate-400 py-12 border-t border-slate-800">
      <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 md:grid-cols-4 gap-8">
        <div>
          <div className="flex items-center gap-2 font-bold text-white text-lg mb-3">
            <Mountain className="w-5 h-5 text-sky-400" />
            <span>Mount Fuji</span>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            High-performance asynchronous backend and client platform designed for extreme concurrency and low-latency scalability.
          </p>
        </div>

        <div>
          <h4 className="text-sm font-semibold text-white mb-3">Product</h4>
          <ul className="space-y-2 text-xs">
            <li><Link href="/#features" className="hover:text-white transition">Features</Link></li>
            <li><Link href="/#pricing" className="hover:text-white transition">Pricing</Link></li>
            <li><Link href="/#faq" className="hover:text-white transition">FAQ</Link></li>
          </ul>
        </div>

        <div>
          <h4 className="text-sm font-semibold text-white mb-3">Legal</h4>
          <ul className="space-y-2 text-xs">
            <li><Link href="/terms" className="hover:text-white transition">Terms & Conditions</Link></li>
            <li><Link href="/privacy" className="hover:text-white transition">Privacy Policy</Link></li>
          </ul>
        </div>

        <div>
          <h4 className="text-sm font-semibold text-white mb-3">Support</h4>
          <ul className="space-y-2 text-xs">
            <li><Link href="/contact" className="hover:text-white transition">Contact Us</Link></li>
            <li><span className="text-slate-500">support@mountfuji.com</span></li>
          </ul>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 mt-12 pt-6 border-t border-slate-800 text-center text-xs text-slate-600">
        © {new Date().getFullYear()} Mount Fuji Platform. All rights reserved.
      </div>
    </footer>
  );
}
