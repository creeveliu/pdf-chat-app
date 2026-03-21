import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PDF Chat App",
  description: "Upload PDFs and ask AI questions.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
