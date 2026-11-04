import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  // The sandbox preview serves the app from a proxied host, not localhost.
  allowedDevOrigins: ["*.e2b.app"],
};

export default nextConfig;
