import { afterEach, describe, expect, it, vi } from "vitest";
import { analyze, ApiError, REQUEST_TIMEOUT_MS } from "@/lib/api";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("api error mapping", () => {
  it("maps fetch failure to an Indonesian network error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
    await expect(analyze({ description: "abc" })).rejects.toMatchObject({
      code: "network",
      message: "Tidak dapat terhubung ke layanan.",
    });
  });
  it("uses the backend error body for 400 and 500", async () => {
    for (const [status, code, message] of [
      [400, "invalid_input", "Input tidak valid."],
      [500, "internal", "Terjadi kesalahan pada server."],
    ] as const) {
      vi.stubGlobal(
        "fetch",
        vi.fn().mockResolvedValue(new Response(JSON.stringify({ error: { code, message } }), { status })),
      );
      const err = await analyze({ description: "abc" }).catch((e) => e);
      expect(err).toBeInstanceOf(ApiError);
      expect(err).toMatchObject({ status, code, message });
    }
  });
  it("aborts a hanging request after the timeout with a friendly message", async () => {
    vi.useFakeTimers();
    vi.stubGlobal(
      "fetch",
      vi.fn(
        (_url: string, init: RequestInit) =>
          new Promise((_resolve, reject) => {
            init.signal?.addEventListener("abort", () =>
              reject(new DOMException("aborted", "AbortError")),
            );
          }),
      ),
    );
    const pending = analyze({ description: "abc" }).catch((e) => e);
    await vi.advanceTimersByTimeAsync(REQUEST_TIMEOUT_MS);
    const err = await pending;
    expect(err).toBeInstanceOf(ApiError);
    expect(err).toMatchObject({
      code: "timeout",
      message: "Permintaan terlalu lama. Coba lagi sebentar lagi.",
    });
  });
});
