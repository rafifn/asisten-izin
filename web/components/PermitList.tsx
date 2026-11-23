import type { PermitItem } from "@/lib/api";
import { formatDate } from "@/lib/format";

export const NO_PERMITS_MESSAGE = "Belum ada data izin untuk kode ini. Cek langsung di oss.go.id.";

export function PermitList({ permits }: { permits: PermitItem[] }) {
  if (permits.length === 0) {
    return (
      <section aria-labelledby="permits-h" className="space-y-3">
        <h2 id="permits-h" className="text-xl font-bold">
          Izin yang perlu diurus (berurutan)
        </h2>
        <p className="rounded-xl border border-border bg-card p-3 text-sm">{NO_PERMITS_MESSAGE}</p>
      </section>
    );
  }
  return (
    <section aria-labelledby="permits-h" className="space-y-3">
      <h2 id="permits-h" className="text-xl font-bold">
        Izin yang perlu diurus (berurutan)
      </h2>
      <ol className="space-y-3">
        {permits.map((p) => (
          <li key={`${p.order}-${p.name}`} className="rounded-2xl border border-border bg-card p-4">
            <div className="flex gap-3">
              <span
                aria-hidden
                className="flex size-8 shrink-0 items-center justify-center rounded-full bg-primary font-bold text-primary-foreground"
              >
                {p.order}
              </span>
              <div className="min-w-0 space-y-1">
                <h3 className="font-semibold">{p.name}</h3>
                <p className="text-sm text-muted">
                  {p.issuer} ·{" "}
                  <span>{p.for_kbli.length ? `untuk: ${p.for_kbli.join(", ")}` : "untuk: semua"}</span>
                </p>
                <p className="text-sm">{p.description}</p>
                <p className="text-sm">
                  <span className="font-semibold">Cara mengurus: </span>
                  {p.how_to}
                </p>
                {p.condition_note && <p className="text-sm font-medium">{p.condition_note}</p>}
                {p.regional_note && <p className="text-sm">Daerah: {p.regional_note}</p>}
                <details className="text-sm">
                  <summary className="min-h-11 cursor-pointer py-2 font-medium text-primary">
                    sumber
                  </summary>
                  <p>
                    <a
                      href={p.source.url}
                      target="_blank"
                      rel="noreferrer"
                      className="break-words text-primary underline"
                    >
                      {p.source.regulation}
                      {p.source.article ? `, ${p.source.article}` : ""}
                    </a>
                  </p>
                  <p className="text-muted">Terakhir diverifikasi {formatDate(p.last_verified)}</p>
                </details>
              </div>
            </div>
          </li>
        ))}
      </ol>
      <p className="text-sm text-muted">
        ⓘ Prosedur bisa berbeda per daerah. Cek ke dinas setempat.
      </p>
    </section>
  );
}
