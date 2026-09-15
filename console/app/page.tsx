'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { fetchOverview, fetchJobs, OverviewMetrics, JobSummary } from '../lib/api';

export default function DashboardOverviewPage() {
  const [metrics, setMetrics] = useState<OverviewMetrics>({
    counts: { pending: 0, claimed: 0, done: 0, failed: 0 },
    worker_breakdown: { local: 0, batch: 0 },
    avg_duration_seconds: 0,
    batch_queue_state: 'UNKNOWN',
    total_sampled_jobs: 0,
  });
  const [recentJobs, setRecentJobs] = useState<JobSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      setError(null);
      try {
        const [overviewData, jobsData] = await Promise.all([
          fetchOverview(),
          fetchJobs(),
        ]);
        if (overviewData) setMetrics(overviewData);
        if (jobsData?.jobs) setRecentJobs(jobsData.jobs.slice(0, 8));
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : 'Failed to load dashboard data';
        setError(message);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const totalCompleted = metrics.counts.done;
  const localRatio =
    metrics.worker_breakdown.local + metrics.worker_breakdown.batch > 0
      ? Math.round(
          (metrics.worker_breakdown.local /
            (metrics.worker_breakdown.local + metrics.worker_breakdown.batch)) *
            100
        )
      : 100;

  return (
    <div className="console-container">
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>System Observability & Monitoring</h1>
        <p style={{ color: 'var(--ink-muted)' }}>
          Real-time metrics for just-in-time TTS generation, worker race performance, and Batch fallback health.
        </p>
      </div>

      {error && (
        <div className="card" style={{ marginBottom: '1.5rem', background: '#fff1f0', borderColor: '#ffa39e', color: '#cf1322' }}>
          <strong>Error loading dashboard:</strong> {error}
        </div>
      )}

      {/* KPI Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.25rem', marginBottom: '2rem' }}>
        <div className="card">
          <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--ink-muted)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
            Completed Jobs
          </div>
          <div style={{ fontSize: '2.2rem', fontWeight: 700, fontFamily: 'Georgia, serif' }}>
            {totalCompleted}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--ink-muted)', marginTop: '0.25rem' }}>
            Pending: <strong>{metrics.counts.pending}</strong> | Claimed: <strong>{metrics.counts.claimed}</strong>
          </div>
        </div>

        <div className="card">
          <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--ink-muted)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
            Worker Race: Local Share
          </div>
          <div style={{ fontSize: '2.2rem', fontWeight: 700, fontFamily: 'Georgia, serif', color: 'var(--success)' }}>
            {localRatio}%
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--ink-muted)', marginTop: '0.25rem' }}>
            Local: <strong>{metrics.worker_breakdown.local}</strong> vs Batch: <strong>{metrics.worker_breakdown.batch}</strong>
          </div>
        </div>

        <div className="card">
          <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--ink-muted)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
            Avg Generation Latency
          </div>
          <div style={{ fontSize: '2.2rem', fontWeight: 700, fontFamily: 'Georgia, serif' }}>
            {metrics.avg_duration_seconds}s
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--ink-muted)', marginTop: '0.25rem' }}>
            Fast turnaround target: &lt; 5.0s
          </div>
        </div>

        <div className="card">
          <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--ink-muted)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
            AWS Batch Queue
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 700, marginTop: '0.2rem' }}>
            <span className={metrics.batch_queue_state === 'ENABLED' ? 'badge badge-done' : 'badge badge-failed'}>
              {metrics.batch_queue_state}
            </span>
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--ink-muted)', marginTop: '0.5rem' }}>
            G4dn.xlarge GPU compute
          </div>
        </div>
      </div>

      {/* Recent Activity Table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid var(--line)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h3 style={{ fontSize: '1.2rem', marginBottom: '0.2rem' }}>Recent TTS Jobs</h3>
            <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--ink-muted)' }}>Latest generation requests across all sites</p>
          </div>
          <Link href="/jobs" className="button" style={{ fontSize: '0.8rem' }}>
            View All in Explorer &rarr;
          </Link>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Content Hash</th>
                <th>Status</th>
                <th>Worker Path</th>
                <th>Backend</th>
                <th>Text Excerpt</th>
                <th>Duration</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {error ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', color: '#cf1322', padding: '2rem' }}>
                    Error loading jobs: {error}
                  </td>
                </tr>
              ) : recentJobs.length === 0 && !loading ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', color: 'var(--ink-muted)', padding: '2rem' }}>
                    No generation jobs recorded yet.
                  </td>
                </tr>
              ) : (
                recentJobs.map((job) => (
                  <tr key={job.content_hash}>
                    <td className="mono" style={{ fontSize: '0.85rem' }}>
                      {job.content_hash.slice(0, 12)}...
                    </td>
                    <td>
                      <span className={`badge badge-${job.status}`}>
                        {job.status}
                      </span>
                    </td>
                    <td>
                      {job.worker_type ? (
                        <span className={`badge badge-worker-${job.worker_type}`}>
                          {job.worker_type}
                        </span>
                      ) : (
                        <span style={{ color: 'var(--ink-muted)', fontSize: '0.8rem' }}>Pending</span>
                      )}
                    </td>
                    <td style={{ textTransform: 'capitalize' }}>{job.tts_backend || 'kokoro'}</td>
                    <td style={{ maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {job.text || 'Narration excerpt'}
                    </td>
                    <td className="mono">
                      {job.duration_seconds ? `${job.duration_seconds}s` : '—'}
                    </td>
                    <td>
                      <Link href={`/jobs/detail?hash=${job.content_hash}`} className="button" style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}>
                        Inspect
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
