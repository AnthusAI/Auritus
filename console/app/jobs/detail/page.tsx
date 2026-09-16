'use client';

import React, { Suspense, useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { fetchJobDetail, JobDetail, deleteJob, regenerateJob, retryJob } from '../../../lib/api';

function JobDetailContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const hash = searchParams ? searchParams.get('hash') || '' : '';
  const [job, setJob] = useState<JobDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionPending, setActionPending] = useState(false);
  const [liveClaimConflict, setLiveClaimConflict] = useState(false);

  const loadDetail = useCallback(async () => {
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
  }, [hash, router]);

  useEffect(() => {
    loadDetail();
  }, [loadDetail]);

  const handleDelete = async () => {
    if (!window.confirm('Are you sure you want to delete this job? This action cannot be undone.')) {
      return;
    }
    setActionPending(true);
    setActionError(null);
    setLiveClaimConflict(false);
    try {
      await deleteJob(hash);
      router.push('/jobs');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setActionError(`Failed to delete job: ${errorMessage}`);
    } finally {
      setActionPending(false);
    }
  };

  const handleRegenerate = async () => {
    setActionPending(true);
    setActionError(null);
    setLiveClaimConflict(false);
    try {
      await regenerateJob(hash);
      await loadDetail();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setActionError(`Failed to regenerate job: ${errorMessage}`);
    } finally {
      setActionPending(false);
    }
  };

  const handleRetry = async (force = false) => {
    setActionPending(true);
    setActionError(null);
    setLiveClaimConflict(false);
    try {
      await retryJob(hash, force);
      await loadDetail();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      if (!force && errorMessage === 'claim_still_live') {
        setLiveClaimConflict(true);
        setActionError('This job has an active claim. Force-release to override it.');
      } else {
        setActionError(`Failed to retry job: ${errorMessage}`);
      }
    } finally {
      setActionPending(false);
    }
  };

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

      {actionError && (
        <div style={{ background: 'var(--danger-bg)', color: 'var(--danger)', padding: '0.75rem 1rem', borderRadius: '4px', marginBottom: '1.5rem', border: '1px solid rgba(148, 60, 46, 0.2)' }}>
          {actionError}
          {liveClaimConflict && (
            <div style={{ marginTop: '0.75rem' }}>
              <button
                onClick={() => handleRetry(true)}
                disabled={actionPending}
                className="button"
                style={{ padding: '0.5rem 0.75rem', background: 'var(--danger)', color: '#fff', border: 'none', marginTop: '0.5rem' }}
              >
                {actionPending ? 'Force-releasing...' : 'Force-release'}
              </button>
            </div>
          )}
        </div>
      )}

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

          {/* Action Buttons Row */}
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.25rem', flexWrap: 'wrap', alignItems: 'center' }}>
            {actionPending && <span style={{ fontSize: '0.875rem', color: 'var(--ink-muted)' }}>Processing...</span>}
            <button
              onClick={handleDelete}
              disabled={actionPending}
              className="button"
              style={{ padding: '0.5rem 0.75rem', cursor: actionPending ? 'not-allowed' : 'pointer', opacity: actionPending ? 0.6 : 1 }}
            >
              {actionPending ? 'Deleting...' : 'Delete Job'}
            </button>
            {job.status === 'done' && (
              <button
                onClick={handleRegenerate}
                disabled={actionPending}
                className="button"
                style={{ padding: '0.5rem 0.75rem', cursor: actionPending ? 'not-allowed' : 'pointer', opacity: actionPending ? 0.6 : 1 }}
              >
                {actionPending ? 'Regenerating...' : 'Regenerate'}
              </button>
            )}
            {(job.status === 'failed' || job.status === 'claimed') && (
              <button
                onClick={() => handleRetry(false)}
                disabled={actionPending || liveClaimConflict}
                className="button"
                style={{ padding: '0.5rem 0.75rem', cursor: actionPending || liveClaimConflict ? 'not-allowed' : 'pointer', opacity: actionPending || liveClaimConflict ? 0.6 : 1 }}
              >
                {actionPending ? 'Retrying...' : job.status === 'claimed' ? 'Release' : 'Retry'}
              </button>
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
