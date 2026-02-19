import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/ThemeProvider";
import { AuthProvider } from "@/components/AuthProvider";
import { FilterProvider } from "@/contexts/FilterContext";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Métricas Taxbase — Painel de Atendimentos",
  description:
    "Dashboard de métricas de atendimento do Messenger para a equipe de TI da Taxbase.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR" suppressHydrationWarning>
      <body className={`${inter.variable} antialiased`}>
        <ThemeProvider>
          <AuthProvider>
            <FilterProvider>{children}</FilterProvider>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
