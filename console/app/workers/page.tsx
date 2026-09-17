'use client';

import React, { useEffect, useState } from 'react';
import { fetchOverview, toggleQueue } from '../../lib/api';

export default function WorkersPage() {
  const [queueState, setQueueState] = useState<string>('ENABLED');
  const [loading, setLoading] = useState(true);
  const [toggling, setToggling] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    async function loadStatus() {
      try {
        const data = await fetchOverview().catch(() => null);
        if (data?.batch_queue_state) {
          setQueueState(data.batch_queue_state);
        }
      } finally {
        setLoading(false);
      }
    }
    loadStatus();
  }, []);

  const handleToggle = async () => {
    setToggling(true);
    setMessage(null);
    try {
      const nextState = queueState === 'ENABLED' ? 'DISABLED' : 'ENABLED';
      const res = await toggleQueue(nextState);
      setQueueState(res.state);
      setMessage(`AWS Batch queue is now ${res.state}.`);
    } catch (err: any) {
      setMessage(`Failed to toggle queue: ${err.message}`);
    } finally {
      setToggling(false);
    }
  };

  return (
    <div className="console-container">
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2rem', marginBottom: '0.4rem' }}>Worker & Infrastructure Health</h1>
        <p style={{ color: 'var(--ink-muted)' }}>
          Monitor the dual-worker race, local GPU heartbeats, and AWS Batch fallback controls.
        </p>
      </div>

      {message && (
        <div style={{ background: 'var(--info-bg)', color: 'var(--info)', padding: '0.75rem 1rem', borderRadius: '4px', marginBottom: '1.5rem', border: '1px solid rgba(34, 92, 138, 0.2)' }}>
          {message}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
        {/* Batch Queue Control Card */}
        <div className="card">
          <h3 style={{ fontSize: '1.2rem', marginBottom: '0.5rem' }}>AWS Batch GPU Queue</h3>
          <p style={{ color: 'var(--ink-muted)', fontSize: '0.875rem', marginBottom: '1.25rem' }}>
            The cloud fallback queue executes any configured TTS backend on EC2 G4dn.xlarge GPU instances via Step Functions when local workers are unavailable.
          </p>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '1rem', background: 'var(--panel)', borderRadius: '6px', marginBottom: '1.5rem' }}>
            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--ink-muted)' }}>Queue State</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 700, marginTop: '0.2rem' }}>
                <span className={queueState === 'ENABLED' ? 'badge badge-done' : 'badge badge-failed'}>
                  {queueState}
                </span>
              </div>
            </div>
            <button
              onClick={handleToggle}
              disabled={toggling}
              className={`button ${queueState === 'ENABLED' ? 'badge-failed' : 'button-primary'}`}
              style={{ padding: '0.6rem 1rem', cursor: 'pointer' }}
            >
              {toggling
                ? 'Updating...'
                : queueState === 'ENABLED'
                ? 'Emergency Disable (Kill Switch)'
                : 'Enable Queue'}
            </button>
          </div>

          <div style={{ fontSize: '0.8rem', color: 'var(--ink-muted)', lineHeight: 1.5 }}>
            <strong>Spend Guardrail:</strong> AWS Budgets will automatically disable this queue if daily spend exceeds the \$50 USD threshold.
          </div>
        </div>

        {/* Local Worker Guide Card */}
        <div className="card">
          <h3 style={{ fontSize: '1.2rem', marginBottom: '0.5rem' }}>Local GPU Worker Fleet</h3>
          <p style={{ color: 'var(--ink-muted)', fontSize: '0.875rem', marginBottom: '1rem' }}>
            Local workers poll for claimable jobs and execute on local Apple Silicon or NVIDIA GPUs, eliminating AWS cloud compute costs.
          </p>

          <div style={{ background: '#21180f', color: '#f4eddd', padding: '1rem', borderRadius: '4px', marginBottom: '1rem' }}>
            <div style={{ color: '#aaa', fontSize: '0.75rem', marginBottom: '0.3rem' }}>CLI Command to run local worker:</div>
            <code className="mono" style={{ fontSize: '0.85rem' }}>auritus worker</code>
          </div>

          <div style={{ fontSize: '0.8rem', color: 'var(--ink-muted)', lineHeight: 1.5 }}>
            Local workers race against the Step Functions claim timer (default 900s). When a local worker claims a job, the cloud fallback cleanly terminates without running EC2 instances.
          </div>
        </div>
      </div>
    </div>
  );
}
