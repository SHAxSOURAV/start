# Client Frontend Application

## 1. Overview
This directory contains the primary client-facing web application for the platform. It is designed to provide an interactive, responsive experience across desktop, tablet, and mobile browsers.

---

## 2. Recommended Tech Stack
- **Framework**: [Next.js](https://nextjs.org/) (App Router) or [Vite](https://vitejs.dev/) with React
- **Language**: TypeScript (`strict` mode)
- **Styling**: [Tailwind CSS](https://tailwindcss.com/) + [shadcn/ui](https://ui.shadcn.com/) / Radix UI
- **State & Server Cache**: [TanStack Query](https://tanstack.com/query) (React Query)
- **Real-Time Client**: `socket.io-client` for bi-directional chat, typing indicators, and notifications
- **Form Management**: `react-hook-form` + `zod` for payload schema validation
- **HTTP Client**: Axios / Fetch with interceptors for automatic JWT refresh and bearer tokens

---

## 3. Backend Integration Contracts
- **Base REST API URL**: `http://localhost:8000/api/v1`
- **Real-Time Socket Server**: `http://localhost:8000`
- **API Documentation**: Refer to root `docs/openapi.yaml` for complete endpoint schemas and contracts.
- **Push & In-App Notifications**: Listen on user-specific room events (`notification`, `chat_message`).

---

## 4. Planned Directory Structure
```
frontend/
├── public/                 # Static assets, icons, fonts
├── src/
│   ├── app/                # Next.js App Router pages and layouts
│   ├── components/         # Reusable UI primitives (buttons, dialogs, cards)
│   ├── hooks/              # Custom React hooks (useAuth, useSocket, etc.)
│   ├── lib/                # API client instances, socket connection, utilities
│   ├── services/           # Domain API service callers (authService, userService)
│   └── types/              # TypeScript interface definitions (matches backend schemas)
├── package.json
└── tailwind.config.ts
```

---

## 5. Getting Started (For Future Agent Tasks)
When initializing this workspace:
```bash
npx create-next-app@latest . --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"
```
Ensure all API requests adhere to the standardized API envelope:
```json
{
  "statusCode": 200,
  "success": true,
  "message": "...",
  "data": { ... }
}
```
