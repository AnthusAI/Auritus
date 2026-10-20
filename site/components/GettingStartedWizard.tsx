'use client';

import React, { useState } from 'react';
import Link from 'next/link';

interface AuthOption {
  id: 'cognito' | 'google' | 'identity-center';
  name: string;
  badge: string;
  tagline: string;
  bestFor: string;
  pros: string[];
  docLink: string;
  cliCommand: string;
  setupSteps: string[];
}

interface ModelOption {
  id: 'kokoro' | 'qwen' | 'higgs';
  name: string;
  voice: string;
  license: string;
  footprint: string;
  hardware: string;
  docLink: string;
}

const AUTH_OPTIONS: AuthOption[] = [
  {
    id: 'cognito',
    name: 'Native Cognito',
    badge: 'Built-in / Simple',
    tagline: 'Self-contained inside your AWS account without any external identity provider.',
    bestFor: 'Individual operators, dev/test deployments, or teams who prefer zero external dependencies.',
    pros: [
      'Zero external IAM or OAuth setup',
      'Cognito User Pool holds credentials directly',
      'No browser flow required for automated scripts',
    ],
    docLink: '/docs/security#cognito',
    cliCommand: 'auritus login --username <email>',
    setupSteps: [
      'Deploy the backend stack with CDK (provisions Cognito User Pool automatically).',
      'Create an operator user in Cognito via AWS CLI or Cognito Console.',
      'Authenticate on your local desk using `auritus login --username <email>`.',
    ],
  },
  {
    id: 'google',
    name: 'Google Workspace',
    badge: 'Popular / SSO',
    tagline: 'Federate operator sign-in with your Google Workspace directory via Google Cloud OAuth.',
    bestFor: 'Organizations using Google for corporate SSO, MFA, and centralized offboarding.',
    pros: [
      'One-click sign-in with Google account',
      'Inherits corporate Google MFA & password rules',
      'Immediate offboarding upon Google account suspension',
    ],
    docLink: '/docs/security/google-workspace',
    cliCommand: 'auritus login --sso google',
    setupSteps: [
      'In Google Cloud Console, create an OAuth 2.0 Client ID (Web Application).',
      'Authorized JavaScript origins: `https://<cognito-domain-prefix>.auth.<region>.amazoncognito.com` and `http://localhost:3000`.',
      'Authorized redirect URIs: `https://<cognito-domain-prefix>.auth.<region>.amazoncognito.com/oauth2/idpresponse` (exact path required).',
      'Store client_id and client_secret in AWS Secrets Manager under auritus/google-oauth.',
      'Authenticate with `auritus login --sso google` or through the Web Console.',
    ],
  },
  {
    id: 'identity-center',
    name: 'AWS IAM Identity Center',
    badge: 'Enterprise SAML 2.0',
    tagline: 'Enterprise SSO federation connecting directly to AWS Identity Center, Okta, Entra ID, or Ping.',
    bestFor: 'Enterprise environments requiring SAML 2.0 directory federation and compliance auditing.',
    pros: [
      'SAML 2.0 federation into Cognito User Pool',
      'Direct integration with AWS SSO / IAM Identity Center',
      'Central audit logs of operator session creation',
    ],
    docLink: '/docs/security#identity-center',
    cliCommand: 'auritus login --sso aws-sso',
    setupSteps: [
      'In AWS IAM Identity Center, create a Customer Managed SAML 2.0 Application.',
      'Set ACS URL to `https://<cognito-domain>.auth.<region>.amazoncognito.com/saml2/idpresponse`.',
      'Pass the SAML metadata XML or URL as CDK context (`-c saml_metadata_url=...`) during deploy.',
      'Authenticate with `auritus login --sso aws-sso`.',
    ],
  },
];

const MODEL_OPTIONS: ModelOption[] = [
  {
    id: 'kokoro',
    name: 'Kokoro-82M',
    voice: 'af_heart',
    license: 'Apache 2.0',
    footprint: '82M params',
    hardware: 'Apple Silicon (MLX), CPU, or Cloud GPU',
    docLink: '/examples/basic',
  },
  {
    id: 'qwen',
    name: 'Qwen3-TTS',
    voice: 'Ryan',
    license: 'Apache 2.0',
    footprint: '1.7B params',
    hardware: 'NVIDIA GPU (CUDA) or AWS Batch fallback',
    docLink: '/examples/qwen',
  },
  {
    id: 'higgs',
    name: 'Higgs Audio v3',
    voice: 'default',
    license: 'Non-commercial research',
    footprint: '4B params',
    hardware: 'Apple Silicon (MLX) or NVIDIA GPU (CUDA)',
    docLink: '/docs/architecture',
  },
];

