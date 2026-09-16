'use client';

import React, { useEffect, useState } from 'react';
import { fetchSites, createSite, revokeSite, Site, CreatedSite } from '../../lib/api';
import { formatEmbedSnippet } from '../../lib/embed';

export default function SitesPage() {
  const [sites, setSites] = useState<Site[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [creatingLabel, setCreatingLabel] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [createdSite, setCreatedSite] = useState<CreatedSite | null>(null);
  const [copyFeedback, setCopyFeedback] = useState<string | null>(null);

  // Load sites on mount
  useEffect(() => {
    async function loadSites() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchSites();
        setSites(data);
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : 'Failed to load sites';
        setError(message);
        setSites([]);
      } finally {
        setLoading(false);
      }
    }
    loadSites();
  }, []);

  const handleCreateSite = async (e: React.FormEvent) => {
    e.preventDefault();
    const label = creatingLabel.trim();
    if (!label) {
      setError('Label is required');
      return;
    }

    setIsCreating(true);
    setError(null);
    setCreatedSite(null);

    try {
      const newSite = await createSite(label);
      setCreatedSite(newSite);
      setCreatingLabel('');
      // Add to list if not already there
      setSites((prev) => [newSite, ...prev]);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to create site';
      setError(message);
    } finally {
      setIsCreating(false);
    }
  };

  const handleCopySnippet = async () => {
    if (!createdSite) return;
    const snippet = formatEmbedSnippet({
      siteKey: createdSite.site_key,
      scriptSrc: 'https://aurit.us/embed.js',
    });
    try {
      await navigator.clipboard.writeText(snippet);
      setCopyFeedback('Copied to clipboard!');
      setTimeout(() => setCopyFeedback(null), 2000);
    } catch (err) {
      setCopyFeedback('Failed to copy');
      setTimeout(() => setCopyFeedback(null), 2000);
    }
  };

  const handleRevokeSite = async (siteId: string) => {
    if (!window.confirm('Are you sure you want to revoke this site? This action cannot be undone.')) {
      return;
    }

    try {
      await revokeSite(siteId);
      setSites((prev) => prev.filter((site) => site.site_id !== siteId));
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to revoke site';
      setError(message);
    }
  };

  const dismissCreatedSite = () => {
    setCreatedSite(null);
  };

  return (
    <div className="console-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '1.5rem' }}>
        <div>
          <h1 style={{ fontSize: '2rem', marginBottom: '0.4rem' }}>Site Keys</h1>
          <p style={{ color: 'var(--ink-muted)' }}>Manage embed site keys for publishing Auritus clips on your sites.</p>
        </div>
      </div>

      {/* Create Site Form */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ marginTop: 0, marginBottom: '1rem' }}>Create New Site Key</h3>
        <form onSubmit={handleCreateSite} style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-end', flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: '250px' }}>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', marginBottom: '0.25rem' }}>
              Site Label
            </label>
            <input
              type="text"
              value={creatingLabel}
              onChange={(e) => setCreatingLabel(e.target.value)}
              placeholder="e.g., Example Site, My Blog"
              style={{ width: '100%', padding: '0.5rem 0.8rem', borderRadius: '4px', border: '1px solid var(--line)', background: '#fff', fontSize: '0.875rem' }}
              disabled={isCreating}
            />
          </div>
          <button
            type="submit"
            className="button button-primary"
            style={{ fontSize: '0.8rem', padding: '0.35rem 1rem', cursor: isCreating ? 'not-allowed' : 'pointer', opacity: isCreating ? 0.6 : 1 }}
            disabled={isCreating}
          >
            {isCreating ? 'Creating...' : 'Create Site Key'}
          </button>
        </form>
      </div>

      {/* Success Message with Created Site Details */}
      {createdSite && (
        <div className="card" style={{ marginBottom: '1.5rem', borderLeft: '4px solid var(--success)', background: 'var(--success-bg)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <h3 style={{ marginTop: 0, marginBottom: '0.5rem', color: 'var(--success)' }}>Site Key Created Successfully</h3>
              <p style={{ fontSize: '0.875rem', color: 'var(--ink-muted)', marginBottom: '0.75rem' }}>
                Site ID: <span className="mono" style={{ fontSize: '0.8rem', background: '#fff', padding: '0.2rem 0.4rem', borderRadius: '3px' }}>{createdSite.site_id}</span>
              </p>
              <p style={{ fontSize: '0.75rem', marginBottom: '1rem', color: 'var(--ink-muted)', fontWeight: 600 }}>
                Save this site key now — it will not be shown again!
              </p>
              <div style={{ background: '#fff', padding: '0.8rem', borderRadius: '3px', marginBottom: '0.8rem', overflow: 'auto' }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', marginBottom: '0.5rem', color: 'var(--ink-muted)' }}>
                  Site Key
                </div>
                <div className="mono" style={{ fontSize: '0.8rem', wordBreak: 'break-all', fontWeight: 600 }}>
                  {createdSite.site_key}
                </div>
              </div>
              <div style={{ background: '#fff', padding: '0.8rem', borderRadius: '3px', marginBottom: '0.8rem', overflow: 'auto', maxHeight: '200px' }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', marginBottom: '0.5rem', color: 'var(--ink-muted)' }}>
                  Embed Snippet
                </div>
                <pre className="mono" style={{ fontSize: '0.75rem', margin: 0, whiteSpace: 'pre-wrap', wordWrap: 'break-word' }}>
                  {formatEmbedSnippet({ siteKey: createdSite.site_key, scriptSrc: 'https://aurit.us/embed.js' })}
                </pre>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                <button onClick={handleCopySnippet} className="button" style={{ fontSize: '0.75rem', padding: '0.35rem 0.75rem' }}>
                  Copy Snippet
                </button>
                {copyFeedback && <span style={{ fontSize: '0.8rem', color: 'var(--success)', alignSelf: 'center' }}>{copyFeedback}</span>}
              </div>
            </div>
            <button
              onClick={dismissCreatedSite}
              style={{ background: 'none', border: 'none', fontSize: '1.5rem', cursor: 'pointer', color: 'var(--ink-muted)', padding: '0.25rem' }}
            >
              ×
            </button>
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="card" style={{ marginBottom: '1.5rem', borderLeft: '4px solid var(--danger)', background: 'var(--danger-bg)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <h3 style={{ marginTop: 0, marginBottom: '0.5rem', color: 'var(--danger)' }}>Error</h3>
              <p style={{ fontSize: '0.875rem', color: 'var(--danger)', margin: 0 }}>{error}</p>
            </div>
            <button
              onClick={() => setError(null)}
              style={{ background: 'none', border: 'none', fontSize: '1.5rem', cursor: 'pointer', color: 'var(--danger)', padding: '0.25rem' }}
            >
              ×
            </button>
          </div>
        </div>
      )}

      {/* Sites List */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Site ID</th>
              <th>Label</th>
              <th>Created At</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {error && !sites.length ? (
              <tr>
                <td colSpan={5} style={{ textAlign: 'center', padding: '2.5rem', color: 'var(--danger)' }}>
                  Error loading sites: {error}
                </td>
              </tr>
            ) : sites.length === 0 ? (
              <tr>
                <td colSpan={5} style={{ textAlign: 'center', padding: '2.5rem', color: 'var(--ink-muted)' }}>
                  {loading ? 'Loading sites...' : 'No sites yet. Create one above to get started.'}
                </td>
              </tr>
            ) : (
              sites.map((site) => (
                <tr key={site.site_id}>
                  <td className="mono" style={{ fontSize: '0.85rem' }}>
                    {site.site_id.slice(0, 12)}...
                  </td>
                  <td>{site.label}</td>
                  <td style={{ fontSize: '0.875rem', color: 'var(--ink-muted)' }}>
                    {new Date(site.created_at).toLocaleString('en-US', {
                      year: 'numeric',
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </td>
                  <td>
                    <span className={`badge badge-${site.disabled ? 'disabled' : 'active'}`}>
                      {site.disabled ? 'Disabled' : 'Active'}
                    </span>
                  </td>
                  <td>
                    <button
                      onClick={() => handleRevokeSite(site.site_id)}
                      className="button"
                      style={{ fontSize: '0.75rem', padding: '0.3rem 0.6rem', background: 'var(--danger-bg)', color: 'var(--danger)', border: '1px solid rgba(148, 60, 46, 0.3)' }}
                    >
                      Revoke
                    </button>
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
