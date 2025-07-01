/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false, // 禁用严格模式以减少hydration问题
  // 禁用开发模式的某些特性来减少水合错误
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*', // 代理到FastAPI后端
      },
    ]
  },
}

module.exports = nextConfig 