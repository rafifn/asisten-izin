import type { NextConfig } from "next";

// "standalone" emits a self-contained server for the Docker image (web/Dockerfile).
const nextConfig: NextConfig = { output: "standalone" };

export default nextConfig;
