import { Bell, User } from "lucide-react";

export function Header() {
  return (
    <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-6">
      <div className="text-sm font-medium text-slate-500">
        System Operational • Environment: Production
      </div>

      <div className="flex items-center gap-4">
        <button className="p-2 text-slate-500 hover:text-slate-800 rounded-lg hover:bg-slate-100 transition">
          <Bell className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2 border-l border-slate-200 pl-4">
          <div className="w-8 h-8 rounded-full bg-sky-600 text-white flex items-center justify-center font-bold text-xs">
            SA
          </div>
          <span className="text-sm font-semibold text-slate-800">Super Admin</span>
        </div>
      </div>
    </header>
  );
}

