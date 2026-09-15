export const SITE_KEY_HEADER = "X-Auritus-Site-Key";

export type JobStatus = "pending" | "processing" | "done" | "failed";

export interface JobRecord {
  content_hash: string;
  status: JobStatus;
  audio_url?: string;
  name?: string;
  byline?: string;
  /** Server-computed clip length. Lets the player show a duration the
   * instant the job is done, without waiting on the <audio> element's own
   * metadata fetch (which preload="none" defers until playback starts). */
  duration_seconds?: number;
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

  async getJob(contentHash: string): Promise<JobRecord> {
    const response = await this.fetchImpl(
      `${this.baseUrl}/jobs/${encodeURIComponent(contentHash)}`,
      {
        method: "GET",
        headers: this.headers(),
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
