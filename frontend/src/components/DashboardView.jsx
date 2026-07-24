import React from 'react';
import { Sparkles, Loader, LayoutGrid } from 'lucide-react';
import InteractiveChart from './InteractiveChart';

export default function DashboardView({ widgets = [], onGenerate, loading }) {
  
  const metricWidgets = widgets.filter(w => w.widget_type === 'metric');
  const chartWidgets = widgets.filter(w => w.widget_type === 'chart');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0, padding: '1.5rem 2rem', gap: '1.5rem', overflowY: 'auto' }}>
      
      {/* Header bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-color)', paddingBottom: '1rem', flexShrink: 0 }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'white', letterSpacing: '-0.02em', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <LayoutGrid size={18} style={{ color: 'var(--primary)' }} />
            Workspace Dashboard
          </h2>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.15rem' }}>
            Auto-generate metric KPIs and distribution charts for all active datasets.
          </p>
        </div>
        
        <button 
          className="btn btn-primary"
          onClick={onGenerate}
          disabled={loading}
          style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', borderRadius: '8px', padding: '0.5rem 1rem' }}
        >
          {loading ? (
            <Loader style={{ animation: 'spin 1.5s linear infinite' }} size={13} />
          ) : (
            <Sparkles size={13} />
          )}
          {widgets.length > 0 ? 'Sync & Re-generate' : 'Generate Auto-Dashboard'}
        </button>
      </div>

      {loading && widgets.length === 0 ? (
        <div style={{ flexGrow: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '0.75rem', color: 'var(--text-secondary)' }}>
          <Loader className="pulse" style={{ color: 'var(--primary)', animation: 'spin 1.5s linear infinite' }} size={32} />
          <span style={{ fontSize: '0.85rem' }}>Calculating data quality and building distribution charts...</span>
        </div>
      ) : widgets.length === 0 ? (
        <div style={{ flexGrow: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '1rem', border: '1px dashed var(--border-color)', borderRadius: '12px', padding: '4rem 2rem', textAlign: 'center' }}>
          <LayoutGrid size={40} style={{ color: 'var(--text-muted)' }} />
          <div>
            <h4 style={{ fontSize: '0.9rem', color: 'white', fontWeight: 600 }}>No dashboard widgets built</h4>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.2rem', maxWidth: '380px' }}>
              Click the button in the top right to analyze your active database tables and construct automatic summary metrics.
            </p>
          </div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', flexGrow: 1 }}>
          
          {/* Metrics KPIs Row */}
          {metricWidgets.length > 0 && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '1rem' }}>
              {metricWidgets.map(m => {
                const item = m.data && m.data[0] ? m.data[0] : {};
                return (
                  <div key={m.id} className="glass-card" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>
                      {m.title}
                    </span>
                    <span style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--primary)' }}>
                      {item.metric_value !== undefined ? String(item.metric_value) : '0'}
                    </span>
                    {item.subtitle && (
                      <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>
                        {item.subtitle}
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {/* Charts Grid Row */}
          {chartWidgets.length > 0 && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(440px, 1fr))', gap: '1.25rem' }}>
              {chartWidgets.map(c => (
                <div key={c.id} className="glass-card" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                  <h4 style={{ fontSize: '0.85rem', fontWeight: 600, color: 'white' }}>
                    {c.title}
                  </h4>
                  <div style={{ pointerEvents: 'none' }}>
                    {/* Reuse InteractiveChart in static preview mode */}
                    <InteractiveChart data={c.data} chartInfo={c.config} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
