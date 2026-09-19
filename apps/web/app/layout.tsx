import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Pallia OS",
  description:
    "Calm, minimal enterprise software for home-based palliative care.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full">{children}</body>
    </html>
  );
}