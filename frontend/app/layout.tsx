import "./globals.css";
import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = { title: "Panic Planner", description: "A cram schedule that gives hard topics more time." };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en"><body>
      <nav className="nav"><Link href="/">Planner</Link><Link href="/chat">Coach chat</Link></nav>
      {children}
    </body></html>
  );
}
