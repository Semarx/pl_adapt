import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { viteSingleFile } from "vite-plugin-singlefile";

// PL alone, no comparator. One self-contained file, recordings inlined.
export default defineConfig({
  plugins: [react(), viteSingleFile()],
  publicDir: false,
  build: {
    outDir: "dist-fp", assetsInlineLimit: 100000000, emptyOutDir: false,
    rollupOptions: { input: "index_fp.html" },
  },
});
