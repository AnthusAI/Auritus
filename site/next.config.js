/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'export',
  images: {
    unoptimized: true,
  },
  // `next build` and `next dev` share .next by default, so a verification
  // build run against a live dev server overwrites the dev manifests and
  // leaves it serving the fallback shell. Set NEXT_DIST_DIR to build aside.
  distDir: process.env.NEXT_DIST_DIR || '.next',
};

module.exports = nextConfig;
