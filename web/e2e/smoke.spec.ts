import { expect, test } from "@playwright/test";
import path from "node:path";

test("describe -> result -> feedback", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Ceritakan usahamu").fill("Saya jual keripik pisang dikemas, dijual online");
  await page.getByRole("button", { name: "Cek izinku" }).click();

  // Fake LLM may ask a clarifying question first; skip it if so.
  const skip = page.getByRole("button", { name: "Lewati" });
  const heading = page.getByRole("heading", { name: "KBLI 2025 yang perlu didaftarkan" });
  await expect(skip.or(heading)).toBeVisible();
  if (await skip.isVisible()) await skip.click();

  await expect(heading).toBeVisible();
  await expect(page.getByText(/^risiko:/).first()).toBeVisible();
  await expect(page.getByRole("listitem").filter({ hasText: "untuk:" }).first()).toBeVisible();
  await expect(page.getByText("Bukan nasihat hukum. Cek ulang di oss.go.id")).toBeVisible();

  await page.screenshot({
    path: path.resolve(__dirname, "../../docs/screenshots/result-mobile.png"),
    fullPage: true,
  });

  await page.getByRole("button", { name: "Membantu", exact: true }).click();
  await expect(page.getByText(/Terima kasih/)).toBeVisible();
});
