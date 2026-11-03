import type { Metadata } from "next";
import { Archivo_Black, Poppins } from "next/font/google";
import "./globals.css";

// Tipografia da identidade Creative (identidade/design-guide.md):
// Archivo Black pra titulos/numeros de destaque, Poppins pro resto.
// A familia "Archivo Black" so existe num unico corte estatico (rotulado
// weight 400 no catalogo do Google Fonts) que ja E o desenho peso 900 —
// nao existe um weight "900" separado pra pedir.
const archivoBlack = Archivo_Black({
  weight: "400",
  subsets: ["latin"],
  variable: "--font-display"
});

const poppins = Poppins({
  weight: ["400", "500", "600", "700", "800"],
  subsets: ["latin"],
  variable: "--font-body"
});

export const metadata: Metadata = {
  title: "CREATIVE ADS",
  description: "SaaS de otimizacao de campanhas da Creative Marketing",
  icons: {
    icon: "/favicon.ico",
    shortcut: "/favicon.ico",
    apple: "/icon.png"
  }
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="pt-BR" className={`${archivoBlack.variable} ${poppins.variable}`}>
      <body>{children}</body>
    </html>
  );
}
