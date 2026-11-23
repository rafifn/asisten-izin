"use client";

import { useState } from "react";
import { Clarify } from "@/components/Clarify";
import { DescribeForm } from "@/components/DescribeForm";
import { Result } from "@/components/Result";
import { Button } from "@/components/ui/button";
import * as api from "@/lib/api";
import type { AnalyzeResponse } from "@/lib/api";

type View =
  | { kind: "form" }
  | { kind: "loading" }
  | { kind: "response"; res: AnalyzeResponse }
  | { kind: "error"; busy: boolean; message: string };

export default function Page() {
  const [description, setDescription] = useState("");
  const [answers, setAnswers] = useState<Record<string, string> | undefined>();
  const [view, setView] = useState<View>({ kind: "form" });

  async function run(desc: string, ans?: Record<string, string>) {
    setDescription(desc);
    setAnswers(ans);
    setView({ kind: "loading" });
    try {
      setView({ kind: "response", res: await api.analyze({ description: desc, ...(ans ? { answers: ans } : {}) }) });
    } catch (e) {
      setView({
        kind: "error",
        busy: api.isBusy(e),
        message: e instanceof api.ApiError ? e.message : "Terjadi kesalahan. Coba lagi.",
      });
    }
  }

  const reset = () => setView({ kind: "form" });
  const res = view.kind === "response" ? view.res : null;

  return (
    <main className="mx-auto max-w-2xl space-y-6 px-4 py-6">
      <header>
        <h1 className="text-2xl font-bold">Asisten Izin Kuliner</h1>
        <p className="text-muted">Kode KBLI 2025 dan daftar izin untuk usaha kuliner mikro dan kecil.</p>
      </header>

      {(view.kind === "form" || view.kind === "loading") && (
        <DescribeForm key={description} initial={description} busy={view.kind === "loading"} onSubmit={(d) => run(d)} />
      )}
      {view.kind === "loading" && <p role="status">Sedang memeriksa…</p>}

      {view.kind === "error" && (
        <div role="alert" className="space-y-3 rounded-xl border border-border bg-card p-4">
          <p className="font-medium">
            {view.busy ? "Layanan sedang sibuk. Coba lagi sebentar lagi." : view.message}
          </p>
          <div className="flex gap-2">
            <Button onClick={() => run(description, answers)}>Coba lagi</Button>
            <Button variant="ghost" onClick={reset}>Ubah cerita</Button>
          </div>
        </div>
      )}

      {res?.status === "needs_clarification" && (
        <Clarify
          questions={res.questions}
          busy={false}
          onSubmit={(a) => run(description, a)}
          onSkip={() => run(description, {})}
        />
      )}

      {res?.status === "out_of_scope" && (
        <div className="space-y-3 rounded-xl border border-border bg-card p-4">
          <p>{res.message}</p>
          <Button variant="outline" onClick={reset}>Coba usaha lain</Button>
        </div>
      )}

      {res?.status === "ok" && (
        <>
          <p className="text-sm">
            <span className="font-semibold">Usaha:</span> {description}
          </p>
          <Result result={res.result} onRetell={reset} />
          {res.result.activities.length > 0 && (
            <Button variant="outline" onClick={reset} className="w-full">Mulai dari awal</Button>
          )}
        </>
      )}
    </main>
  );
}
