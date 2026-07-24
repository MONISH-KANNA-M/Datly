import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, 
  Terminal, 
  ChevronDown, 
  ChevronUp, 
  Check, 
  Copy, 
  AlertTriangle,
  FileText,
  BarChart3,
  Table as TableIcon,
  Sparkles,
  ArrowRight,
  Database,
  Download
} from 'lucide-react';
import InteractiveChart from './InteractiveChart';

// Helper to trigger spreadsheet table download
const downloadAsXls = (data, filename = 'byob_export.xls') => {
  if (!data || data.length === 0) return;
  const headers = Object.keys(data[0]).join('\t');
  const rows = data.map(row => 
    Object.values(row).map(val => {
      if (val === null || val === undefined) return '';
      return String(val).replace(/\t/g, ' ').replace(/\n/g, ' ');
    }).join('\t')
  ).join('\n');
  
  const blob = new Blob([`${headers}\n${rows}`], { type: 'application/vnd.ms-excel;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.setAttribute("href", url);
  link.setAttribute("download", filename);
  link.style.visibility = 'hidden';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

// Lightweight regex markdown parsing for bold, code blocks, and unordered lists
function renderMessageText(text) {
  if (!text) return null;

  // Simple escaping to prevent raw HTML rendering but let our tags pass
  let formatted = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Bold: **text** -> strong
  formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong style="color: white; font-weight: 600;">$1</strong>');

  // Italic: *text* -> em
  formatted = formatted.replace(/\*(.*?)\*/g, '<em style="color: var(--text-primary);">$1</em>');

  // Inline Code: `code` -> code tag
  formatted = formatted.replace(/`(.*?)`/g, '<code style="font-family: var(--font-mono); color: #38bdf8; background: rgba(56, 189, 248, 0.07); padding: 0.15rem 0.35rem; border-radius: 4px; font-size: 0.85em; border: 1px solid rgba(56, 189, 248, 0.15);">$1</code>');

  // Multi-line parsing for bulleted lists
  const lines = formatted.split('\n');
  let inList = false;
  const parsedLines = [];

  for (let line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      if (!inList) {
        parsedLines.push('<ul style="margin: 0.6rem 0 0.6rem 1.25rem; display: flex; flex-direction: column; gap: 0.35rem; list-style-type: disc;">');
        inList = true;
      }
      const content = trimmed.substring(2);
      parsedLines.push(`<li style="color: var(--text-primary); font-size: 0.88rem; line-height: 1.5; padding-left: 0.1rem;">${content}</li>`);
    } else {
      if (inList) {
        parsedLines.push('</ul>');
        inList = false;
      }
      parsedLines.push(`<p style="margin-bottom: 0.6rem; font-size: 0.9rem; line-height: 1.55; color: rgba(243, 244, 246, 0.95);">${line}</p>`);
    }
  }
  if (inList) {
    parsedLines.push('</ul>');
  }

  return <div dangerouslySetInnerHTML={{ __html: parsedLines.join('') }} />;
}

export default function ChatWindow({ 
  messages, 
  loading, 
  onSubmitQuestion,
  uploadedFiles,
  modelProvider = 'auto',
  setModelProvider
}) {
  const [question, setQuestion] = useState('');
  const messagesEndRef = useRef(null);

  // Auto scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!question.trim() || loading) return;
    onSubmitQuestion(question);
    setQuestion('');
  };

  const handleSuggestionClick = (promptText) => {
    if (loading) return;
    onSubmitQuestion(promptText);
  };

  // Sample prompt suggestions to wow users on load
  const sampleSuggestions = [
    { title: "Outlier Check", text: "Are there any outliers or anomalies in the dataset?", desc: "Check statistical thresholds" },
    { title: "Summary Metrics", text: "Summarize the key trends and columns of the table", desc: "Get high-level statistics" },
    { title: "Visual Trends", text: "Plot the columns in a bar chart to compare values", desc: "Generate visual graphs" }
  ];

  return (
    <div className="chat-panel">
      {/* Messages Scroll Containment */}
      <div className="messages-container" style={{ padding: '1.75rem 2rem' }}>
        {messages.length === 0 ? (
          <div className="empty-chat" style={{ maxWidth: '680px', margin: '0 auto', gap: '1.5rem', alignSelf: 'center', display: 'flex', flexDirection: 'column', height: 'auto', paddingTop: '2.5rem' }}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
              <div style={{
                width: '56px',
                height: '56px',
                borderRadius: '16px',
                backgroundColor: 'rgba(99, 110, 250, 0.08)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '1rem',
                border: '1px solid rgba(99, 110, 250, 0.2)'
              }}>
                <Sparkles style={{ color: 'var(--primary)', width: '28px', height: '28px' }} />
              </div>
              <h2 className="empty-chat-title" style={{ fontSize: '1.6rem', fontWeight: 800, letterSpacing: '-0.02em', fontFamily: 'var(--font-header)' }}>
                Conversational BI Engine
              </h2>
              <p className="empty-chat-p" style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginTop: '0.4rem', maxWidth: '460px' }}>
                Ask questions in natural language. The AI agent compiles DuckDB SQL, aggregates stats, flags outliers, and selects charts.
              </p>
            </div>

            {uploadedFiles.length === 0 ? (
              <div className="glass-card" style={{ padding: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.75rem', borderColor: 'rgba(239, 68, 68, 0.15)', backgroundColor: 'rgba(239, 68, 68, 0.02)' }}>
                <Database style={{ color: 'var(--danger)', flexShrink: 0 }} size={20} />
                <div style={{ textAlign: 'left' }}>
                  <h4 style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>No active data tables</h4>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.1rem' }}>
                    Upload a CSV/Excel file in the left panel to register a database namespace and unlock querying capabilities.
                  </p>
                </div>
              </div>
            ) : (
              <div style={{ width: '100%', marginTop: '0.5rem' }}>
                <p style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.75rem', textAlign: 'center' }}>
                  Suggested Analytics Prompts
                </p>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '0.65rem' }}>
                  {sampleSuggestions.map((s, idx) => (
                    <div 
                      key={idx} 
                      className="glass-card"
                      onClick={() => handleSuggestionClick(s.text)}
                      style={{
                        padding: '0.85rem 1.1rem',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        textAlign: 'left',
                        transition: 'all 0.2s',
                        borderRadius: '10px'
                      }}
                    >
                      <div style={{ minWidth: 0, paddingRight: '0.5rem' }}>
                        <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--primary)' }}>{s.title}</div>
                        <div style={{ fontSize: '0.8rem', color: 'var(--text-primary)', fontWeight: 500, marginTop: '0.15rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                          "{s.text}"
                        </div>
                      </div>
                      <ArrowRight size={13} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          messages.map(msg => (
            <div key={msg.id} className={`msg-wrapper ${msg.role}`} style={{ marginBottom: '0.75rem' }}>
              <div className="msg-bubble" style={{ 
                padding: msg.role === 'user' ? '0.75rem 1.1rem' : '1.25rem 1.5rem',
                border: msg.role === 'user' ? '1px solid rgba(99, 110, 250, 0.15)' : '1px solid var(--border-color)',
                boxShadow: msg.role === 'user' ? '0 4px 12px rgba(99, 110, 250, 0.1)' : 'var(--shadow-sm)'
              }}>
                {msg.role === 'user' ? (
                  <div style={{ whiteSpace: 'pre-line', fontSize: '0.9rem', fontWeight: 500 }}>{msg.text}</div>
                ) : (
                  <AssistantResponse msg={msg} />
                )}
              </div>
            </div>
          ))
        )}

        {/* Premium Spinner Loader Animation */}
        {loading && (
          <div className="msg-wrapper assistant" style={{ marginBottom: '0.75rem' }}>
            <div className="msg-bubble glass-card" style={{ 
              padding: '2rem 2.5rem',
              backgroundColor: 'rgba(20, 20, 26, 0.65)',
              border: '1px solid rgba(99, 110, 250, 0.25)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '1.25rem',
              maxWidth: '520px',
              margin: '1.5rem auto',
              boxShadow: '0 8px 32px rgba(99, 110, 250, 0.15)',
              borderRadius: '16px'
            }}>
              <div style={{
                position: 'relative',
                width: '60px',
                height: '60px',
                borderRadius: '50%',
                background: 'linear-gradient(to right, var(--primary) 10%, rgba(99, 110, 250, 0.05) 40%)',
                animation: 'spin 1s linear infinite',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <div style={{
                  width: '52px',
                  height: '52px',
                  borderRadius: '50%',
                  backgroundColor: '#101015'
                }} />
                <Sparkles 
                  style={{
                    position: 'absolute',
                    color: 'var(--primary)',
                    animation: 'pulse 1.5s ease-in-out infinite'
                  }} 
                  size={20} 
                />
              </div>

              <div style={{ textAlign: 'center' }}>
                <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'white', letterSpacing: '-0.01em' }}>
                  Analyzing dataset
                </h4>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.3rem', maxWidth: '320px', lineHeight: '1.45' }}>
                  The agent is writing SQL queries, performing statistical validation, and building charts.
                </p>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Bar Section */}
      <div className="chat-input-bar" style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem', padding: '1rem 2rem 1.5rem 2rem', borderTop: '1px solid var(--border-color)', backgroundColor: 'var(--bg-app)' }}>
        
        {/* Model Selector Corner Dropdown */}
        <div style={{ display: 'flex', justifyContent: 'flex-start', alignItems: 'center', gap: '0.4rem', paddingLeft: '0.1rem' }}>
          <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.02em' }}>Engine:</span>
          <select
            value={modelProvider}
            onChange={(e) => setModelProvider(e.target.value)}
            style={{
              backgroundColor: 'var(--bg-sidebar)',
              border: '1px solid var(--border-color)',
              color: 'white',
              fontSize: '0.7rem',
              fontWeight: 600,
              padding: '0.2rem 0.6rem 0.2rem 0.4rem',
              borderRadius: '6px',
              outline: 'none',
              cursor: 'pointer',
              transition: 'border-color 0.15s'
            }}
          >
            <option value="auto" style={{ backgroundColor: '#101015', color: 'white' }}>Auto (Local/Cloud)</option>
            <option value="ollama" style={{ backgroundColor: '#101015', color: 'white' }}>Ollama Local</option>
            <option value="groq" style={{ backgroundColor: '#101015', color: 'white' }}>Groq Cloud (Fast)</option>
          </select>
        </div>

        <form onSubmit={handleSubmit} className="chat-input-form" style={{ margin: 0 }}>
          <input
            type="text"
            className="form-input"
            placeholder={uploadedFiles.length === 0 ? "Please upload datasets on the left panel to begin..." : "Ask a question (e.g. 'Plot average of values by item') ..."}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={loading || uploadedFiles.length === 0}
            style={{ 
              padding: '0.8rem 1.1rem',
              borderRadius: '10px',
              backgroundColor: 'var(--bg-app)',
              border: '1px solid var(--border-color)'
            }}
          />
          <button 
            type="submit" 
            className="btn btn-primary"
            disabled={loading || !question.trim() || uploadedFiles.length === 0}
            style={{ padding: '0 1.25rem', borderRadius: '10px' }}
          >
            <Send size={14} />
            Ask
          </button>
        </form>
      </div>
    </div>
  );
}

// Render Assistant Turn Contents
function AssistantResponse({ msg }) {
  const [activeTab, setActiveTab] = useState('insights');
  const [showReasoning, setShowReasoning] = useState(false);
  const [copied, setCopied] = useState(false);

  const copySql = () => {
    if (!msg.sql_query) return;
    navigator.clipboard.writeText(msg.sql_query);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const hasData = msg.data && msg.data.length > 0;
  const hasChart = msg.chart_info && msg.chart_info.recommended_type !== 'none' && hasData;
  const hasAnomalies = msg.anomalies && msg.anomalies.length > 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
      
      {/* 1. Reasoning chains */}
      {msg.reasoning && (
        <div>
          <button 
            onClick={() => setShowReasoning(!showReasoning)}
            style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '0.25rem', 
              background: 'transparent', 
              border: 'none', 
              color: 'var(--primary)', 
              fontSize: '0.75rem', 
              fontWeight: 600,
              cursor: 'pointer',
              padding: 0,
              opacity: 0.85
            }}
          >
            {showReasoning ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
            {showReasoning ? 'Hide logical reasoning' : 'Show agent workflow steps'}
          </button>
          
          {showReasoning && (
            <div className="reasoning-box" style={{ marginTop: '0.4rem', borderLeftColor: 'var(--primary)', backgroundColor: 'rgba(99, 110, 250, 0.03)' }}>
              <div className="reasoning-title" style={{ fontSize: '0.75rem' }}>
                <Terminal size={11} />
                Execution Graph
              </div>
              <div className="reasoning-text" style={{ fontSize: '0.75rem', lineHeight: '1.45', opacity: 0.9 }}>
                {msg.reasoning}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 2. Outlier anomalies alert cards */}
      {hasAnomalies && (
        <div className="anomaly-card" style={{ margin: '0.25rem 0', borderRadius: '10px' }}>
          <div className="anomaly-header" style={{ fontSize: '0.8rem' }}>
            <AlertTriangle size={14} />
            Data Outliers Flagged ({msg.anomalies.length})
          </div>
          <div className="anomaly-desc" style={{ fontSize: '0.75rem' }}>
            {msg.anomalies[0].llm_explanation || "Statistical thresholds (IQR/Z-Score) detected values that sit significantly outside normal aggregates."}
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.3rem', marginTop: '0.4rem' }}>
            {msg.anomalies.slice(0, 4).map((a, i) => (
              <span key={i} className="anomaly-badge" style={{ fontSize: '0.65rem' }}>
                {a.column}: {a.value}
              </span>
            ))}
            {msg.anomalies.length > 4 && (
              <span className="anomaly-badge" style={{ backgroundColor: 'transparent', color: 'rgba(255,255,255,0.4)', fontSize: '0.65rem' }}>
                +{msg.anomalies.length - 4} more
              </span>
            )}
          </div>
        </div>
      )}

      {/* 3. Text output summaries */}
      {!hasData ? (
        <div className="message-content-text">
          {renderMessageText(msg.text)}
        </div>
      ) : (
        <div>
          {/* Result Tab heads */}
          <div className="result-tabs" style={{ marginBottom: '0.5rem' }}>
            <button 
              className={`tab-btn ${activeTab === 'insights' ? 'active' : ''}`}
              onClick={() => setActiveTab('insights')}
              style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}
            >
              <FileText size={12} />
              Insights
            </button>
            
            {hasChart && (
              <button 
                className={`tab-btn ${activeTab === 'chart' ? 'active' : ''}`}
                onClick={() => setActiveTab('chart')}
                style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}
              >
                <BarChart3 size={12} />
                Chart
              </button>
            )}
            
            <button 
              className={`tab-btn ${activeTab === 'data' ? 'active' : ''}`}
              onClick={() => setActiveTab('data')}
              style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}
            >
              <TableIcon size={12} />
              Data ({msg.data.length})
            </button>
          </div>

          {/* Tab content bodies */}
          <div className="tab-content" style={{ minHeight: '180px' }}>
            {activeTab === 'insights' && (
              <div className="message-content-text">
                {renderMessageText(msg.text)}
              </div>
            )}
            
            {activeTab === 'chart' && hasChart && (
              <InteractiveChart data={msg.data} chartInfo={msg.chart_info} />
            )}
            
            {activeTab === 'data' && (
              <div>
                {/* Export download bar */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.65rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Showing up to 100 rows</span>
                  <button 
                    className="btn btn-secondary"
                    onClick={() => downloadAsXls(msg.data, `byob_export_${Date.now()}.xls`)}
                    style={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      gap: '0.3rem', 
                      padding: '0.35rem 0.65rem', 
                      borderRadius: '6px', 
                      fontSize: '0.75rem', 
                      cursor: 'pointer',
                      border: '1px solid var(--border-color)',
                      backgroundColor: 'rgba(255,255,255,0.02)',
                      color: 'var(--text-primary)',
                      transition: 'all 0.2s'
                    }}
                  >
                    <Download size={12} style={{ color: 'var(--primary)' }} />
                    Export to Excel (.xls)
                  </button>
                </div>

                <div className="data-table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        {Object.keys(msg.data[0]).map(col => (
                          <th key={col}>{col}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {msg.data.slice(0, 100).map((row, i) => (
                        <tr key={i}>
                          {Object.values(row).map((val, j) => (
                            <td key={j}>{val === null || val === undefined ? 'NULL' : String(val)}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {msg.data.length > 100 && (
                    <div style={{ padding: '0.5rem', textAlign: 'center', fontSize: '0.7rem', color: 'var(--text-muted)', backgroundColor: '#0f0f15' }}>
                      Showing first 100 of {msg.data.length} rows.
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 4. Code Blocks */}
      {msg.sql_query && (
        <div className="sql-box" style={{ borderRadius: '8px', padding: '0.6rem 0.8rem', marginTop: '0.2rem' }}>
          <div className="sql-header" style={{ marginBottom: '0.25rem', paddingBottom: '0.25rem' }}>
            <span>DuckDB Script</span>
            <button className="sql-copy-btn" onClick={copySql}>
              {copied ? <Check size={9} style={{ color: 'var(--success)' }} /> : <Copy size={9} />}
              {copied ? 'Copied' : 'Copy'}
            </button>
          </div>
          <pre style={{ overflowX: 'auto', whiteSpace: 'pre-wrap', margin: 0, fontSize: '0.75rem', lineHeight: '1.45' }}>
            <code style={{ color: '#38bdf8' }}>{msg.sql_query}</code>
          </pre>
          {msg.execution_time_ms !== undefined && (
            <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginTop: '0.25rem', display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '0.35rem' }}>
              {msg.execution_time_ms === 0.0 && (
                <span className="status-badge status-success" style={{ backgroundColor: 'rgba(0,204,150,0.1)', color: 'var(--success)', padding: '0.1rem 0.35rem', fontSize: '0.6rem', display: 'flex', alignItems: 'center', gap: '0.15rem', borderRadius: '4px', border: '1px solid rgba(0,204,150,0.2)' }}>
                  <Sparkles size={8} />
                  ⚡ Cached
                </span>
              )}
              <span>Fetched in {msg.execution_time_ms.toFixed(1)}ms</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
