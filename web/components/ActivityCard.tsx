import { Button } from "@/components/ui/button";
import type { ActivityOut } from "@/lib/api";

type Option = {
  code: string;
  title: string;
  definition: string;
  risk_level: string | null;
  note: string;
  noteLabel: string;
};

export function ActivityCard({
  activity,
  selected,
  onSelect,
  disabled,
}: {
  activity: ActivityOut;
  selected: string;
  onSelect: (code: string) => void;
  disabled?: boolean;
}) {
  const p = activity.primary;
  const options: Option[] = [
    { ...p, note: p.reason, noteLabel: "kenapa cocok" },
    ...activity.alternatives.map((a) => ({ ...a, note: a.when_to_choose, noteLabel: "pilih ini jika" })),
  ];
  return (
    <section className="space-y-3 rounded-2xl border border-border bg-card p-4">
      <h3 className="text-lg font-semibold">Kegiatan: {activity.label}</h3>
      <ul className="space-y-3">
        {options.map((o) => {
          const isSel = o.code === selected;
          return (
            <li
              key={o.code}
              className={`rounded-xl border p-3 ${isSel ? "border-2 border-primary bg-accent" : "border-border"}`}
            >
              <p className="font-semibold">
                {o.code === p.code && <span aria-label="disarankan">★ </span>}
                <span className="font-mono">{o.code}</span> {o.title}
              </p>
              <p className="text-sm">
                <span className="text-muted">{o.noteLabel}: </span>
                {o.note}
              </p>
              <p className="mt-1 inline-block rounded-md border border-border px-2 py-0.5 text-sm font-medium">
                {o.risk_level ? `risiko: ${o.risk_level}` : "risiko: belum ada data"}
              </p>
              <details className="text-sm">
                <summary className="min-h-11 cursor-pointer py-2 font-medium text-primary">
                  definisi resmi
                </summary>
                <p>{o.definition}</p>
              </details>
              {isSel ? (
                <p className="text-sm font-semibold text-primary">✓ Dipilih</p>
              ) : (
                <Button
                  variant="outline"
                  disabled={disabled}
                  aria-label={`Pilih ${o.code}`}
                  onClick={() => onSelect(o.code)}
                >
                  Pilih kode ini
                </Button>
              )}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
