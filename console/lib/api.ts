/** Admin API client for Auritus monitoring and queue control. */

import { getAuthorizationHeader } from './auth';

export interface OverviewMetrics {
  counts: {
    pending: number;
    claimed: number;
    done: number;
    failed: number;
  };
  worker_breakdown: {
    local: number;
    batch: number;
  };
  avg_duration_seconds: number;
  batch_queue_state: string;
  total_sampled_jobs: number;
}

export interface JobSummary {
  content_hash: string;
  status: 'pending' | 'claimed' | 'done' | 'failed';
  tts_backend?: string;
  voice_id?: string;
  text?: string;
  name?: string;
  byline?: string;
  site_id?: string;
  worker_type?: 'local' | 'batch';
  claimed_by?: string;
  created_at?: string;
  claimed_at?: string;
  completed_at?: string;
  failed_at?: string;
  duration_seconds?: number;
  error_message?: string;
  audio_url?: string;
}

export interface JobDetail extends JobSummary {
  site_key?: string;
}

const API_BASE = (process.env.NEXT_PUBLIC_AURITUS_API_ENDPOINT || '').replace(/\/+$/, '');

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${path}`;
  const authHeaders = getAuthorizationHeader();
  const headers = {
    'Content-Type': 'application/json',
    ...authHeaders,
    ...(options.headers || {}),
  };

  const response = await fetch(url, { ...options, headers });
  if (response.status === 401 || response.status === 403) {
    throw new Error('Unauthorized');
  }
  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    throw new Error(errorBody.error || `HTTP ${response.status}`);
  }
  return response.json();
}

export async function fetchOverview(): Promise<OverviewMetrics> {
  return apiFetch<OverviewMetrics>('/admin/overview');
}

export async function fetchJobs(status?: string, limit?: number): Promise<{ jobs: JobSummary[] }> {
  const params = new URLSearchParams();
  if (status) params.set('status', status);
  if (limit) params.set('limit', String(limit));
  const query = params.toString() ? `?${params.toString()}` : '';
  return apiFetch<{ jobs: JobSummary[] }>(`/admin/jobs${query}`);
}

export async function fetchJobDetail(hash: string): Promise<JobDetail> {
  return apiFetch<JobDetail>(`/admin/jobs/${encodeURIComponent(hash)}`);
}

export async function toggleQueue(desiredState?: 'ENABLED' | 'DISABLED'): Promise<{ state: string }> {
  return apiFetch<{ state: string }>('/admin/queue/toggle', {
    method: 'POST',
    body: JSON.stringify(desiredState ? { state: desiredState } : {}),
  });
}
