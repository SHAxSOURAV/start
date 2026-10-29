import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";

export const metadata: Metadata = {
  title: "Mount Fuji | High-Performance Cloud Architecture",
  description:
    "Production-grade, asynchronous monorepo platform with FastAPI, Redis, Socket.IO, Next.js, and React Native Expo.",
  openGraph: {
    title: "Mount Fuji Platform",
    description: "High-performance enterprise architecture for global scale.",
    url: "https://mountfuji.com",
    siteName: "Mount Fuji",
    locale: "en_US",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-white text-slate-900 antialiased flex flex-col min-h-screen">
        <Navbar />
        <main className="flex-1">{children}</main>
        <Footer />
      </body>
    </html>
  );
}

