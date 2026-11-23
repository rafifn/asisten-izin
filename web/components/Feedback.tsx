"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import * as api from "@/lib/api";

export function Feedback({ requestId }: { requestId: string }) {
  const [state, setState] = useState<"idle" | "sending" | "done" | "error">("idle");
  async function send(helpful: boolean) {
    setState("sending");
    try {
      await api.feedback({ request_id: requestId, helpful });
      setState("done");
    } catch {
      setState("error");
    }
  }
  if (state === "done") return <p role="status">Terima kasih atas masukanmu!</p>;
  return (
    <div className="flex flex-wrap items-center gap-3">
      <span className="font-medium">Apakah ini membantu?</span>
      <Button variant="outline" aria-label="Membantu" disabled={state === "sending"} onClick={() => send(true)}>
        👍
      </Button>
      <Button variant="outline" aria-label="Tidak membantu" disabled={state === "sending"} onClick={() => send(false)}>
        👎
      </Button>
      {state === "error" && <span role="alert" className="text-sm">Gagal mengirim. Coba lagi.</span>}
    </div>
  );
}
