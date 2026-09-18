'use client';

import React from 'react';

export interface DonutSegment {
  label: string;
  value: number;
  color: string;
  testId?: string;
}

interface DonutChartProps {
  segments: DonutSegment[];
  size?: number;
  strokeWidth?: number;
  centerLabel?: string;
  centerSublabel?: string;
}

export function DonutChart({
  segments,
  size = 140,
  strokeWidth = 20,
  centerLabel,
  centerSublabel,
}: DonutChartProps) {
  const total = segments.reduce((sum, s) => sum + s.value, 0);
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const center = size / 2;

  let cumulative = 0;

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem', flexWrap: 'wrap' }}>
      <div style={{ position: 'relative', width: size, height: size, flexShrink: 0 }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          {total === 0 ? (
            <circle
              cx={center}
              cy={center}
              r={radius}
              fill="none"
              stroke="var(--line)"
              strokeWidth={strokeWidth}
            />
          ) : (
            segments.map((segment) => {
              const fraction = segment.value / total;
              const dashLength = fraction * circumference;
              const offset = -cumulative * circumference;
              cumulative += fraction;
              return (
                <circle
                  key={segment.label}
                  cx={center}
                  cy={center}
                  r={radius}
                  fill="none"
                  stroke={segment.color}
                  strokeWidth={strokeWidth}
                  strokeDasharray={`${dashLength} ${circumference - dashLength}`}
                  strokeDashoffset={offset}
                  transform={`rotate(-90 ${center} ${center})`}
                />
              );
            })
          )}
        </svg>
        {(centerLabel || centerSublabel) && (
          <div
            style={{
              position: 'absolute',
              inset: 0,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              textAlign: 'center',
            }}
          >
            {centerLabel && (
              <div style={{ fontSize: '1.3rem', fontWeight: 700, fontFamily: 'Georgia, serif' }}>
                {centerLabel}
              </div>
            )}
            {centerSublabel && (
              <div style={{ fontSize: '0.7rem', color: 'var(--ink-muted)' }}>{centerSublabel}</div>
            )}
          </div>
        )}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
        {segments.map((segment) => (
          <div key={segment.label} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem' }}>
            <span
              style={{
                display: 'inline-block',
                width: '0.7rem',
                height: '0.7rem',
                borderRadius: '50%',
                background: segment.color,
                flexShrink: 0,
              }}
            />
            <span style={{ color: 'var(--ink-muted)' }}>{segment.label}:</span>
            <strong data-testid={segment.testId}>{segment.value}</strong>
          </div>
        ))}
      </div>
    </div>
  );
}
