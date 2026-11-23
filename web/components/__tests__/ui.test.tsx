import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "@/lib/api";
import { okResult, permit } from "./fixtures";

vi.mock("@/lib/api", async (orig) => ({
  ...(await orig<typeof import("@/lib/api")>()),
  analyze: vi.fn(),
  permits: vi.fn(),
  feedback: vi.fn(),
}));

import * as api from "@/lib/api";
import { Clarify } from "@/components/Clarify";
import { DescribeForm } from "@/components/DescribeForm";
import { PermitList } from "@/components/PermitList";
import { Result } from "@/components/Result";
import Page from "@/app/page";

beforeEach(() => vi.resetAllMocks());

describe("PermitList", () => {
  it("labels permits with their KBLI codes", () => {
    render(<PermitList permits={[permit({ for_kbli: ["10791", "47911"] })]} />);
    expect(screen.getByText("untuk: 10791, 47911")).toBeInTheDocument();
  });
  it("renders notes and an expandable source", async () => {
    render(
      <PermitList
        permits={[permit({ condition_note: "Jika dijual online", regional_note: "Cek dinas" })]}
      />,
    );
    expect(screen.getByText("Jika dijual online")).toBeInTheDocument();
    expect(screen.getByText(/Cek dinas/)).toBeInTheDocument();
    expect(screen.getByText(/Prosedur bisa berbeda per daerah/)).toBeInTheDocument();
    expect(screen.getByText("sumber")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /PP 28\/2025/ })).toHaveAttribute(
      "href",
      "https://example.test/pp28",
    );
  });
});

describe("Result", () => {
  it("always shows the disclaimer, date and assumptions", () => {
    render(<Result result={okResult()} />);
    expect(screen.getByText("Bukan nasihat hukum. Cek ulang di oss.go.id")).toBeInTheDocument();
    expect(screen.getByText(/Data per 15 Nov 2026/)).toBeInTheDocument();
    expect(screen.getByText("Dianggap usaha mikro/kecil")).toBeInTheDocument();
    expect(screen.getByText("risiko: menengah rendah")).toBeInTheDocument();
  });
  it("shows stale warning only when flagged", () => {
    const first = render(<Result result={okResult()} />);
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    first.unmount();
    render(<Result result={okResult({ stale_warning: true })} />);
    expect(screen.getByRole("alert")).toHaveTextContent(/belum diverifikasi/);
  });
  it("picking an alternative requests new permits", async () => {
    vi.mocked(api.permits).mockResolvedValue({
      permits: [permit({ name: "SPP-IRT" })],
      stale_warning: false,
    });
    render(<Result result={okResult()} />);
    await userEvent.click(screen.getByRole("button", { name: /pilih 10793/i }));
    expect(api.permits).toHaveBeenCalledWith({
      request_id: "11111111-1111-1111-1111-111111111111",
      primary_codes: ["10793"],
    });
    expect(await screen.findByText("SPP-IRT")).toBeInTheDocument();
  });
  it("sends feedback on thumbs up", async () => {
    vi.mocked(api.feedback).mockResolvedValue(undefined);
    render(<Result result={okResult()} />);
    await userEvent.click(screen.getByRole("button", { name: "Membantu" }));
    expect(api.feedback).toHaveBeenCalledWith({
      request_id: "11111111-1111-1111-1111-111111111111",
      helpful: true,
    });
    expect(await screen.findByText(/Terima kasih/)).toBeInTheDocument();
  });
});

describe("DescribeForm", () => {
  it("has the label, privacy note and example chips that fill the box", async () => {
    const onSubmit = vi.fn();
    render(<DescribeForm onSubmit={onSubmit} busy={false} />);
    expect(screen.getByLabelText("Ceritakan usahamu")).toBeInTheDocument();
    expect(
      screen.getByText("Jangan tulis data pribadi seperti NIK atau nomor HP."),
    ).toBeInTheDocument();
    const chips = screen.getAllByTestId("example-chip");
    expect(chips).toHaveLength(3);
    await userEvent.click(chips[0]);
    expect(screen.getByLabelText("Ceritakan usahamu")).toHaveValue(chips[0].textContent);
    await userEvent.click(screen.getByRole("button", { name: "Cek izinku" }));
    expect(onSubmit).toHaveBeenCalledWith(chips[0].textContent);
  });
});

describe("Clarify", () => {
  const qs = [{ id: "q1", text: "Dikemas?", options: ["Dikemas", "Langsung disantap"] }];
  it("submits chosen options and allows skipping", async () => {
    const onSubmit = vi.fn();
    const onSkip = vi.fn();
    render(<Clarify questions={qs} onSubmit={onSubmit} onSkip={onSkip} busy={false} />);
    await userEvent.click(screen.getByRole("button", { name: "Dikemas" }));
    await userEvent.click(screen.getByRole("button", { name: "Lanjut" }));
    expect(onSubmit).toHaveBeenCalledWith({ q1: "Dikemas" });
    await userEvent.click(screen.getByRole("button", { name: "Lewati" }));
    expect(onSkip).toHaveBeenCalled();
  });
  it("accepts free text", async () => {
    const onSubmit = vi.fn();
    render(<Clarify questions={qs} onSubmit={onSubmit} onSkip={vi.fn()} busy={false} />);
    await userEvent.type(screen.getByLabelText(/Dikemas\?.*jawaban lain/i), "dua-duanya");
    await userEvent.click(screen.getByRole("button", { name: "Lanjut" }));
    expect(onSubmit).toHaveBeenCalledWith({ q1: "dua-duanya" });
  });
});

