/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f2ff',
          100: '#e8f0fe',
          500: '#667eea',
          600: '#5a6fd8',
          700: '#4f63d2',
        },
        secondary: {
          500: '#764ba2',
          600: '#6a4190',
        }
      },
      fontFamily: {
        sans: ['Microsoft YaHei', 'Arial', 'sans-serif'],
      },
    },
  },
  plugins: [],
} 