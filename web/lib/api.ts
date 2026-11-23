// Types mirror api/app/pipeline/{analyze,schemas}.py and api/app/routes.py.
// The UI only renders what the API returns; it holds no business logic.

export type Source = { regulation: string; article: string | null; url: string };

export type PermitItem = {
  order: number;
  name: string;
  issuer: string;
  description: string;
  how_to: string;
  for_kbli: string[];
  condition_note: string | null;
  regional_note: string | null;
  source: Source;
  last_verified: string; // ISO date
};

export type Question = { id: string; text: string; options: string[] };

export type PrimaryOut = {
  code: string;
  title: string;
  definition: string;
  reason: string;
  risk_level: string | null;
};

export type AlternativeOut = {
  code: string;
  title: string;
  definition: string;
  when_to_choose: string;
  risk_level: string | null;
};

export type ActivityOut = {
  label: string;
  primary: PrimaryOut;
  alternatives: AlternativeOut[];
};

export type Kbli2020Mapping = { from: string; to: string[] };

export type AnalyzeResult = {
  activities: ActivityOut[];
  permits: PermitItem[];
  assumptions: string[];
  scope_note: string | null;
  kbli_2020_mapping: Kbli2020Mapping[] | null;
  data_as_of: string; // ISO date
  stale_warning: boolean;
  request_id: string;
};

export type AnalyzeRequest = { description: string; answers?: Record<string, string> };

export type AnalyzeResponse =
  | { status: "needs_clarification"; request_id: string; questions: Question[] }
  | { status: "out_of_scope"; request_id: string; message: string }
  | { status: "ok"; request_id: string; result: AnalyzeResult };

export type PermitsRequest = { request_id: string; primary_codes: string[] };
export type PermitsResponse = { permits: PermitItem[]; stale_warning: boolean };
export type FeedbackRequest = { request_id: string; helpful: boolean; comment?: string };

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

const baseUrl = () => process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function post<T>(path: string, body: unknown): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${baseUrl()}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    throw new ApiError(0, "network", "Tidak dapat terhubung ke layanan.");
  }
  if (!res.ok) {
    let code = "internal";
    let message = "Terjadi kesalahan. Coba lagi.";
    try {
      const data = await res.json();
      code = data.error?.code ?? code;
      message = data.error?.message ?? message;
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(res.status, code, message);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const analyze = (req: AnalyzeRequest) => post<AnalyzeResponse>("/v1/analyze", req);
export const permits = (req: PermitsRequest) => post<PermitsResponse>("/v1/permits", req);
export const feedback = (req: FeedbackRequest) => post<void>("/v1/feedback", req);

export const isBusy = (e: unknown) =>
  e instanceof ApiError && (e.status === 503 || e.code === "llm_unavailable");