export default function GettingStartedWizard() {
  const [selectedAuth, setSelectedAuth] = useState<AuthOption['id']>('cognito');
  const [selectedModel, setSelectedModel] = useState<ModelOption['id']>('kokoro');
  const [siteKey, setSiteKey] = useState('demo-site-key');

  const activeAuth = AUTH_OPTIONS.find((o) => o.id === selectedAuth) || AUTH_OPTIONS[0];
  const activeModel = MODEL_OPTIONS.find((m) => m.id === selectedModel) || MODEL_OPTIONS[0];

  return (
    <div className="wizard-container">
      {/* Step Navigation Breadcrumb */}
      <nav className="wizard-stepper" aria-label="Getting started steps">
        <div className="stepper-step active">
          <span className="step-num">1</span>
          <span className="step-text">Deploy CDK</span>
        </div>
        <div className="stepper-divider" />
        <div className={`stepper-step active`}>
          <span className="step-num">2</span>
          <span className="step-text">Authentication</span>
        </div>
        <div className="stepper-divider" />
        <div className={`stepper-step active`}>
          <span className="step-num">3</span>
          <span className="step-text">Voice Model</span>
        </div>
        <div className="stepper-divider" />
        <div className={`stepper-step active`}>
          <span className="step-num">4</span>
          <span className="step-text">Embed Snippet</span>
        </div>
      </nav>

      {/* STEP 1: Deploy CDK Backend */}
      <section className="wizard-section">
        <div className="section-badge">Step 1: Deploy Backend</div>
        <h2 className="section-heading">Deploy your private cloud resources</h2>
        <p className="section-subtext">
          Auritus runs inside your AWS account with no standing third-party access. AWS CDK boots DynamoDB, API Gateway,
          Cognito User Pool, and the AWS Batch GPU fallback.
        </p>
        <div className="code-card">
          <div className="code-header">Terminal</div>
          <pre className="code-body">
            <code>{`# Clone and install dependencies
git clone https://github.com/AnthusAI/Auritus.git
cd Auritus

# Deploy backend to your AWS account
auritus deploy --region us-east-1`}</code>
          </pre>
        </div>
      </section>

      {/* STEP 2: Choose Workforce Authentication */}
      <section className="wizard-section">
        <div className="section-badge">Step 2: Operator Identity</div>
        <h2 className="section-heading">Choose your authentication method</h2>
        <p className="section-subtext">
          Select an identity provider. Selecting an option smoothly slides in the specific configuration steps and CLI login command.
        </p>

        {/* Side-by-side Apple Store style option cards */}
        <div className="option-deck" role="radiogroup" aria-label="Operator authentication choice">
          {AUTH_OPTIONS.map((opt) => {
            const isSelected = selectedAuth === opt.id;
            return (
              <button
                key={opt.id}
                role="radio"
                aria-checked={isSelected}
                onClick={() => setSelectedAuth(opt.id)}
                className={`option-card ${isSelected ? 'option-card-selected' : ''}`}
              >
                <div className="card-top">
                  <span className="badge">{opt.badge}</span>
                  <div className={`selection-indicator ${isSelected ? 'selected' : ''}`} />
                </div>
                <h3 className="card-title">{opt.name}</h3>
                <p className="card-tagline">{opt.tagline}</p>
                <div className="card-best-for">
                  <strong>Best for:</strong> {opt.bestFor}
                </div>
              </button>
            );
          })}
        </div>

        {/* Animated Expanding Drawer for Selected Auth Choice */}
        <div className="drawer-container">
          <div className="expanded-card">
            <div className="expanded-header">
              <div>
                <span className="badge-pill">{activeAuth.name} Setup Instructions</span>
                <h4 style={{ margin: '0.4rem 0 0', fontSize: '1.25rem' }}>How to configure {activeAuth.name}</h4>
              </div>
              <Link href={activeAuth.docLink} className="button button-outline" style={{ fontSize: '0.85rem' }}>
                Full Documentation &rarr;
              </Link>
            </div>

            <div className="expanded-body">
              <div className="steps-column">
                <strong>Setup Steps:</strong>
                <ol style={{ paddingLeft: '1.2rem', margin: '0.5rem 0' }}>
                  {activeAuth.setupSteps.map((step, idx) => (
                    <li key={idx} style={{ marginBottom: '0.4rem', color: 'var(--ink)' }}>
                      {step}
                    </li>
                  ))}
                </ol>
              </div>

              <div className="command-column">
                <strong>Operator Login Command:</strong>
                <div className="code-card" style={{ marginTop: '0.4rem' }}>
                  <pre className="code-body">
                    <code>{activeAuth.cliCommand}</code>
                  </pre>
                </div>
              </div>
            </div>

            {activeAuth.id === 'google' && (
              <div style={{ marginTop: '1.25rem', paddingTop: '1.25rem', borderTop: '1px solid var(--line)' }}>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
                  <div className="code-card">
                    <div className="code-header">Authorized JavaScript origins</div>
                    <pre className="code-body">
                      <code>{`https://<cognito-domain-prefix>.auth.<region>.amazoncognito.com\nhttp://localhost:3000`}</code>
                    </pre>
                  </div>
                  <div className="code-card" style={{ border: '1px solid var(--highlight)' }}>
                    <div className="code-header" style={{ color: 'var(--highlight)', fontWeight: 700 }}>
                      Authorized redirect URIs (Required)
                    </div>
                    <pre className="code-body">
                      <code>{`https://<cognito-domain-prefix>.auth.<region>.amazoncognito.com/oauth2/idpresponse`}</code>
                    </pre>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* STEP 3: Choose Voice Model */}
      <section className="wizard-section">
        <div className="section-badge">Step 3: Speech Generation</div>
        <h2 className="section-heading">Select your default TTS model</h2>
        <p className="section-subtext">
          Compare the supported voice models side-by-side, including the license that governs the weights of each model. See docs/TTS_LICENSES.md before any commercial deployment.
        </p>

        {/* Side-by-side Model Picker */}
        <div className="option-deck" role="radiogroup" aria-label="TTS Model choice">
          {MODEL_OPTIONS.map((model) => {
            const isSelected = selectedModel === model.id;
            return (
              <div
                key={model.id}
                role="radio"
                aria-checked={isSelected}
                onClick={() => setSelectedModel(model.id)}
                className={`option-card ${isSelected ? 'option-card-selected' : ''}`}
                style={{ cursor: 'pointer' }}
              >
                <div className="card-top">
                  <span className="badge">{model.license}</span>
                  <div className={`selection-indicator ${isSelected ? 'selected' : ''}`} />
                </div>
                <h3 className="card-title">{model.name}</h3>
                <p className="card-tagline">Voice: <strong>{model.voice}</strong></p>

                <div className="specs-list">
                  <div><span>Footprint:</span> <strong>{model.footprint}</strong></div>
                  <div><span>Target:</span> <strong>{model.hardware}</strong></div>
                </div>

                <div style={{ marginTop: '0.75rem', textAlign: 'right' }}>
                  <Link href={model.docLink} className="text-link" style={{ fontSize: '0.82rem' }}>
                    View Example &rarr;
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* STEP 4: Live Dynamic Embed Builder */}
      <section className="wizard-section">
        <div className="section-badge">Step 4: Embed & Publish</div>
        <h2 className="section-heading">Embed on your website</h2>
        <p className="section-subtext">
          Here is your customized snippet dynamically configured for <strong>{activeModel.name}</strong> ({activeModel.voice}). Drop this script into any article or blog template.
        </p>

        <div style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <label style={{ fontSize: '0.85rem', fontWeight: 700, textTransform: 'uppercase' }}>
            Your Site Key:
          </label>
          <input
            type="text"
            value={siteKey}
            onChange={(e) => setSiteKey(e.target.value)}
            style={{
              padding: '0.45rem 0.75rem',
              borderRadius: '4px',
              border: '1px solid var(--line)',
              background: '#fff',
              fontSize: '0.9rem',
              fontFamily: 'monospace',
              minWidth: '220px',
            }}
          />
        </div>

        <div className="code-card">
          <div className="code-header">HTML Embed Snippet (Dynamic)</div>
          <pre className="code-body">
            <code>{`<script
  src="https://aurit.us/embed.js"
  data-auritus-site-key="${siteKey}"
  data-auritus-tts-backend="${activeModel.id}"
  data-auritus-voice="${activeModel.voice}"
  data-auritus-name="Article title"
  data-auritus-byline="By Author"
></script>`}</code>
          </pre>
        </div>

        <div style={{ marginTop: '1.5rem', display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
          <Link href="/examples/basic" className="button button-primary">
            Explore Live Examples
          </Link>
          <Link href="/docs/theming" className="button button-outline">
            Customize Player Theme
          </Link>
        </div>
      </section>
    </div>
  );
}
