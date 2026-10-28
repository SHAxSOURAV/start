import { Sidebar } from "@/components/Sidebar";
import { Header } from "@/components/Header";
import { Search, Filter, ShieldCheck, ShieldAlert } from "lucide-react";

export default function UsersPage() {
  const mockUsers = [
    { id: "usr_101", name: "Alice Johnson", email: "alice@example.com", role: "USER", status: "ACTIVE" },
    { id: "usr_102", name: "David Miller", email: "david@example.com", role: "DRIVER", status: "ACTIVE" },
    { id: "usr_103", name: "Charlie Brown", email: "charlie@example.com", role: "USER", status: "SUSPENDED" },
    { id: "usr_104", name: "Eva Williams", email: "eva@example.com", role: "ADMIN", status: "ACTIVE" },
  ];

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <Header />
        <main className="flex-1 p-8 bg-slate-50">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-2xl font-bold text-slate-900">User Management</h1>
              <p className="text-sm text-slate-500 mt-1">
                Moderate accounts, inspect audit trails, and manage security statuses.
              </p>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="p-4 border-b border-slate-200 flex items-center justify-between gap-4">
              <div className="flex items-center gap-2 bg-slate-100 rounded-lg px-3 py-2 w-72">
                <Search className="w-4 h-4 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search by name or email..."
                  className="bg-transparent text-sm text-slate-800 placeholder-slate-400 focus:outline-none w-full"
                />
              </div>

              <button className="flex items-center gap-2 px-3 py-2 border border-slate-200 rounded-lg text-sm text-slate-700 hover:bg-slate-50">
                <Filter className="w-4 h-4" />
                Filters
              </button>
            </div>

            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200">
                <tr>
                  <th className="px-6 py-3.5">Name</th>
                  <th className="px-6 py-3.5">Email</th>
                  <th className="px-6 py-3.5">Role</th>
                  <th className="px-6 py-3.5">Status</th>
                  <th className="px-6 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 text-slate-700">
                {mockUsers.map((user) => (
                  <tr key={user.id} className="hover:bg-slate-50">
                    <td className="px-6 py-4 font-medium text-slate-900">{user.name}</td>
                    <td className="px-6 py-4 text-slate-500">{user.email}</td>
                    <td className="px-6 py-4">
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-slate-100 text-slate-800">
                        {user.role}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${
                          user.status === "ACTIVE"
                            ? "bg-emerald-100 text-emerald-800"
                            : "bg-amber-100 text-amber-800"
                        }`}
                      >
                        {user.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button className="text-xs font-semibold text-sky-600 hover:text-sky-800">
                        Manage Status
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </main>
      </div>
    </div>
  );
}
