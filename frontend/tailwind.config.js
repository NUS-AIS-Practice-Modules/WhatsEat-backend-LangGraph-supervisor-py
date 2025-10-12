/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./public/index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: "#ff6b6b",
          muted: "#ffe3e3",
        },
      },
    },
  },
  plugins: [],
};
