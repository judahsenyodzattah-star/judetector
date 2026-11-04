import type { Metadata } from "next";
import type { ReactNode } from "react";

import { AppShell } from "@/components/app-shell";
import { loadModelInfo } from "@/lib/server-api";
import { SessionProvider } from "@/lib/session";

import "./globals.css";

export const metadata: Metadata = {
  title: { default: "JUDEtector", template: "%s · JUDEtector" },
  description:
    "Check a photo for one trained subject. A single-subject detector — not face recognition.",
  icons: { icon: "/icon.svg" },
};

export default async function RootLayout({ children }: { children: ReactNode }) {
  const modelInfo = await loadModelInfo();

  return (
    <html lang="en">
      <body>
        <SessionProvider>
          <AppShell modelInfo={modelInfo}>{children}</AppShell>
        </SessionProvider>
      </body>
    </html>
  );
}
