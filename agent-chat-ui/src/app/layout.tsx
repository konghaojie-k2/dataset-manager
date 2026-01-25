import type { Metadata } from "next";
import "./globals.css";
import { Playfair_Display, Outfit } from "next/font/google";
import React from "react";
import { NuqsAdapter } from "nuqs/adapters/next/app";

// Distinctive typography pair: elegant serif + modern sans-serif
const playfair = Playfair_Display({
  subsets: ["latin"],
  variable: "--font-playfair",
  display: "swap",
  weight: ["400", "500", "600", "700"],
});

const outfit = Outfit({
  subsets: ["latin"],
  variable: "--font-outfit",
  display: "swap",
  weight: ["300", "400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "数据集超市 | Dataset Supermarket",
  description: "智能数据集管理平台 - 上传、分析、发现数据集",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body className={`${playfair.variable} ${outfit.variable} font-sans antialiased`}>
        <NuqsAdapter>{children}</NuqsAdapter>
      </body>
    </html>
  );
}
