import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        freyja: {
          dark: "#0f0f1a",
          panel: "#1a1a2e",
          accent: "#89dceb",
          teal: "#94e2d5",
        },
      },
    },
  },
  plugins: [],
};

export default config;
