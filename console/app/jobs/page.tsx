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
  const [pageSize, setPageSize] = useState<number>(25);
  const [currentToken, setCurrentToken] = useState<string | undefined>(undefined);
  const [nextToken, setNextToken] = useState<string | null>(null);
  const [cursorHistory, setCursorHistory] = useState<(string | undefined)[]>([]);
  const [pageIndex, setPageIndex] = useState<number>(1);

  useEffect(() => {
    async function loadJobs() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchJobs(
          statusFilter === 'all' ? undefined : statusFilter,
          pageSize,
          currentToken
        );
        setJobs(data.jobs || []);
        setNextToken(data.next_token || null);
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : 'Failed to load jobs';
        setError(message);
        setJobs([]);
        setNextToken(null);
      } finally {
        setLoading(false);
      }
    }
    loadJobs();
  }, [statusFilter, pageSize, currentToken]);

  function handleStatusChange(newStatus: string) {
    setStatusFilter(newStatus);
    setCursorHistory([]);
    setCurrentToken(undefined);
    setPageIndex(1);
  }

  function handlePageSizeChange(newSize: number) {
    setPageSize(newSize);
    setCursorHistory([]);
    setCurrentToken(undefined);
    setPageIndex(1);
  }

  function handleNextPage() {
    if (nextToken) {
      setCursorHistory((prev) => [...prev, currentToken]);
      setCurrentToken(nextToken);
      setPageIndex((prev) => prev + 1);
    }
  }

  function handlePrevPage() {
    if (cursorHistory.length > 0) {
      const prevToken = cursorHistory[cursorHistory.length - 1];
      setCursorHistory((prev) => prev.slice(0, -1));
      setCurrentToken(prevToken);
      setPageIndex((prev) => Math.max(1, prev - 1));
    }
  }

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
            onChange={(e) => handleStatusChange(e.target.value)}
            style={{ padding: '0.5rem 0.8rem', borderRadius: '4px', border: '1px solid var(--line)', background: '#fff', fontSize: '0.875rem' }}
          >
            <option value="all">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="claimed">Claimed</option>
            <option value="done">Done</option>
            <option value="failed">Failed</option>
          </select>
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', marginBottom: '0.25rem' }}>
            Page Size
          </label>
          <select
            value={pageSize}
            onChange={(e) => handlePageSizeChange(Number(e.target.value))}
            style={{ padding: '0.5rem 0.8rem', borderRadius: '4px', border: '1px solid var(--line)', background: '#fff', fontSize: '0.875rem' }}
          >
            <option value={10}>10 per page</option>
            <option value={25}>25 per page</option>
            <option value={50}>50 per page</option>
            <option value={100}>100 per page</option>
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
            placeholder="Search content hash or excerpt on current page..."
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
                        {job.worker_type === 'batch' ? 'AWS Batch' : 'Local'}
                      </span>
                    ) : job.status === 'done' ? (
                      <span style={{ color: 'var(--ink-muted)', fontSize: '0.8rem' }}>—</span>
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

        {/* Pagination Controls Footer */}
        <div style={{ padding: '0.85rem 1.25rem', borderTop: '1px solid var(--line)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#faf8f5', flexWrap: 'wrap', gap: '0.75rem' }}>
          <div style={{ fontSize: '0.875rem', color: 'var(--ink-muted)' }}>
            Showing <strong>{filtered.length}</strong> jobs (Page {pageIndex})
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <button
              onClick={handlePrevPage}
              disabled={pageIndex === 1 || loading}
              className="button"
              style={{ fontSize: '0.8rem', padding: '0.35rem 0.75rem', cursor: pageIndex === 1 ? 'not-allowed' : 'pointer', opacity: pageIndex === 1 ? 0.5 : 1 }}
            >
              &larr; Previous
            </button>
            <span style={{ fontSize: '0.85rem', fontWeight: 600, padding: '0 0.5rem' }}>
              Page {pageIndex}
            </span>
            <button
              onClick={handleNextPage}
              disabled={!nextToken || loading}
              className="button"
              style={{ fontSize: '0.8rem', padding: '0.35rem 0.75rem', cursor: !nextToken ? 'not-allowed' : 'pointer', opacity: !nextToken ? 0.5 : 1 }}
            >
              Next &rarr;
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
