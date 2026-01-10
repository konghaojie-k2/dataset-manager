/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false, // 禁用严格模式以减少hydration问题
  // 启用standalone输出以支持Docker部署
  output: 'standalone',
  // 禁用开发模式的某些特性来减少水合错误
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: process.env.NODE_ENV === 'production'
          ? 'http://backend:8003/api/:path*'  // Docker环境中的后端服务名
          : 'http://localhost:8003/api/:path*', // 开发环境
      },
    ]
  },
}

module.exports = nextConfig 