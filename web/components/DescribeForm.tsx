"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";

export const EXAMPLES = [
  "Saya membuat keripik pisang di rumah, dikemas, dijual online dan dititip di warung",
  "Warung makan kecil dengan beberapa meja, jual nasi dan lauk",
  "Katering nasi kotak untuk acara kantor, dimasak di dapur rumah",
];

export function DescribeForm({
  onSubmit,
  busy,
  initial = "",
}: {
  onSubmit: (description: string) => void;
  busy: boolean;
  initial?: string;
}) {
  const [text, setText] = useState(initial);
  const valid = text.trim().length >= 3;
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        if (valid && !busy) onSubmit(text.trim());
      }}
      className="space-y-3"
    >
      <label htmlFor="desc" className="block text-lg font-semibold">
        Ceritakan usahamu
      </label>
      <textarea
        id="desc"
        value={text}
        onChange={(e) => setText(e.target.value)}
        rows={5}
        maxLength={2000}
        aria-describedby="desc-note"
        className="w-full rounded-xl border border-border bg-card p-3 text-base"
      />
      <p id="desc-note" className="text-sm text-muted">
        Jangan tulis data pribadi seperti NIK atau nomor HP.
      </p>
      <div className="flex flex-col gap-2">
        <span className="text-sm text-muted">Contoh:</span>
        {EXAMPLES.map((ex) => (
          <button
            key={ex}
            type="button"
            data-testid="example-chip"
            onClick={() => setText(ex)}
            className="min-h-11 rounded-xl border border-border bg-card px-3 py-2 text-left text-sm hover:bg-accent"
          >
            {ex}
          </button>
        ))}
      </div>
      <Button type="submit" disabled={!valid || busy} className="w-full">
        {busy ? "Memeriksa…" : "Cek izinku"}
      </Button>
    </form>
  );
}
