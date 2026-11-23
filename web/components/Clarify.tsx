"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import type { Question } from "@/lib/api";

export function Clarify({
  questions,
  onSubmit,
  onSkip,
  busy,
}: {
  questions: Question[];
  onSubmit: (answers: Record<string, string>) => void;
  onSkip: () => void;
  busy: boolean;
}) {
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const set = (id: string, v: string) => setAnswers((a) => ({ ...a, [id]: v }));
  const given = Object.fromEntries(Object.entries(answers).filter(([, v]) => v.trim()));
  return (
    <section className="space-y-5" aria-label="Pertanyaan tambahan">
      <p className="text-base">Biar lebih tepat, jawab dulu ya (boleh dilewati).</p>
      {questions.map((q) => (
        <fieldset key={q.id} className="space-y-2">
          <legend className="font-semibold">{q.text}</legend>
          <div className="flex flex-wrap gap-2">
            {q.options.map((o) => (
              <Button
                key={o}
                variant={answers[q.id] === o ? "selected" : "outline"}
                aria-pressed={answers[q.id] === o}
                onClick={() => set(q.id, o)}
              >
                {o}
              </Button>
            ))}
          </div>
          <label className="block text-sm text-muted">
            <span className="sr-only">{q.text} </span>
            <span aria-hidden>atau tulis jawaban lain</span>
            <span className="sr-only">jawaban lain</span>
            <input
              type="text"
              maxLength={500}
              value={q.options.includes(answers[q.id] ?? "") ? "" : (answers[q.id] ?? "")}
              onChange={(e) => set(q.id, e.target.value)}
              className="mt-1 min-h-11 w-full rounded-xl border border-border bg-card px-3 text-base text-foreground"
            />
          </label>
        </fieldset>
      ))}
      <div className="flex flex-col gap-2">
        <Button disabled={busy || Object.keys(given).length === 0} onClick={() => onSubmit(given)}>
          Lanjut
        </Button>
        <Button variant="ghost" disabled={busy} onClick={onSkip}>
          Lewati
        </Button>
      </div>
    </section>
  );
}
