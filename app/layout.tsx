import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "校内信息服务智能问答台",
  description: "面向校内师生的信息化处服务知识库检索与问答工具。",
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
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
