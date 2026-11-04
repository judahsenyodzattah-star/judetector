import type { Metadata } from "next";

import { HomeView } from "@/components/home-view";
import { loadModelInfo } from "@/lib/server-api";

export const metadata: Metadata = { title: "Home" };

export default async function HomePage() {
  const modelInfo = await loadModelInfo();
  return <HomeView modelInfo={modelInfo} />;
}
