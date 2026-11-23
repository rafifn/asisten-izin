import { defineConfig, devices } from "@playwright/test";

// Runs against an already-running fake-mode stack (API :8000, web :3000).
export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  use: { baseURL: process.env.E2E_BASE_URL ?? "http://localhost:3000" },
  projects: [{ name: "mobile", use: { ...devices["Pixel 7"] } }],
});
