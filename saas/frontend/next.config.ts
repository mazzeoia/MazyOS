import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  output: "standalone",
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.BACKEND_API_URL ?? "http://127.0.0.1:8000"}/:path*`
      }
    ];
  }
};

export default nextConfig;
