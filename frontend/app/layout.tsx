import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Hack Orbit — AI Mission Copilot",
  description: "AI Mission Intelligence Copilot for Satellites",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
