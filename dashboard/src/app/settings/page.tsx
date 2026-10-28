import { Sidebar } from "@/components/Sidebar";
import { Header } from "@/components/Header";

export default function SettingsPage() {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <Header />
        <main className="flex-1 p-8 bg-slate-50">
          <div className="mb-8">
            <h1 className="text-2xl font-bold text-slate-900">Platform Settings</h1>
            <p className="text-sm text-slate-500 mt-1">
              Configure terms, privacy policy, and system operational toggles.
            </p>
          </div>

          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm max-w-2xl space-y-6">
            <div>
              <label className="block text-sm font-semibold text-slate-800 mb-1">
                Maintenance Mode
              </label>
              <p className="text-xs text-slate-500 mb-3">
                Temporarily restrict platform access to Super Admins.
              </p>
              <button className="px-4 py-2 bg-slate-200 text-slate-700 text-sm font-semibold rounded-lg hover:bg-slate-300 transition">
                Enable Maintenance Mode
              </button>
            </div>

            <div className="border-t border-slate-200 pt-6">
              <label className="block text-sm font-semibold text-slate-800 mb-1">
                Terms & Conditions Version
              </label>
              <p className="text-xs text-slate-500 mb-3">
                Last updated via Admin API.
              </p>
              <input
                type="text"
                disabled
                value="v2.4 (Published on MongoDB cluster)"
                className="w-full bg-slate-100 border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-600"
              />
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
