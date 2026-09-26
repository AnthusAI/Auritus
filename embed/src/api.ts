export const SITE_KEY_HEADER = "X-Auritus-Site-Key";

export type JobStatus = "pending" | "processing" | "done" | "failed";

export interface JobRecord {
  content_hash: string;
  status: JobStatus;
  audio_url?: string;
  name?: string;
  byline?: string;
}

export interface CreateJobBody {
  content_hash: string;
  text: string;
  name: string;
  byline: string;
  tts_backend: string;
  voice_id: string;
}

export interface AuritusApiClientOptions {
  baseUrl: string;
  siteKey: string;
  fetchImpl?: typeof fetch;
}

/**
 * Thin fetch wrapper for embed job routes.
 */
export class AuritusApiClient {
  private readonly baseUrl: string;
  private readonly siteKey: string;
  private readonly fetchImpl: typeof fetch;

  constructor(options: AuritusApiClientOptions) {
    this.baseUrl = options.baseUrl.replace(/\/$/, "");
    this.siteKey = options.siteKey;
    this.fetchImpl = options.fetchImpl ?? fetch.bind(globalThis);
  }

  private headers(): HeadersInit {
    return {
      Accept: "application/json",
      "Content-Type": "application/json",
      [SITE_KEY_HEADER]: this.siteKey,
    };
  }

  async createJob(body: CreateJobBody): Promise<JobRecord> {
    const response = await this.fetchImpl(`${this.baseUrl}/jobs`, {
      method: "POST",
      headers: this.headers(),
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      throw new Error(
        `Auritus POST /jobs failed: ${response.status} ${await response.text()}`,
      );
    }
    return (await response.json()) as JobRecord;
  }

  /**
   * Fetch a job record.
   *
   * @param contentHash - The job's content hash.
   * @param options - `timeoutMs` aborts the request with a `TimeoutError`
   *   when it has not completed in time.
   */
  async getJob(
    contentHash: string,
    options: { timeoutMs?: number } = {},
  ): Promise<JobRecord> {
    const response = await this.fetchImpl(
      `${this.baseUrl}/jobs/${encodeURIComponent(contentHash)}`,
      {
        method: "GET",
        headers: this.headers(),
        signal:
          options.timeoutMs === undefined
            ? undefined
            : AbortSignal.timeout(options.timeoutMs),
      },
    );
    if (!response.ok) {
      throw new Error(
        `Auritus GET /jobs/${contentHash} failed: ${response.status} ${await response.text()}`,
      );
    }
    return (await response.json()) as JobRecord;
  }
}
