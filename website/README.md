# Public Marketing Website

## 1. Overview
This directory contains the public marketing website, landing pages, and lead-generation portal. It is optimized for high-speed performance, search engine indexing (SEO), and conversion.

---

## 2. Key Pages & Features
- **Hero & Value Proposition**: Engaging interactive hero with product features and CTAs.
- **Features & Solutions**: Showcase of capabilities, platform security, and integrations.
- **Pricing & Plans**: Tiered subscription plans with direct Stripe Checkout integration.
- **Public Legal Pages**: Dynamic or static Terms of Service, Privacy Policy, and About Us.
- **Contact & Inquiries**: Public contact forms directly submitting to Backend Inquiries endpoints.
- **SEO & Social Sharing**: Complete OpenGraph, Twitter cards, and structured JSON-LD schemas.

---

## 3. Recommended Tech Stack
- **Framework**: [Next.js](https://nextjs.org/) (Static Site Generation / Incremental Static Regeneration) or [Astro](https://astro.build/)
- **Language**: TypeScript
- **Styling**: [Tailwind CSS](https://tailwindcss.com/)
- **Animations**: [Framer Motion](https://www.framer.com/motion/)
- **SEO & Analytics**: Next-SEO, Google Analytics / Plausible integration

---

## 4. Backend Integration Contracts
- **Base REST API URL**: `http://localhost:8000/api/v1`
- **Contact Submissions**: `POST http://localhost:8000/api/v1/admin/manage-web/contact-us`
- **Dynamic Content**: `GET http://localhost:8000/api/v1/admin/manage-web/terms-conditions`, `GET .../privacy-policy`

---

## 5. Planned Directory Structure
```
website/
├── public/                 # Static marketing imagery, favicons, robots.txt, sitemap.xml
├── src/
│   ├── app/                # Pages (home, pricing, features, about, contact, legal)
│   ├── components/         # Hero, navigation, footer, pricing cards, contact form
│   ├── lib/                # API client, SEO utilities
│   └── styles/             # Global styling & Tailwind typography
├── package.json
└── tailwind.config.ts
```
