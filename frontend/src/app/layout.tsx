import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CodeVector – Products",
  description: "Browse products with cursor-based pagination",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
