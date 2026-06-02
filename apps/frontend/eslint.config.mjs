import { defineConfig, globalIgnores } from "eslint/config";
import { fileURLToPath } from "node:url";
import path from "node:path";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const eslintConfig = defineConfig([
  {
    settings: {
      next: {
        rootDir: __dirname,
      },
    },
  },
  ...nextVitals,
  ...nextTs,
  {
    rules: {
      "@typescript-eslint/no-unused-vars": [
        "warn",
        { argsIgnorePattern: "^_", varsIgnorePattern: "^_" },
      ],
      // Downgraded from error to warn: this rule flags standard data-fetching
      // patterns (setState inside useEffect) which are still common in React 18
      // style code. Migrate to `use` hook / Suspense when convenient.
      "react-hooks/set-state-in-effect": "warn",
    },
  },
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
    // Generated files:
    "coverage/**",
  ]),
]);

export default eslintConfig;
