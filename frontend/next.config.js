/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*', // 代理到FastAPI后端
      },
    ]
  },
  experimental: {
    appDir: true,
  },
}

module.exports = nextConfig 