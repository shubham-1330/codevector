import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      colors: {
        canvas: "#0f1117",
        surface: "#1a1d27",
        border: "#2a2d3a",
        accent: "#6c8ef7",
        muted: "#6b7280",
      },
    },
  },
  plugins: [],
};

export default config;
