import path from "node:path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* Standalone output supports a small, self-contained Docker image. */
  output: "standalone",
  /* Pin the workspace root so Turbopack ignores unrelated higher-level lockfiles. */
  turbopack: {
    root: path.join(__dirname),
  },
};

export default nextConfig;