describe("Page", () => {
  it("shows retry message on 503 and retries", async () => {
    vi.mocked(api.analyze).mockRejectedValueOnce(new ApiError(503, "llm_unavailable", "x"));
    render(<Page />);
    await userEvent.type(screen.getByLabelText("Ceritakan usahamu"), "jual keripik pisang");
    await userEvent.click(screen.getByRole("button", { name: "Cek izinku" }));
    expect(
      await screen.findByText("Layanan sedang sibuk. Coba lagi sebentar lagi."),
    ).toBeInTheDocument();
    vi.mocked(api.analyze).mockResolvedValueOnce({
      status: "ok",
      request_id: "r",
      result: okResult(),
    });
    await userEvent.click(screen.getByRole("button", { name: "Coba lagi" }));
    await waitFor(() => expect(screen.getByText("Industri Kerupuk")).toBeInTheDocument());
  });
  it("shows out-of-scope message only", async () => {
    vi.mocked(api.analyze).mockResolvedValue({
      status: "out_of_scope",
      request_id: "r",
      message: "Belum didukung.",
    });
    render(<Page />);
    await userEvent.type(screen.getByLabelText("Ceritakan usahamu"), "jual mobil bekas");
    await userEvent.click(screen.getByRole("button", { name: "Cek izinku" }));
    expect(await screen.findByText("Belum didukung.")).toBeInTheDocument();
  });
  it("skip resubmits with empty answers", async () => {
    vi.mocked(api.analyze).mockResolvedValueOnce({
      status: "needs_clarification",
      request_id: "r",
      questions: [{ id: "q1", text: "Dikemas?", options: ["Ya"] }],
    });
    render(<Page />);
    await userEvent.type(screen.getByLabelText("Ceritakan usahamu"), "jual keripik");
    await userEvent.click(screen.getByRole("button", { name: "Cek izinku" }));
    vi.mocked(api.analyze).mockResolvedValueOnce({ status: "ok", request_id: "r", result: okResult() });
    await userEvent.click(await screen.findByRole("button", { name: "Lewati" }));
    await waitFor(() =>
      expect(api.analyze).toHaveBeenLastCalledWith({ description: "jual keripik", answers: {} }),
    );
  });
  it("asks clarifying questions then resubmits with answers", async () => {
    vi.mocked(api.analyze).mockResolvedValueOnce({
      status: "needs_clarification",
      request_id: "r",
      questions: [{ id: "q1", text: "Dikemas?", options: ["Ya", "Tidak"] }],
    });
    render(<Page />);
    await userEvent.type(screen.getByLabelText("Ceritakan usahamu"), "jual keripik");
    await userEvent.click(screen.getByRole("button", { name: "Cek izinku" }));
    vi.mocked(api.analyze).mockResolvedValueOnce({
      status: "ok",
      request_id: "r",
      result: okResult(),
    });
    await userEvent.click(await screen.findByRole("button", { name: "Ya" }));
    await userEvent.click(screen.getByRole("button", { name: "Lanjut" }));
    await waitFor(() =>
      expect(api.analyze).toHaveBeenLastCalledWith({
        description: "jual keripik",
        answers: { q1: "Ya" },
      }),
    );
  });
});

describe("Page error paths", () => {
  async function submit() {
    render(<Page />);
    await userEvent.type(screen.getByLabelText("Ceritakan usahamu"), "jual keripik pisang");
    await userEvent.click(screen.getByRole("button", { name: "Cek izinku" }));
  }
  it.each([
    [new ApiError(400, "invalid_input", "Input tidak valid.")],
    [new ApiError(500, "internal", "Terjadi kesalahan pada server.")],
    [new ApiError(0, "network", "Tidak dapat terhubung ke layanan.")],
  ])("shows the Indonesian message for %s and allows retry and edit", async (err) => {
    vi.mocked(api.analyze).mockRejectedValueOnce(err);
    await submit();
    expect(await screen.findByText(err.message)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Coba lagi" })).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Ubah cerita" }));
    expect(screen.getByLabelText("Ceritakan usahamu")).toHaveValue("jual keripik pisang");
  });
  it("falls back to an Indonesian message for unknown errors", async () => {
    vi.mocked(api.analyze).mockRejectedValueOnce(new Error("Failed to fetch"));
    await submit();
    expect(await screen.findByText("Terjadi kesalahan. Coba lagi.")).toBeInTheDocument();
  });
});

describe("Result with multiple activities", () => {
  const two = () => {
    const base = okResult();
    return okResult({
      activities: [
        base.activities[0],
        {
          label: "jualan online",
          primary: { ...base.activities[0].primary, code: "47911", title: "Perdagangan Online" },
          alternatives: [
            { ...base.activities[0].alternatives[0], code: "47912", title: "Perdagangan Lain" },
          ],
        },
      ],
    });
  };
  it("picks an alternative in the second activity, keeping activity order", async () => {
    vi.mocked(api.permits).mockResolvedValue({
      permits: [permit({ name: "Izin Baru" })],
      stale_warning: false,
    });
    render(<Result result={two()} />);
    await userEvent.click(screen.getByRole("button", { name: "Pilih 47912" }));
    expect(api.permits).toHaveBeenCalledWith({
      request_id: "11111111-1111-1111-1111-111111111111",
      primary_codes: ["10791", "47912"],
    });
    expect(await screen.findByText("Izin Baru")).toBeInTheDocument();
    expect(screen.queryByText("NIB")).not.toBeInTheDocument();
  });
  it("keeps selection and permits when the permits call fails", async () => {
    vi.mocked(api.permits).mockRejectedValue(new ApiError(500, "internal", "x"));
    render(<Result result={two()} />);
    await userEvent.click(screen.getByRole("button", { name: "Pilih 47912" }));
    expect(await screen.findByText("Gagal memperbarui daftar izin. Coba lagi.")).toBeInTheDocument();
    expect(screen.getByText("NIB")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Pilih 47912" })).toBeInTheDocument();
  });
});
