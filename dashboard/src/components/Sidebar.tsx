import Link from "next/link";
import { LayoutDashboard, Users, Settings, ShieldAlert } from "lucide-react";

export function Sidebar() {
  const navItems = [
    { name: "Overview", href: "/", icon: LayoutDashboard },
    { name: "User Management", href: "/users", icon: Users },
    { name: "Platform Settings", href: "/settings", icon: Settings },
  ];

  return (
    <aside className="w-64 bg-slate-900 text-white min-h-screen flex flex-col p-4">
      <div className="flex items-center gap-3 px-2 py-4 mb-6 border-b border-slate-800">
        <ShieldAlert className="w-7 h-7 text-sky-400" />
        <span className="font-bold text-lg tracking-wide">Fuji Admin</span>
      </div>

      <nav className="flex-1 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-300 hover:text-white hover:bg-slate-800 transition"
            >
              <Icon className="w-5 h-5" />
              {item.name}
            </Link>
          );
        })}
      </nav>

      <div className="pt-4 border-t border-slate-800 text-xs text-slate-500 px-2">
        Mount Fuji Admin Console v1.0
      </div>
    </aside>
  );
}
