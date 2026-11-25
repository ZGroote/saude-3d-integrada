import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = { title: { default: "Saúde 3D Integrada", template: "%s · Saúde 3D" }, description: "Prontuário clínico integrado para profissionais de saúde." };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="pt-BR"><body className="min-h-screen antialiased">{children}</body></html>;
}
