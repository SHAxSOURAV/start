# Admin & Operations Dashboard

## 1. Overview
This directory contains the administrative and operational dashboard. It is designed for platform operators, customer support agents, and Super Admins to monitor metrics, moderate content, oversee users, and manage platform-wide settings.

---

## 2. Core Operational Modules
1. **User & Driver Management**:
   - List, search, and filter users and drivers with cursor/page pagination.
   - Account status transitions (`ACTIVE`, `BLOCKED`, `SUSPENDED`).
   - Audit logging and moderation reason tracking.
2. **Platform Management**:
   - System settings and maintenance mode toggling.
   - Dynamic content management (Terms & Conditions, Privacy Policy, FAQs, About Us).
   - Inquiries & feedback resolution.
3. **Analytics & Financials**:
   - Platform activity metrics, active user counters, real-time socket connections.
   - Stripe subscription and payment intent audit logs.

---

## 3. Recommended Tech Stack
- **Framework**: [Next.js](https://nextjs.org/) (App Router) or [Vite](https://vitejs.dev/) + React
- **Language**: TypeScript (`strict` mode)
- **Styling & Components**: [Tailwind CSS](https://tailwindcss.com/) + [shadcn/ui](https://ui.shadcn.com/) / Lucide React
- **Data Tables**: [TanStack Table](https://tanstack.com/table) (Sorting, filtering, server-side pagination)
- **Charts & Dashboards**: [Recharts](https://recharts.org/) / [Tremor](https://tremor.so/)
- **State Management**: [Zustand](https://zustand-demo.pmnd.rs/) + [TanStack Query](https://tanstack.com/query)

---

## 4. Backend Integration Contracts
- **Base REST API URL**: `http://localhost:8000/api/v1/admin`
- **Authentication**: JWT Bearer token with roles `ADMIN` or `SUPER_ADMIN`.
- **Reference Spec**: Refer to root `docs/openapi.yaml` (Admin module tags).

---

## 5. Planned Directory Structure
```
dashboard/
├── public/
├── src/
│   ├── app/                # Admin route layouts (auth, dashboard, users, settings)
│   ├── components/         # Metric cards, data tables, modal dialogs, status badges
│   ├── hooks/              # Custom admin hooks
│   ├── lib/                # API client, role guards, token storage
│   ├── services/           # Admin API services (adminUserService, adminSettingsService)
│   └── types/              # Admin-specific TypedDicts & DTOs
├── package.json
└── tailwind.config.ts
```
