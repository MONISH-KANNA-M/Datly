import React from 'react';
import { MessageSquare, Plus, Trash2, Activity, LogOut, LayoutGrid } from 'lucide-react';

export default function Sidebar({ 
  sessions, 
  currentSessionId, 
  onSelectSession, 
  onCreateSession, 
  onDeleteSession,
  username,
  onLogout,
  activeView = 'chat',     // View toggles: 'chat' or 'dashboard'
  onViewChange
}) {
  return (
    <aside className="sidebar">
      {/* Header Logotype */}
      <div className="sidebar-section" style={{ borderBottom: '1px solid var(--border-color)', padding: '1.25rem 1rem' }}>
        <style>{`
          @keyframes datly-glow-pulse {
            0% {
              transform: scale(1) translateY(0px);
              filter: drop-shadow(0 0 2px rgba(99, 110, 250, 0.4));
            }
            50% {
              transform: scale(1.06) translateY(-2.5px);
              filter: drop-shadow(0 0 12px rgba(99, 110, 250, 0.95)) drop-shadow(0 0 20px rgba(56, 189, 248, 0.7));
            }
            100% {
              transform: scale(1) translateY(0px);
              filter: drop-shadow(0 0 2px rgba(99, 110, 250, 0.4));
            }
          }
          .datly-logo-animated {
            animation: datly-glow-pulse 3.5s ease-in-out infinite;
            transform-origin: center;
            transition: all 0.3s ease;
          }
          .datly-logo-animated:hover {
            animation-duration: 1.5s;
            filter: drop-shadow(0 0 15px rgba(99, 110, 250, 1.0)) drop-shadow(0 0 25px rgba(56, 189, 248, 0.9));
          }
        `}</style>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', marginBottom: '0.2rem' }}>
          <svg className="datly-logo-animated" width="22" height="22" viewBox="0 0 512 512" style={{ flexShrink: 0 }}>
            <defs>
              <linearGradient id="sideDbGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#636efa" />
                <stop offset="100%" stopColor="#38bdf8" />
              </linearGradient>
              <linearGradient id="sideChatGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#a5b4fc" />
                <stop offset="100%" stopColor="#636efa" />
              </linearGradient>
            </defs>
            <g transform="translate(0, -10)">
              <ellipse cx="230" cy="180" rx="90" ry="28" fill="url(#sideDbGrad)" />
              <path d="M 140 180 A 90 28 0 0 0 320 180 L 320 250 A 90 28 0 0 1 140 250 Z" fill="url(#sideDbGrad)" opacity="0.85" />
              <ellipse cx="230" cy="250" rx="90" ry="28" fill="none" stroke="#0e0e12" strokeWidth="5" />
              <path d="M 140 250 A 90 28 0 0 0 320 250 L 320 320 A 90 28 0 0 1 140 320 Z" fill="url(#sideDbGrad)" opacity="0.65" />
              <rect x="230" y="260" width="160" height="110" rx="28" fill="url(#sideChatGrad)" stroke="#0e0e12" strokeWidth="8" />
              <path d="M 265 365 L 245 400 L 295 367 Z" fill="url(#sideChatGrad)" stroke="#0e0e12" strokeWidth="8" strokeLinejoin="round" />
              <path d="M 266 362 L 245 400 L 295 367 Z" fill="url(#sideChatGrad)" />
              <rect x="270" y="295" width="80" height="8" rx="4" fill="#0e0e12" opacity="0.8" />
              <rect x="270" y="315" width="55" height="8" rx="4" fill="#0e0e12" opacity="0.8" />
            </g>
          </svg>
          <span className="app-title" style={{ fontSize: '1.2rem', fontWeight: 800, color: 'white', letterSpacing: '-0.02em' }}>Datly</span>
        </div>
      </div>

      {/* Navigation Tabs inside the Sidebar */}
      <div style={{ padding: '0.75rem 1rem 0.5rem 1rem', display: 'flex', flexDirection: 'column', gap: '0.25rem', borderBottom: '1px solid var(--border-color)' }}>
        <button
          onClick={() => onViewChange('chat')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            width: '100%',
            padding: '0.55rem 0.75rem',
            borderRadius: '6px',
            background: activeView === 'chat' ? 'rgba(99, 110, 250, 0.08)' : 'transparent',
            border: 'none',
            color: activeView === 'chat' ? 'white' : 'var(--text-secondary)',
            fontSize: '0.8rem',
            fontWeight: 600,
            cursor: 'pointer',
            textAlign: 'left',
            transition: 'all 0.15s'
          }}
        >
          <MessageSquare size={14} style={{ color: activeView === 'chat' ? 'var(--primary)' : 'var(--text-secondary)' }} />
          Chat Workspace
        </button>
        
        <button
          onClick={() => onViewChange('dashboard')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            width: '100%',
            padding: '0.55rem 0.75rem',
            borderRadius: '6px',
            background: activeView === 'dashboard' ? 'rgba(99, 110, 250, 0.08)' : 'transparent',
            border: 'none',
            color: activeView === 'dashboard' ? 'white' : 'var(--text-secondary)',
            fontSize: '0.8rem',
            fontWeight: 600,
            cursor: 'pointer',
            textAlign: 'left',
            transition: 'all 0.15s'
          }}
        >
          <LayoutGrid size={14} style={{ color: activeView === 'dashboard' ? 'var(--primary)' : 'var(--text-secondary)' }} />
          Analytics Dashboard
        </button>
      </div>

      {/* Sleek full-width "+ New Chat" Button (Only active when in Chat Mode) */}
      <div style={{ padding: '1rem 1rem 0.25rem 1rem' }}>
        <button 
          onClick={() => {
            onViewChange('chat');
            onCreateSession();
          }}
          className="btn btn-primary"
          style={{ 
            width: '100%', 
            padding: '0.65rem 0.85rem', 
            borderRadius: '8px', 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center', 
            gap: '0.4rem', 
            fontSize: '0.82rem',
            fontWeight: 600,
            cursor: 'pointer',
            border: 'none',
            boxShadow: '0 4px 12px rgba(99, 110, 250, 0.15)',
            transition: 'all 0.2s'
          }}
        >
          <Plus size={15} />
          New Chat
        </button>
      </div>

      {/* Conversations history list */}
      <div className="sidebar-section" style={{ display: 'flex', flexDirection: 'column', flexGrow: 1, minHeight: 0, borderBottom: 'none', paddingTop: '0.5rem' }}>
        <div className="sidebar-section-title" style={{ paddingBottom: '0.35rem' }}>
          <span>Conversations</span>
        </div>
        
        <div className="session-list">
          {sessions.length === 0 ? (
            <div style={{ padding: '2rem 1rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
              No chats yet. Click the "New Chat" button above to start.
            </div>
          ) : (
            sessions.map(s => (
              <div 
                key={s.id} 
                className={`session-item ${s.id === currentSessionId ? 'active' : ''}`}
                onClick={() => {
                  onViewChange('chat');
                  onSelectSession(s.id);
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', minWidth: 0 }}>
                  <MessageSquare size={13} style={{ color: s.id === currentSessionId ? 'var(--primary)' : 'var(--text-secondary)', flexShrink: 0 }} />
                  <span className="session-title" title={s.title}>{s.title}</span>
                </div>
                <button 
                  className="btn-icon" 
                  style={{ padding: '0.15rem', opacity: s.id === currentSessionId ? 1 : 0.4 }}
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteSession(s.id);
                  }}
                  title="Delete conversation"
                >
                  <Trash2 size={11} style={{ color: 'var(--danger)' }} />
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Profile and Logout Card at the bottom */}
      <div style={{ 
        borderTop: '1px solid var(--border-color)', 
        padding: '0.95rem 1rem', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between', 
        backgroundColor: '#0a0a0f',
        transition: 'all 0.25s'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', minWidth: 0, cursor: 'default' }}>
          
          {/* Avatar with dynamic online pulse indicator */}
          <div style={{ position: 'relative', flexShrink: 0 }}>
            <div style={{ 
              width: '32px', 
              height: '32px', 
              borderRadius: '50%', 
              backgroundColor: 'rgba(99, 110, 250, 0.12)', 
              color: 'var(--primary)', 
              border: '1px solid rgba(99, 110, 250, 0.25)',
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center', 
              fontWeight: '700', 
              fontSize: '0.85rem'
            }}>
              {username ? username[0].toUpperCase() : 'U'}
            </div>
            {/* Green glowing status dot */}
            <span style={{
              position: 'absolute',
              bottom: '1px',
              right: '1px',
              width: '8px',
              height: '8px',
              backgroundColor: '#00cc96',
              border: '1.5px solid #0a0a0f',
              borderRadius: '50%',
              display: 'inline-block',
              boxShadow: '0 0 6px #00cc96'
            }} />
          </div>

          {/* User Meta labels */}
          <div style={{ display: 'flex', flexDirection: 'column', minWidth: 0 }}>
            <span style={{ 
              fontSize: '0.78rem', 
              fontWeight: 700, 
              whiteSpace: 'nowrap', 
              overflow: 'hidden', 
              textOverflow: 'ellipsis', 
              color: 'white',
              lineHeight: '1.2'
            }}>
              {username || 'Data Analyst'}
            </span>
            <span style={{ 
              fontSize: '0.62rem', 
              color: 'var(--text-muted)', 
              fontWeight: 500,
              marginTop: '0.1rem' 
            }}>
              Analyst Account
            </span>
          </div>
        </div>

        {/* Custom styled logout trigger */}
        <button 
          className="btn-icon" 
          onClick={onLogout} 
          title="Log Out of Session"
          style={{ 
            color: 'var(--danger)', 
            padding: '0.35rem', 
            borderRadius: '6px',
            backgroundColor: 'rgba(239, 68, 68, 0.05)',
            border: '1px solid rgba(239, 68, 68, 0.1)',
            cursor: 'pointer',
            transition: 'all 0.15s'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = 'rgba(239, 68, 68, 0.15)';
            e.currentTarget.style.borderColor = 'rgba(239, 68, 68, 0.3)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = 'rgba(239, 68, 68, 0.05)';
            e.currentTarget.style.borderColor = 'rgba(239, 68, 68, 0.1)';
          }}
        >
          <LogOut size={12} />
        </button>
      </div>
    </aside>
  );
}
