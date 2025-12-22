/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  reactStrictMode: true,
  poweredByHeader: false,

  // Enable src directory
  experimental: {
    typedRoutes: true,
  },

  // Environment variables validation
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    NEXT_PUBLIC_WS_URL: process.env.NEXT_PUBLIC_WS_URL,
    NEXT_PUBLIC_MAX_FILE_SIZE: process.env.NEXT_PUBLIC_MAX_FILE_SIZE,
  },
};

export default nextConfig;
