'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { fetchJobs, JobSummary } from '../../lib/api';

export default function JobExplorerPage() {
  const [jobs, setJobs] = useState<JobSummary[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadJobs() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchJobs(statusFilter === 'all' ? undefined : statusFilter, 100);
        setJobs(data.jobs || []);
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : 'Failed to load jobs';
        setError(message);
        setJobs([]);
      } finally {
        setLoading(false);
      }
    }
    loadJobs();
  }, [statusFilter]);

  const filtered = jobs.filter((j) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return j.content_hash.toLowerCase().includes(q) || (j.text && j.text.toLowerCase().includes(q));
  });

  return (
    <div className="console-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '1.5rem' }}>
        <div>
          <h1 style={{ fontSize: '2rem', marginBottom: '0.4rem' }}>Job Explorer</h1>
          <p style={{ color: 'var(--ink-muted)' }}>Inspect in-flight, completed, and failed generation jobs.</p>
        </div>
      </div>

      {/* Controls / Filter Bar */}
      <div className="card" style={{ marginBottom: '1.5rem', display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
        <div>
          <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', marginBottom: '0.25rem' }}>
            Filter by Status
          </label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{ padding: '0.5rem 0.8rem', borderRadius: '4px', border: '1px solid var(--line)', background: '#fff', fontSize: '0.875rem' }}
          >
            <option value="all">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="claimed">Claimed</option>
            <option value="done">Done</option>
            <option value="failed">Failed</option>
          </select>
        </div>

        <div style={{ flex: 1, minWidth: '220px' }}>
          <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', marginBottom: '0.25rem' }}>
            Search by Hash or Text
          </label>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search content hash or excerpt..."
            style={{ width: '100%', padding: '0.5rem 0.8rem', borderRadius: '4px', border: '1px solid var(--line)', background: '#fff', fontSize: '0.875rem' }}
          />
        </div>
      </div>

      {/* Jobs Data Table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Content Hash</th>
              <th>Status</th>
              <th>Worker Attribution</th>
              <th>TTS Backend</th>
              <th>Text Excerpt</th>
              <th>Duration</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {error ? (
              <tr>
                <td colSpan={7} style={{ textAlign: 'center', padding: '2.5rem', color: '#cf1322' }}>
                  Error loading jobs: {error}
                </td>
              </tr>
            ) : filtered.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ textAlign: 'center', padding: '2.5rem', color: 'var(--ink-muted)' }}>
                  {loading ? 'Loading jobs...' : 'No matching jobs found.'}
                </td>
              </tr>
            ) : (
              filtered.map((job) => (
                <tr key={job.content_hash}>
                  <td className="mono" style={{ fontSize: '0.85rem' }}>
                    {job.content_hash.slice(0, 16)}...
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
                      <span style={{ color: 'var(--ink-muted)', fontSize: '0.8rem' }}>Unclaimed</span>
                    )}
                  </td>
                  <td style={{ textTransform: 'capitalize' }}>
                    {job.tts_backend || 'kokoro'} {job.voice_id ? `(${job.voice_id})` : ''}
                  </td>
                  <td style={{ maxWidth: '340px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {job.text || '—'}
                  </td>
                  <td className="mono">
                    {job.duration_seconds ? `${job.duration_seconds}s` : '—'}
                  </td>
                  <td>
                    <Link href={`/jobs/detail?hash=${job.content_hash}`} className="button" style={{ fontSize: '0.75rem', padding: '0.3rem 0.6rem' }}>
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
  );
}
