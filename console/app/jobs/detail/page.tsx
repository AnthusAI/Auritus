'use client';

import React, { Suspense, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { fetchJobDetail, JobDetail } from '../../../lib/api';

function JobDetailContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const hash = searchParams ? searchParams.get('hash') || '' : '';
  const [job, setJob] = useState<JobDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDetail() {
      if (!hash) {
        setLoading(false);
        return;
      }
      try {
        const data = await fetchJobDetail(hash);
        setJob(data);
        setError(null);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Unknown error';
        if (errorMessage === 'Unauthorized') {
          router.replace('/login');
        } else {
          setError(errorMessage);
        }
      } finally {
        setLoading(false);
      }
    }
    loadDetail();
  }, [hash, router]);

  if (loading) {
    return (
      <div className="console-container" style={{ padding: '3rem 0', textAlign: 'center' }}>
        Loading job inspection...
      </div>
    );
  }

  if (error) {
    return (
      <div className="console-container" style={{ padding: '3rem 0' }}>
        <div style={{ background: 'var(--danger-bg)', color: 'var(--danger)', padding: '1.5rem', borderRadius: '6px', marginBottom: '1.5rem' }}>
          <h2 style={{ fontSize: '1.1rem', marginBottom: '0.5rem', marginTop: 0 }}>Failed to load job details</h2>
          <p style={{ marginBottom: 0, fontSize: '0.95rem' }}>{error}</p>
        </div>
        <Link href="/jobs" className="button">
          &larr; Back to Job Explorer
        </Link>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="console-container" style={{ padding: '3rem 0' }}>
        <p>No content hash provided or job not found.</p>
        <Link href="/jobs" className="button">
          &larr; Back to Job Explorer
        </Link>
      </div>
    );
  }

  return (
    <div className="console-container">
      <div style={{ marginBottom: '1.5rem' }}>
        <Link href="/jobs" style={{ fontSize: '0.875rem', color: 'var(--accent)', fontWeight: 600 }}>
          &larr; Back to Job Explorer
        </Link>
        <h1 style={{ fontSize: '1.8rem', marginTop: '0.5rem' }}>Job Inspection</h1>
        <p className="mono" style={{ fontSize: '0.85rem', color: 'var(--ink-muted)' }}>
          {job.content_hash}
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
        {/* Left Card: Status & Narration Audio */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <span className={`badge badge-${job.status}`}>{job.status}</span>
            {job.worker_type && (
              <span className={`badge badge-worker-${job.worker_type}`}>
                {job.worker_type} worker
              </span>
            )}
          </div>

          {job.audio_url ? (
            <div style={{ background: 'var(--panel)', padding: '1.25rem', borderRadius: '6px', marginBottom: '1.25rem' }}>
              <h3 style={{ fontSize: '1rem', marginBottom: '0.5rem' }}>Generated Speech Audio</h3>
              <audio controls src={job.audio_url} style={{ width: '100%' }}>
                Your browser does not support audio playback.
              </audio>
            </div>
          ) : (
            <div style={{ padding: '1rem', background: 'var(--panel)', borderRadius: '6px', color: 'var(--ink-muted)', marginBottom: '1.25rem' }}>
              No audio artifact available ({job.status}).
            </div>
          )}

          <div>
            <h4 style={{ fontSize: '0.85rem', textTransform: 'uppercase', color: 'var(--ink-muted)', marginBottom: '0.4rem' }}>
              Extracted Text
            </h4>
            <div style={{ background: '#fff', padding: '1rem', borderRadius: '4px', border: '1px solid var(--line)', lineHeight: 1.6, maxHeight: '240px', overflowY: 'auto' }}>
              {job.text || 'No text recorded.'}
            </div>
          </div>
        </div>

        {/* Right Card: Telemetry & Timestamps */}
        <div className="card">
          <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem' }}>Execution Telemetry</h3>
          <div style={{ display: 'grid', gap: '0.75rem', fontSize: '0.9rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--line)', paddingBottom: '0.4rem' }}>
              <span style={{ color: 'var(--ink-muted)' }}>TTS Engine</span>
              <strong>{job.tts_backend || 'kokoro'}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--line)', paddingBottom: '0.4rem' }}>
              <span style={{ color: 'var(--ink-muted)' }}>Voice ID</span>
              <strong>{job.voice_id || 'af_heart'}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--line)', paddingBottom: '0.4rem' }}>
              <span style={{ color: 'var(--ink-muted)' }}>Claimed By</span>
              <strong className="mono" style={{ fontSize: '0.8rem' }}>{job.claimed_by || '—'}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--line)', paddingBottom: '0.4rem' }}>
              <span style={{ color: 'var(--ink-muted)' }}>Generation Time</span>
              <strong>{job.duration_seconds ? `${job.duration_seconds}s` : '—'}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--line)', paddingBottom: '0.4rem' }}>
              <span style={{ color: 'var(--ink-muted)' }}>Requested At</span>
              <span className="mono" style={{ fontSize: '0.8rem' }}>{job.created_at || '—'}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--line)', paddingBottom: '0.4rem' }}>
              <span style={{ color: 'var(--ink-muted)' }}>Claimed At</span>
              <span className="mono" style={{ fontSize: '0.8rem' }}>{job.claimed_at || '—'}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--line)', paddingBottom: '0.4rem' }}>
              <span style={{ color: 'var(--ink-muted)' }}>Completed At</span>
              <span className="mono" style={{ fontSize: '0.8rem' }}>{job.completed_at || '—'}</span>
            </div>
            {job.error_message && (
              <div style={{ background: 'var(--danger-bg)', color: 'var(--danger)', padding: '0.75rem', borderRadius: '4px', marginTop: '0.5rem' }}>
                <strong>Error:</strong> {job.error_message}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Raw Diagnostic JSON */}
      <div className="card">
        <h4 style={{ fontSize: '0.85rem', textTransform: 'uppercase', color: 'var(--ink-muted)', marginBottom: '0.5rem' }}>
          Diagnostic Record JSON
        </h4>
        <pre className="mono" style={{ background: '#21180f', color: '#f4eddd', padding: '1rem', borderRadius: '4px', overflowX: 'auto', fontSize: '0.8rem' }}>
          {JSON.stringify(job, null, 2)}
        </pre>
      </div>
    </div>
  );
}

export default function JobDetailPage() {
  return (
    <Suspense fallback={<div className="console-container" style={{ padding: '3rem 0', textAlign: 'center' }}>Loading job inspection...</div>}>
      <JobDetailContent />
    </Suspense>
  );
}
