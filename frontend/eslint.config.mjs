import { defineConfig, globalIgnores } from "eslint/config";

// Use @eslint/eslintrc to convert CommonJS configs
import { FlatCompat } from "@eslint/eslintrc";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const compat = new FlatCompat({
  baseDirectory: __dirname,
});

const eslintConfig = defineConfig([
  // Next.js Core Web Vitals and TypeScript configs
  ...compat.extends("next/core-web-vitals", "next/typescript"),
  
  // Override default ignores of eslint-config-next.
  globalIgnores([
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),
]);

export default eslintConfig;
