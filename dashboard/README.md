# Mount Fuji Operations Dashboard (Next.js 15 App Router)

Enterprise administration portal for platform moderation, analytics, user governance, and system configuration, aligned with official Next.js App Router guidelines from Context7.

---

## 1. Tech Stack & Architectural Patterns

- **Framework**: [Next.js 15](https://nextjs.org/) (App Router, Server Components & Client Components)
- **Language**: TypeScript (`strict` mode)
- **Styling**: [Tailwind CSS](https://tailwindcss.com/)
- **Icons**: [Lucide React](https://lucide.dev/)
- **Data Tables & Caching**: [TanStack Table](https://tanstack.com/table) + [TanStack Query v5](https://tanstack.com/query)
- **Charts & Visualizations**: [Recharts](https://recharts.org/)
- **State Management**: [Zustand](https://zustand-demo.pmnd.rs/)

---

## 2. Directory Layout

```
dashboard/
├── next.config.ts          # Next.js 15 configuration
├── tailwind.config.ts      # Tailwind CSS styling configuration
├── postcss.config.mjs
├── tsconfig.json           # Path aliases (@/* -> ./src/*)
├── package.json            # Scripts & dependencies
└── src/
    ├── app/                # Next.js 15 App Router pages & layouts
    │   ├── layout.tsx      # Root HTML layout with metadata
    │   ├── page.tsx        # Overview analytics dashboard
    │   ├── globals.css     # Tailwind core stylesheet
    │   ├── users/
    │   │   └── page.tsx    # User moderation & account status transitions
    │   └── settings/
    │       └── page.tsx    # Platform settings & dynamic content
    ├── components/         # Reusable UI components (Sidebar, Header, Cards)
    ├── services/           # Backend Admin API client (adminUserService)
    └── types/              # Admin TypedDicts & DTOs
```

---

## 3. Getting Started

### Installation
```bash
cd dashboard
npm install
```

### Running Development Server
```bash
# Starts Next.js on http://localhost:3001
npm run dev
```

### Building for Production
```bash
npm run build
npm start
```

---

## 4. Environment Variables

Create `.env.local` inside `dashboard/`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```
