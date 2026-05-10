import js from "@eslint/js";

const eslintConfig = [
  js.configs.recommended,
  {
    files: ["**/*.js"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      globals: {
        console: "readonly",
        process: "readonly",
        module: "readonly",
        self: "readonly",
        caches: "readonly",
        fetch: "readonly",
        URL: "readonly",
        Headers: "readonly",
        Response: "readonly",
        indexedDB: "readonly",
      },
    },
    rules: {
      "no-unused-vars": "error",
      "no-console": "off",
      "no-undef": "off",
    },
  },
  {
    ignores: [
      ".next/**",
      "out/**",
      "build/**",
      "next-env.d.ts",
      "node_modules/**",
      "*.config.js",
      "*.config.ts",
      "**/*.ts",
      "**/*.tsx",
      "src/**",
      ".eslintrc.js",
      "public/sw.js",
    ],
  },
];

export default eslintConfig;
