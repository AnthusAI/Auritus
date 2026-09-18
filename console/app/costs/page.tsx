'use client';

import React, { useEffect, useState } from 'react';
import { fetchCosts, CostSummary, DailyCost, fetchSites, Site } from '../../lib/api';

export default function CostsPage() {
  const [costs, setCosts] = useState<CostSummary>({ daily: [], total: { gpu_cost_usd: 0, platform_cost_usd: 0, avoided_cost_usd: 0, batch_job_count: 0, local_job_count: 0, billed_seconds: 0, local_duration_seconds: 0 } });
  const [sites, setSites] = useState<Site[]>([]);
  const [selectedSiteId, setSelectedSiteId] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<'date-asc' | 'date-desc'>('date-desc');

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      setError(null);
      try {
        const [costsData, sitesData] = await Promise.all([
          fetchCosts(selectedSiteId || undefined),
          fetchSites(),
        ]);
        setCosts(costsData);
        setSites(sitesData);
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : 'Failed to load costs data';
        setError(message);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [selectedSiteId]);

  const sortedDaily = [...costs.daily].sort((a, b) => {
    if (sortBy === 'date-asc') {
      return new Date(a.date).getTime() - new Date(b.date).getTime();
    } else {
      return new Date(b.date).getTime() - new Date(a.date).getTime();
    }
  });

  const formatUSD = (value: number) => {
    return `$${value.toFixed(4)}`;
  };

  return (
    <div className="console-container">
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>Cost Analysis</h1>
        <p style={{ color: 'var(--ink-muted)' }}>
          Modelled cost estimates for GPU, platform services, and avoided costs via local workers.
        </p>
        <p style={{ fontSize: '0.85rem', color: 'var(--ink-muted)', marginTop: '0.5rem', fontStyle: 'italic' }}>
          ℹ️ These are modelled estimates based on rate cards, not an AWS invoice. Actual billing may differ.
        </p>
      </div>

      {error && (
        <div className="card" style={{ marginBottom: '1.5rem', background: 'var(--danger-bg)', borderColor: 'var(--danger)', color: 'var(--danger)' }}>
          <strong>Error loading costs:</strong> {error}
        </div>
      )}

      {loading ? (
        <div className="card" style={{ textAlign: 'center', padding: '2rem', color: 'var(--ink-muted)' }}>
          Loading cost data...
        </div>
      ) : error ? null : (
        <>
          {/* Summary Tiles */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.25rem', marginBottom: '2rem' }}>
            <div className="card">
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--ink-muted)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
                Total GPU Cost
              </div>
              <div style={{ fontSize: '2.2rem', fontWeight: 700, fontFamily: 'Georgia, serif', color: 'var(--accent)' }}>
                {formatUSD(costs.total.gpu_cost_usd)}
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--ink-muted)', marginTop: '0.25rem' }}>
                Cloud job GPU hours
              </div>
            </div>

            <div className="card">
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--ink-muted)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
                Total Platform Cost
              </div>
              <div style={{ fontSize: '2.2rem', fontWeight: 700, fontFamily: 'Georgia, serif', color: 'var(--signal)' }}>
                {formatUSD(costs.total.platform_cost_usd)}
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--ink-muted)', marginTop: '0.25rem' }}>
                API & infrastructure
              </div>
            </div>

            <div className="card">
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--ink-muted)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
                Avoided Cost (Local Workers)
              </div>
              <div style={{ fontSize: '2.2rem', fontWeight: 700, fontFamily: 'Georgia, serif', color: 'var(--success)' }}>
                {formatUSD(costs.total.avoided_cost_usd)}
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--ink-muted)', marginTop: '0.25rem' }}>
                GPU hours saved
              </div>
            </div>
          </div>

          {/* Filters */}
          <div className="card" style={{ marginBottom: '1.5rem' }}>
            <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--ink-muted)', textTransform: 'uppercase', marginBottom: '0.3rem' }}>
                  Filter by Site
                </label>
                <select
                  value={selectedSiteId}
                  onChange={(e) => setSelectedSiteId(e.target.value)}
                  style={{
                    padding: '0.5rem 0.75rem',
                    borderRadius: '4px',
                    border: '1px solid var(--line)',
                    background: '#fff',
                    color: 'var(--ink)',
                    fontSize: '0.875rem',
                  }}
                >
                  <option value="">All Sites</option>
                  {sites.map((site) => (
                    <option key={site.site_id} value={site.site_id}>
                      {site.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Daily Costs Table */}
          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid var(--line)' }}>
              <h3 style={{ fontSize: '1.2rem', marginBottom: '0.2rem' }}>Daily Cost Breakdown</h3>
              <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--ink-muted)' }}>
                Detailed daily cost rollups across all tracked metrics
              </p>
            </div>

            {costs.daily.length === 0 ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--ink-muted)' }}>
                No cost data available for the selected filters.
              </div>
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th style={{ cursor: 'pointer' }} onClick={() => setSortBy(sortBy === 'date-asc' ? 'date-desc' : 'date-asc')}>
                        Date {sortBy === 'date-asc' ? '↑' : '↓'}
                      </th>
                      {selectedSiteId === '' && <th>Site ID</th>}
                      <th>GPU Cost</th>
                      <th>Platform Cost</th>
                      <th>Avoided Cost</th>
                      <th>Cloud Jobs</th>
                      <th>Local Jobs</th>
                      <th>Billed Seconds</th>
                      <th>Local Seconds</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sortedDaily.map((day, index) => (
                      <tr key={`${day.site_id}-${day.date}-${index}`}>
                        <td className="mono" style={{ fontSize: '0.85rem' }}>
                          {new Date(day.date).toLocaleDateString()}
                        </td>
                        {selectedSiteId === '' && <td className="mono" style={{ fontSize: '0.85rem' }}>{day.site_id}</td>}
                        <td>{formatUSD(day.gpu_cost_usd)}</td>
                        <td>{formatUSD(day.platform_cost_usd)}</td>
                        <td style={{ color: 'var(--success)', fontWeight: 600 }}>{formatUSD(day.avoided_cost_usd)}</td>
                        <td style={{ textAlign: 'right' }}>{day.batch_job_count}</td>
                        <td style={{ textAlign: 'right' }}>{day.local_job_count}</td>
                        <td style={{ textAlign: 'right', fontSize: '0.85rem' }} className="mono">
                          {day.billed_seconds.toFixed(0)}s
                        </td>
                        <td style={{ textAlign: 'right', fontSize: '0.85rem' }} className="mono">
                          {day.local_duration_seconds.toFixed(0)}s
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
          {/* Reconciliation vs. actual AWS bill: account-wide only (Cost
              Explorer has no per-site attribution), so this only ever has
              data for the "all sites" view. */}
          {selectedSiteId === '' && costs.reconciliation && costs.reconciliation.length > 0 && (
            <div className="card" style={{ padding: 0, overflow: 'hidden', marginTop: '1.5rem' }}>
              <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid var(--line)' }}>
                <h3 style={{ fontSize: '1.2rem', marginBottom: '0.2rem' }}>Reconciliation vs. Actual AWS Bill</h3>
                <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--ink-muted)' }}>
                  Account-wide GPU cost estimate vs. actual AWS Cost Explorer spend (Batch/EC2 only). Cost Explorer cannot attribute spend to a single site.
                </p>
              </div>
              <div style={{ overflowX: 'auto' }}>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Estimated GPU Cost</th>
                      <th>Actual Cost</th>
                      <th>Variance</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {costs.reconciliation.map((row) => (
                      <tr key={row.date}>
                        <td className="mono" style={{ fontSize: '0.85rem' }}>
                          {new Date(row.date).toLocaleDateString()}
                        </td>
                        <td>{formatUSD(row.estimated_gpu_cost_usd)}</td>
                        <td>{formatUSD(row.actual_cost_usd)}</td>
                        <td style={{ color: row.out_of_tolerance ? 'var(--danger)' : 'var(--ink)' }}>
                          {formatUSD(row.variance_usd)}
                        </td>
                        <td>
                          {row.out_of_tolerance ? (
                            <span style={{ color: 'var(--danger)', fontWeight: 600 }}>Out of tolerance</span>
                          ) : (
                            <span style={{ color: 'var(--success)' }}>Within tolerance</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
