# Mount Fuji Public Website (Next.js 15 App Router)

Public marketing website, landing pages, and lead-generation portal built with **Next.js 15**, **Tailwind CSS**, and **TypeScript**, aligned with official Next.js App Router guidelines from Context7.

---

## 1. Tech Stack & Architectural Patterns

- **Framework**: [Next.js 15](https://nextjs.org/) (App Router, Server-Side Rendering & Static Generation)
- **Language**: TypeScript (`strict` mode)
- **Styling**: [Tailwind CSS](https://tailwindcss.com/)
- **Icons**: [Lucide React](https://lucide.dev/)
- **Animations**: [Framer Motion](https://www.framer.com/motion/)
- **HTTP Client**: Axios (Connected to Backend public inquiry endpoints)
- **SEO & Social Sharing**: Complete OpenGraph, Twitter card metadata, and semantic markup

---

## 2. Directory Layout

```
website/
├── next.config.ts          # Next.js 15 configuration
├── tailwind.config.ts      # Tailwind CSS styling configuration
├── postcss.config.mjs
├── tsconfig.json           # Path aliases (@/* -> ./src/*)
├── package.json            # Scripts & dependencies
└── src/
    ├── app/                # Next.js 15 App Router pages & layouts
    │   ├── layout.tsx      # Global HTML shell with OpenGraph metadata, Navbar & Footer
    │   ├── page.tsx        # Public marketing landing page (Hero, Features, CTA)
    │   ├── globals.css     # Global Tailwind stylesheet
    │   ├── contact/
    │   │   └── page.tsx    # Interactive contact form (wired to Backend API)
    │   ├── terms/
    │   │   └── page.tsx    # Platform terms & conditions
    │   └── privacy/
    │       └── page.tsx    # Privacy policy
    └── components/         # Reusable presentation components (Navbar, Footer)
```

---

## 3. Getting Started

### Installation
```bash
cd website
npm install
```

### Running Development Server
```bash
# Starts Next.js on http://localhost:3000
npm run dev
```

### Building for Production
```bash
npm run build
npm start
```

---

## 4. Environment Variables

Create `.env.local` inside `website/`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```
