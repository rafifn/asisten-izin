"use client";

import { useState } from "react";
import { ActivityCard } from "@/components/ActivityCard";
import { Feedback } from "@/components/Feedback";
import { PermitList } from "@/components/PermitList";
import { Button } from "@/components/ui/button";
import * as api from "@/lib/api";
import type { AnalyzeResult, PermitItem } from "@/lib/api";
import { formatDate } from "@/lib/format";

export const STALE_MESSAGE =
  "Sebagian data sudah lama tidak diverifikasi. Pastikan cek ulang di oss.go.id.";

/**
 * `onRetell` returns to the form with the description kept; it is offered when the API was
 * not sure about any code (no activities).
 */
export function Result({ result, onRetell }: { result: AnalyzeResult; onRetell?: () => void }) {
  if (result.activities.length === 0) {
    return (
      <div className="space-y-4">
        {result.scope_note && (
          <p className="rounded-xl border border-border bg-card p-3 text-sm">{result.scope_note}</p>
        )}
        {onRetell && (
          <Button onClick={onRetell} className="w-full">
            Ceritakan lebih rinci
          </Button>
        )}
      </div>
    );
  }
  return <ResultBody result={result} />;
}

function ResultBody({ result }: { result: AnalyzeResult }) {
  const [selected, setSelected] = useState<string[]>(() =>
    result.activities.map((a) => a.primary.code),
  );
  const [permits, setPermits] = useState<PermitItem[]>(result.permits);
  const [stale, setStale] = useState(result.stale_warning);
  const [dataAsOf, setDataAsOf] = useState(result.data_as_of);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function select(index: number, code: string) {
    const next = selected.map((c, i) => (i === index ? code : c));
    setLoading(true);
    setError(null);
    try {
      const res = await api.permits({ request_id: result.request_id, primary_codes: next });
      setSelected(next);
      setPermits(res.permits);
      setStale(res.stale_warning);
      setDataAsOf(res.data_as_of);
    } catch {
      setError("Gagal memperbarui daftar izin. Coba lagi.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <p className="text-sm text-muted">Data per {formatDate(dataAsOf)}</p>
      {result.assumptions.length > 0 && (
        <ul className="-mt-4 text-sm text-muted">
          {result.assumptions.map((a) => (
            <li key={a}>{a}</li>
          ))}
        </ul>
      )}
      {stale && (
        <p role="alert" className="rounded-xl bg-warn-bg p-3 text-sm font-medium text-warn-fg">
          ⚠ {STALE_MESSAGE}
        </p>
      )}
      {result.scope_note && (
        <p className="rounded-xl border border-border bg-card p-3 text-sm">{result.scope_note}</p>
      )}
      {result.kbli_2020_mapping?.map((m) => (
        <p key={m.from} className="text-sm text-muted">
          {m.to.length > 0
            ? `kode lama ${m.from} → kode baru ${m.to.join(", ")}`
            : `kode lama ${m.from} tidak punya padanan dalam cakupan aplikasi ini`}
        </p>
      ))}
      <section aria-labelledby="kbli-h" className="space-y-3">
        <h2 id="kbli-h" className="text-xl font-bold">
          KBLI 2025 yang perlu didaftarkan
        </h2>
        {result.activities.map((a, i) => (
          <ActivityCard
            key={a.label}
            activity={a}
            selected={selected[i]}
            disabled={loading}
            onSelect={(code) => select(i, code)}
          />
        ))}
      </section>
      {error && (
        <p role="alert" className="text-sm font-medium">
          {error}
        </p>
      )}
      <div aria-busy={loading}>
        <PermitList permits={permits} />
      </div>
      <p className="rounded-xl bg-warn-bg p-3 font-semibold text-warn-fg">
        <span aria-hidden>⚠ </span>
        <span>Bukan nasihat hukum. Cek ulang di oss.go.id</span>
      </p>
      <Feedback requestId={result.request_id} />
    </div>
  );
}
