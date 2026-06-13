import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        space: {
          bg: "#070b14",
          card: "#0d1224",
          border: "#1a2540",
          muted: "#2a3a5c",
        },
      },
    },
  },
  plugins: [],
};

export default config;
