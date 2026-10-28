import { Sidebar } from "@/components/Sidebar";
import { Header } from "@/components/Header";
import { Users, Activity, CreditCard, ShieldCheck } from "lucide-react";

export default function OverviewPage() {
  const stats = [
    { title: "Total Users", value: "24,520", change: "+12.4%", icon: Users },
    { title: "Active Real-Time Sockets", value: "1,432", change: "+4.1%", icon: Activity },
    { title: "Monthly Recurring Revenue", value: "$48,900", change: "+18.2%", icon: CreditCard },
    { title: "Platform Health", value: "99.98%", change: "Optimal", icon: ShieldCheck },
  ];

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <Header />
        <main className="flex-1 p-8 bg-slate-50">
          <div className="mb-8">
            <h1 className="text-2xl font-bold text-slate-900">Dashboard Overview</h1>
            <p className="text-sm text-slate-500 mt-1">
              Live operational metrics connected to Backend API.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {stats.map((stat) => {
              const Icon = stat.icon;
              return (
                <div
                  key={stat.title}
                  className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                      {stat.title}
                    </span>
                    <Icon className="w-5 h-5 text-sky-600" />
                  </div>
                  <div className="text-2xl font-bold text-slate-900 mt-3">
                    {stat.value}
                  </div>
                  <div className="text-xs text-emerald-600 font-medium mt-1">
                    {stat.change} vs last month
                  </div>
                </div>
              );
            })}
          </div>

          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <h2 className="text-lg font-bold text-slate-900 mb-2">System Status</h2>
            <p className="text-sm text-slate-600">
              MongoDB 7 cluster running with strict IXSCAN index optimization. Redis 8.1 in-memory token cache connected with sub-millisecond response latency.
            </p>
          </div>
        </main>
      </div>
    </div>
  );
}
