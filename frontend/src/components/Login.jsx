import React from 'react';
import { SignInButton, SignUpButton } from '@clerk/clerk-react';
import { Activity, LogIn, UserPlus, Sparkles } from 'lucide-react';

export default function Login() {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      width: '100vw',
      height: '100vh',
      backgroundColor: '#08080b',
      backgroundImage: 'radial-gradient(circle at top right, rgba(99, 110, 250, 0.08), transparent 40%)'
    }}>
      <div style={{
        width: '400px',
        padding: '3rem 2.5rem',
        textAlign: 'center',
        background: 'rgba(20, 20, 26, 0.65)',
        backdropFilter: 'blur(12px)',
        border: '1px solid #222230',
        borderRadius: '16px',
        boxShadow: '0 10px 30px rgba(0, 0, 0, 0.5)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '1.75rem',
        boxSizing: 'border-box'
      }}>
        {/* App Title Head */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <div style={{
            width: '48px',
            height: '48px',
            borderRadius: '12px',
            backgroundColor: 'rgba(99, 110, 250, 0.15)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: '0.75rem',
            border: '1px solid rgba(99, 110, 250, 0.25)'
          }}>
            <Activity className="logo-icon pulse" style={{ width: '26px', height: '26px', color: '#636efa' }} />
          </div>
          <h2 className="app-title" style={{ fontSize: '1.85rem', fontWeight: 800, color: 'white', letterSpacing: '-0.02em' }}>Datly</h2>
          <p style={{ fontSize: '0.75rem', color: '#a0aec0', textTransform: 'uppercase', letterSpacing: '0.05em', marginTop: '0.2rem', fontWeight: 600 }}>
            Talk to Your Data.
          </p>
        </div>

        {/* Info */}
        <p style={{ fontSize: '0.82rem', color: '#a0aec0', lineHeight: '1.5', margin: '0 0.5rem' }}>
          Welcome to the secure analytics portal. Connect your local datasets, execute natural language queries, and visualize patterns.
        </p>

        {/* Separated Sign In & Sign Up Modal Buttons */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem', width: '100%' }}>
          <SignInButton mode="modal">
            <button className="btn btn-primary" style={{ width: '100%', padding: '0.8rem', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', cursor: 'pointer', border: 'none' }}>
              <LogIn size={15} />
              Sign In to Account
            </button>
          </SignInButton>

          <SignUpButton mode="modal">
            <button className="btn btn-secondary" style={{ width: '100%', padding: '0.8rem', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', cursor: 'pointer', border: '1px solid #222230', backgroundColor: '#14141a' }}>
              <UserPlus size={15} />
              Register New Account
            </button>
          </SignUpButton>
        </div>

        {/* Bottom Metadata */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: '#64748b', fontSize: '0.65rem', textTransform: 'uppercase', letterSpacing: '0.05em', marginTop: '0.5rem' }}>
          <Sparkles size={11} style={{ color: '#636efa' }} />
          Isolated User Datasets Enabled
        </div>
      </div>
    </div>
  );
}
