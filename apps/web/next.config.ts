import path from "node:path";

import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

const withNextIntl = createNextIntlPlugin();

const nextConfig: NextConfig = {
  // Needed so Turbopack can resolve packages/i18n, which lives outside
  // apps/web (this repo isn't set up as an npm workspace).
  turbopack: {
    root: path.join(__dirname, "../.."),
  },
};

export default withNextIntl(nextConfig);
