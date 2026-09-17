'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { fetchOverview, fetchJobs, fetchCosts, OverviewMetrics, JobSummary, CostSummary } from '../lib/api';
import { DonutChart } from '../components/DonutChart';

type RangePreset = 'today' | '7d' | '30d' | 'custom';

function isoDate(d: Date): string {
  return d.toISOString().slice(0, 10);
}

function getRangeForPreset(
  preset: RangePreset,
  customStart: string,
  customEnd: string
): { from: string; to: string } | null {
  const today = new Date();
  if (preset === 'today') {
    const t = isoDate(today);
    return { from: t, to: t };
  }
  if (preset === '7d') {
    const start = new Date(today);
    start.setDate(start.getDate() - 6);
    return { from: isoDate(start), to: isoDate(today) };
  }
  if (preset === '30d') {
    const start = new Date(today);
    start.setDate(start.getDate() - 29);
    return { from: isoDate(start), to: isoDate(today) };
  }
  // custom
  if (customStart && customEnd && customStart <= customEnd) {
    return { from: customStart, to: customEnd };
  }
  return null;
}

export default function DashboardOverviewPage() {
  const [metrics, setMetrics] = useState<OverviewMetrics>({
    counts: { pending: 0, claimed: 0, done: 0, failed: 0 },
    worker_breakdown: { local: 0, batch: 0 },
    avg_duration_seconds: 0,
    batch_queue_state: 'UNKNOWN',
    total_sampled_jobs: 0,
  });
  const [costs, setCosts] = useState<CostSummary>({ daily: [], total: { gpu_cost_usd: 0, platform_cost_usd: 0, avoided_cost_usd: 0, batch_job_count: 0, local_job_count: 0, billed_seconds: 0, local_duration_seconds: 0 } });
  const [recentJobs, setRecentJobs] = useState<JobSummary[]>([]);
  const [loadingSnapshot, setLoadingSnapshot] = useState(true);
  const [loadingRange, setLoadingRange] = useState(true);
  const [snapshotError, setSnapshotError] = useState<string | null>(null);
  const [rangeError, setRangeError] = useState<string | null>(null);

  const [preset, setPreset] = useState<RangePreset>('today');
  const [customStart, setCustomStart] = useState('');
  const [customEnd, setCustomEnd] = useState('');

  const range = getRangeForPreset(preset, customStart, customEnd);

  // "Right now" live snapshot -- unscoped, mount-only. GET /admin/overview
  // has no date concept (it computes off a capped scan(Limit=100), the same
  // defect class as auritus-294fa6), so it is deliberately never re-fetched
  // on range change.
  useEffect(() => {
    async function loadSnapshot() {
      setLoadingSnapshot(true);
      setSnapshotError(null);
      try {
        const [overviewData, jobsData] = await Promise.all([fetchOverview(), fetchJobs()]);
        if (overviewData) setMetrics(overviewData);
        if (jobsData?.jobs) setRecentJobs(jobsData.jobs.slice(0, 8));
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : 'Failed to load dashboard data';
        setSnapshotError(message);
      } finally {
        setLoadingSnapshot(false);
      }
    }
    loadSnapshot();
  }, []);

  // Range-scoped aggregates -- refetches whenever the selected date range
  // changes. Backed by /admin/costs, which already supports from/to over
  // the pre-aggregated AuritusCostRollups table.
  useEffect(() => {
    if (!range) return;
    async function loadRange() {
      setLoadingRange(true);
      setRangeError(null);
      try {
        const costsData = await fetchCosts(undefined, range!.from, range!.to);
        if (costsData) setCosts(costsData);
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : 'Failed to load cost data';
        setRangeError(message);
      } finally {
        setLoadingRange(false);
      }
    }
    loadRange();
  }, [range?.from, range?.to]);

  const error = snapshotError || rangeError;
  const loading = loadingSnapshot || loadingRange;

  // Completed Jobs and the Local/Cloud split are deliberately derived from
  // the cost rollup (costs.total), not metrics.counts.done /
  // metrics.worker_breakdown -- this makes them date-range-aware and avoids
  // the unscoped-scan reliability trap, at the cost of counting "jobs that
  // contributed a rollup" rather than literally every status=done row.
  const totalCompleted = costs.total.local_job_count + costs.total.batch_job_count;
  const localRatio =
    totalCompleted > 0 ? Math.round((costs.total.local_job_count / totalCompleted) * 100) : 100;

  const formatUSD = (value: number) => {
    return `$${value.toFixed(4)}`;
  };

  return (
    <div className="console-container">
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>System Observability & Monitoring</h1>
        <p style={{ color: 'var(--ink-muted)' }}>
          Real-time metrics for just-in-time TTS generation, worker race performance, and cloud fallback health.
        </p>
      </div>

      {error && (
        <div className="card" style={{ marginBottom: '1.5rem', background: '#fff1f0', borderColor: '#ffa39e', color: '#cf1322' }}>
          <strong>Error loading dashboard:</strong> {error}
        </div>
      )}

      {/* Right now: live snapshot, not scoped to the selected date range */}
      <div style={{ marginBottom: '0.75rem' }}>
        <h2 style={{ fontSize: '1rem', marginBottom: '0.1rem' }}>Right now</h2>
        <p style={{ fontSize: '0.8rem', color: 'var(--ink-muted)', margin: 0 }}>
          Live snapshot — not scoped to the selected date range below.
        </p>
      </div>
      <div
        data-testid="section-live-snapshot"
        style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '1rem', marginBottom: '2rem' }}
      >
        <div className="card">
          <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--ink-muted)', textTransform: 'uppercase', marginBottom: '0.4rem' }}>
            Pending
          </div>
          <div style={{ fontSize: '1.4rem', fontWeight: 700 }}>{metrics.counts.pending}</div>
        </div>

        <div className="card">
          <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--ink-muted)', textTransform: 'uppercase', marginBottom: '0.4rem' }}>
            Claimed
          </div>
          <div style={{ fontSize: '1.4rem', fontWeight: 700 }}>{metrics.counts.claimed}</div>
        </div>

        <div className="card">
          <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--ink-muted)', textTransform: 'uppercase', marginBottom: '0.4rem' }}>
            Failed
          </div>
          <div style={{ fontSize: '1.4rem', fontWeight: 700 }}>{metrics.counts.failed}</div>
        </div>

        <div className="card">
          <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--ink-muted)', textTransform: 'uppercase', marginBottom: '0.4rem' }}>
            Avg Generation Latency
          </div>
          <div style={{ fontSize: '1.4rem', fontWeight: 700 }}>{metrics.avg_duration_seconds}s</div>
        </div>

        <div className="card">
          <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--ink-muted)', textTransform: 'uppercase', marginBottom: '0.4rem' }}>
            Cloud Fallback
          </div>
          <div style={{ marginTop: '0.1rem' }}>
            <span className={metrics.batch_queue_state === 'ENABLED' ? 'badge badge-done' : 'badge badge-failed'}>
              {metrics.batch_queue_state}
            </span>
          </div>
          <div style={{ fontSize: '0.7rem', color: 'var(--ink-muted)', marginTop: '0.4rem' }}>
            G4dn.xlarge GPU compute
          </div>
        </div>
      </div>

      {/* For selected range: cost-rollup-derived aggregates */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-end',
          flexWrap: 'wrap',
          gap: '1rem',
          marginBottom: '0.75rem',
        }}
      >
        <div>
          <h2 style={{ fontSize: '1rem', marginBottom: '0.1rem' }}>For selected range</h2>
          <p style={{ fontSize: '0.8rem', color: 'var(--ink-muted)', margin: 0 }}>
            Completed jobs, worker split, and costs across sites for the chosen period.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
          {(['today', '7d', '30d', 'custom'] as RangePreset[]).map((p) => (
            <button
              key={p}
              className="button"
              onClick={() => setPreset(p)}
              style={{
                fontSize: '0.8rem',
                background: preset === p ? 'var(--accent)' : undefined,
                color: preset === p ? '#fff' : undefined,
              }}
            >
              {p === 'today' ? 'Today' : p === '7d' ? '7 days' : p === '30d' ? '30 days' : 'Custom'}
            </button>
          ))}
          {preset === 'custom' && (
            <>
              <input
                type="date"
                value={customStart}
                onChange={(e) => setCustomStart(e.target.value)}
                style={{ padding: '0.4rem 0.6rem', borderRadius: '4px', border: '1px solid var(--line)', fontSize: '0.8rem' }}
              />
              <span style={{ color: 'var(--ink-muted)' }}>to</span>
              <input
                type="date"
                value={customEnd}
                onChange={(e) => setCustomEnd(e.target.value)}
                style={{ padding: '0.4rem 0.6rem', borderRadius: '4px', border: '1px solid var(--line)', fontSize: '0.8rem' }}
              />
            </>
          )}
        </div>
      </div>

      <div
        data-testid="section-range-scoped"
        style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.25rem', marginBottom: '2rem' }}
      >
        <div className="card">
          <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--ink-muted)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
            Completed Jobs
          </div>
          <div style={{ fontSize: '2.2rem', fontWeight: 700, fontFamily: 'Georgia, serif' }}>
            {totalCompleted}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--ink-muted)', marginTop: '0.25rem' }}>
            Local + cloud, selected range
          </div>
        </div>

        <div className="card">
          <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--ink-muted)', textTransform: 'uppercase', marginBottom: '0.75rem' }}>
            Local vs Cloud
          </div>
          <DonutChart
            segments={[
              { label: 'Local', value: costs.total.local_job_count, color: 'var(--success)', testId: 'donut-local-count' },
              { label: 'Cloud', value: costs.total.batch_job_count, color: 'var(--info)', testId: 'donut-cloud-count' },
            ]}
            centerLabel={`${localRatio}%`}
            centerSublabel="Local share"
            size={110}
            strokeWidth={16}
          />
        </div>

        <Link href="/costs" style={{ textDecoration: 'none' }}>
          <div className="card" style={{ cursor: 'pointer', height: '100%', transition: 'background-color 0.2s' }} onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--panel)'} onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'var(--card)'}>
            <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--ink-muted)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
              Cloud GPU Cost
            </div>
            <div style={{ fontSize: '2.2rem', fontWeight: 700, fontFamily: 'Georgia, serif', color: 'var(--accent)' }}>
              {formatUSD(costs.total.gpu_cost_usd)}
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--ink-muted)', marginTop: '0.25rem' }}>
              Click to explore &rarr;
            </div>
          </div>
        </Link>

        <Link href="/costs" style={{ textDecoration: 'none' }}>
          <div className="card" style={{ cursor: 'pointer', height: '100%', transition: 'background-color 0.2s' }} onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--panel)'} onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'var(--card)'}>
            <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--ink-muted)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
              Saved via Local Workers
            </div>
            <div style={{ fontSize: '2.2rem', fontWeight: 700, fontFamily: 'Georgia, serif', color: 'var(--success)' }}>
              {formatUSD(costs.total.avoided_cost_usd)}
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--ink-muted)', marginTop: '0.25rem' }}>
              GPU hours avoided
            </div>
          </div>
        </Link>
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
