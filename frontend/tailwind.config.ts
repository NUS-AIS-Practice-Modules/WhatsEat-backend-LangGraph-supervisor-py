import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
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
} satisfies Config;
