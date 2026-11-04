import type { Metadata } from "next";

import { DetectView } from "@/components/detect-view";
import { loadModelInfo } from "@/lib/server-api";

export const metadata: Metadata = { title: "Detect" };

export default async function DetectPage() {
  const modelInfo = await loadModelInfo();
  return <DetectView modelInfo={modelInfo} />;
}
