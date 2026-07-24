import React, { useRef, useState } from 'react';
import { 
  UploadCloud, 
  FileSpreadsheet, 
  Trash2, 
  Loader, 
  Database, 
  ChevronDown, 
  ChevronRight, 
  Layers, 
  Sparkles,
  ShieldAlert,
  X,
  Heart
} from 'lucide-react';

// Helper to strip long user session prefixes for clean UI presentation
const getFriendlyTableName = (rawTableName) => {
  if (!rawTableName) return '';
  return rawTableName.replace(/^u_user_[a-zA-Z0-9]+_/, '');
};

export default function FileUpload({ 
  uploadedFiles, 
  onUploadSuccess, 
  onDeleteFile,
  schema,
  getToken,
  selectedTables = [],
  onToggleTableSelection,
  apiBaseUrl = 'http://localhost:8000'
}) {
  const fileInputRef = useRef(null);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [expandedTables, setExpandedTables] = useState({});

  // Data Quality States
  const [activeQualityTable, setActiveQualityTable] = useState(null);
  const [qualityReport, setQualityReport] = useState(null);
  const [qualityLoading, setQualityLoading] = useState(false);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      uploadFiles(e.target.files);
    }
  };

  const onDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const onDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      uploadFiles(e.dataTransfer.files);
    }
  };

  const uploadFiles = async (fileList) => {
    setUploading(true);
    const formData = new FormData();
    for (let i = 0; i < fileList.length; i++) {
      formData.append('files', fileList[i]);
    }

    try {
      const token = await getToken();
      const response = await fetch(`${apiBaseUrl}/api/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Upload request failed.');
      }

      const data = await response.json();
      onUploadSuccess(data.files);
      if (fileInputRef.current) fileInputRef.current.value = '';
    } catch (error) {
      console.error('File upload error:', error);
      alert('Failed to upload file. Make sure the backend server is running.');
    } finally {
      setUploading(false);
    }
  };

  const triggerQualityCheck = async (tableName) => {
    setActiveQualityTable(tableName);
    setQualityLoading(true);
    setQualityReport(null);
    try {
      const token = await getToken();
      const response = await fetch(`${apiBaseUrl}/api/files/${tableName}/quality`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!response.ok) throw new Error();
      const data = await response.json();
      setQualityReport(data);
    } catch (error) {
      console.error('Data quality profiling failed:', error);
      setActiveQualityTable(null);
      alert('Failed to profile table quality. Please ensure the backend is connected.');
    } finally {
      setQualityLoading(false);
    }
  };

  const toggleTable = (tableName) => {
    setExpandedTables(prev => ({
      ...prev,
      [tableName]: !prev[tableName]
    }));
  };

  return (
    <div className="ingest-panel">
      {/* 1. Drag & Drop File uploader */}
      <div>
        <h3 style={{ fontFamily: 'var(--font-header)', fontWeight: 600, fontSize: '0.9rem', marginBottom: '0.65rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
          <FileSpreadsheet size={15} style={{ color: 'var(--primary)' }} />
          Ingest Datasets
        </h3>
        
        <div 
          className="file-upload-zone"
          onDragEnter={onDrag}
          onDragLeave={onDrag}
          onDragOver={onDrag}
          onDrop={onDrop}
          onClick={() => fileInputRef.current?.click()}
          style={{ borderColor: dragActive ? 'var(--primary)' : 'var(--border-color)', backgroundColor: dragActive ? 'var(--bg-input)' : 'var(--bg-sidebar)' }}
        >
          <input 
            type="file" 
            ref={fileInputRef} 
            style={{ display: 'none' }} 
            multiple 
            accept=".csv,.xlsx,.xls"
            onChange={handleFileChange}
          />
          
          {uploading ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.4rem', padding: '0.2rem 0' }}>
              <Loader className="pulse" style={{ color: 'var(--primary)', animation: 'spin 1.5s linear infinite' }} size={24} />
              <p style={{ fontSize: '0.75rem', fontWeight: 500 }}>Ingesting tables...</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
              <UploadCloud className="file-upload-icon" />
              <p style={{ fontSize: '0.75rem', fontWeight: 500, marginBottom: '0.1rem' }}>Drag & drop files here</p>
              <p style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>CSV or Excel files</p>
            </div>
          )}
        </div>
      </div>

      {/* 2. Uploaded Tables list */}
      <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '1rem' }}>
        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.5rem', fontWeight: 600, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>Active Tables</span>
          <span style={{ fontSize: '0.65rem', textTransform: 'none', fontWeight: 'normal' }}>check to query</span>
        </div>
        
        <div className="file-list">
          {uploadedFiles.length === 0 ? (
            <div style={{ padding: '1rem 0', color: 'var(--text-muted)', fontSize: '0.75rem', textAlign: 'center' }}>
              No datasets loaded.
            </div>
          ) : (
            uploadedFiles.map(file => {
              const isSelected = selectedTables.includes(file.table_name);
              const friendlyName = getFriendlyTableName(file.table_name);
              return (
                <div key={file.table_name} className="file-item">
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', minWidth: 0, flexGrow: 1 }}>
                    <input 
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => onToggleTableSelection(file.table_name)}
                      style={{ cursor: 'pointer', flexShrink: 0, accentColor: 'var(--primary)' }}
                      title="Select this table for queries"
                    />
                    <div className="file-item-info" style={{ minWidth: 0, flexGrow: 1 }}>
                      <span className="file-item-name" title={file.filename} style={{ textDecoration: isSelected ? 'none' : 'line-through', opacity: isSelected ? 1 : 0.45, transition: 'all 0.15s', textTransform: 'capitalize', fontSize: '0.85rem', fontWeight: 600 }}>
                        {friendlyName}
                      </span>
                      
                      <span className="file-item-rows" style={{ display: 'flex', flexDirection: 'column', gap: '0.1rem', marginTop: '0.1rem' }}>
                        <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>File: {file.filename}</span>
                        <span>Scope ID: <code style={{ color: isSelected ? 'var(--primary)' : 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: '0.65rem' }}>{friendlyName}</code> ({file.row_count} rows)</span>
                        
                        {/* Profile Data Quality Button trigger */}
                        <div style={{ display: 'flex', gap: '0.4rem', marginTop: '0.2rem' }}>
                          <button 
                            onClick={(e) => { e.stopPropagation(); triggerQualityCheck(file.table_name); }}
                            style={{ 
                              background: 'transparent', 
                              border: 'none', 
                              color: 'var(--primary)', 
                              fontSize: '0.65rem', 
                              fontWeight: 600,
                              padding: 0, 
                              cursor: 'pointer', 
                              display: 'flex', 
                              alignItems: 'center', 
                              gap: '0.15rem' 
                            }}
                          >
                            <Sparkles size={10} />
                            Data Quality Profile
                          </button>
                        </div>
                      </span>
                    </div>
                  </div>
                  <button 
                    className="btn-icon"
                    style={{ color: 'var(--danger)', padding: '0.25rem', flexShrink: 0 }}
                    onClick={() => onDeleteFile(file.table_name)}
                    title="Remove from database"
                  >
                    <Trash2 size={12} />
                  </button>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* 3. Collapsible Database schema browser */}
      <div className="schema-catalog-container" style={{ borderTop: '1px solid var(--border-color)', paddingTop: '1rem' }}>
        <div className="sidebar-section-title" style={{ marginBottom: '0.5rem' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}><Layers size={12} /> Table Schemas</span>
          <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>{Object.keys(schema).length} active</span>
        </div>
        
        <div className="schema-catalog">
          {Object.keys(schema).length === 0 ? (
            <div style={{ padding: '1rem 0.5rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.75rem' }}>
              No active schemas.
            </div>
          ) : (
            Object.entries(schema).map(([tableName, cols]) => {
              const isExpanded = !!expandedTables[tableName];
              const isSelected = selectedTables.includes(tableName);
              const friendlyName = getFriendlyTableName(tableName);
              return (
                <div key={tableName} className="schema-table-item" style={{ opacity: isSelected ? 1 : 0.5, transition: 'all 0.15s' }}>
                  <div className="schema-table-header" onClick={() => toggleTable(tableName)}>
                    <span className="schema-table-name" style={{ textTransform: 'capitalize' }}>
                      <Database size={11} />
                      {friendlyName}
                    </span>
                    {isExpanded ? <ChevronDown size={11} /> : <ChevronRight size={11} />}
                  </div>
                  {isExpanded && (
                    <div className="schema-table-cols">
                      {cols.map(c => (
                        <div key={c.name} className="schema-col-item">
                          <span className="schema-col-name">{c.name}</span>
                          <span className="schema-col-type">{c.type}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* --- Data Quality Report Modal Overlay --- */}
      {activeQualityTable && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.7)',
          backdropFilter: 'blur(5px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 9999,
          padding: '1.5rem'
        }}>
          <div className="glass-card" style={{
            width: '100%',
            maxWidth: '620px',
            backgroundColor: '#121217',
            borderColor: '#222230',
            borderRadius: '16px',
            boxShadow: '0 20px 40px rgba(0,0,0,0.6)',
            display: 'flex',
            flexDirection: 'column',
            maxHeight: '85vh',
            boxSizing: 'border-box'
          }}>
            {/* Modal Head */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1.25rem 1.5rem', borderBottom: '1px solid var(--border-color)', flexShrink: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <ShieldAlert size={18} style={{ color: 'var(--primary)' }} />
                <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'white', textTransform: 'capitalize' }}>
                  {getFriendlyTableName(activeQualityTable)} Data Quality Profile
                </h3>
              </div>
              <button 
                onClick={() => setActiveQualityTable(null)}
                style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', padding: '0.2rem' }}
              >
                <X size={16} />
              </button>
            </div>

            {/* Modal Body */}
            <div style={{ padding: '1.5rem', overflowY: 'auto', flexGrow: 1, display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              {qualityLoading ? (
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem', padding: '3rem 0' }}>
                  <Loader style={{ color: 'var(--primary)', animation: 'spin 1.5s linear infinite' }} size={32} />
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Running DuckDB profiling scans...</span>
                </div>
              ) : qualityReport ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                  {/* Health summary banner */}
                  <div style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'space-between', 
                    padding: '1rem 1.25rem', 
                    borderRadius: '12px', 
                    backgroundColor: 'rgba(99, 110, 250, 0.04)', 
                    border: '1px solid rgba(99, 110, 250, 0.2)' 
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <Heart size={18} style={{ color: qualityReport.health_score > 80 ? 'var(--success)' : 'var(--warning)' }} />
                      <div>
                        <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'white' }}>Data Quality Health Score</h4>
                        <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.1rem' }}>
                          Calculated using row counts, duplicate values, and null rates.
                        </p>
                      </div>
                    </div>
                    <span style={{ 
                      fontSize: '1.75rem', 
                      fontWeight: 800, 
                      color: qualityReport.health_score > 80 ? 'var(--success)' : 'var(--warning)' 
                    }}>
                      {qualityReport.health_score}%
                    </span>
                  </div>

                  {/* Health Bar fill */}
                  <div style={{ width: '100%', height: '6px', backgroundColor: 'rgba(255,255,255,0.06)', borderRadius: '3px', overflow: 'hidden', marginTop: '-0.65rem' }}>
                    <div style={{ 
                      width: `${qualityReport.health_score}%`, 
                      height: '100%', 
                      background: qualityReport.health_score > 80 
                        ? 'linear-gradient(90deg, #00cc96 0%, #38bdf8 100%)' 
                        : 'linear-gradient(90deg, #ff9f43 0%, #ef4444 100%)',
                      borderRadius: '3px',
                      transition: 'width 1.2s cubic-bezier(0.4, 0, 0.2, 1)' 
                    }} />
                  </div>

                  {/* General stats cards */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                    <div className="glass-card" style={{ padding: '0.85rem 1rem' }}>
                      <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Total Ingested Rows</span>
                      <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'white', marginTop: '0.2rem' }}>{qualityReport.total_rows}</div>
                    </div>
                    <div className="glass-card" style={{ padding: '0.85rem 1rem' }}>
                      <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Duplicate Rows Rate</span>
                      <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'white', marginTop: '0.2rem' }}>
                        {qualityReport.duplicate_rows} <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>({qualityReport.duplicate_percentage}%)</span>
                      </div>
                    </div>
                  </div>

                  {/* Column analysis table */}
                  <div>
                    <h4 style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.5rem', fontWeight: 600 }}>
                      Column Profiling Report
                    </h4>
                    <div className="data-table-container" style={{ maxHeight: '250px' }}>
                      <table className="data-table" style={{ fontSize: '0.75rem' }}>
                        <thead>
                          <tr>
                            <th>Column</th>
                            <th>Type</th>
                            <th>Null Count</th>
                            <th>Uniqueness</th>
                            <th>Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          {qualityReport.columns.map(c => (
                            <tr key={c.name}>
                              <td style={{ fontWeight: 600, color: 'white' }}>{c.name}</td>
                              <td><code style={{ fontSize: '0.65rem' }}>{c.type}</code></td>
                              <td>{c.null_count} <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>({c.null_percentage}%)</span></td>
                              <td>{c.distinct_count} <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>({c.distinct_percentage}%)</span></td>
                              <td>
                                <span className={`status-badge ${c.status === 'Healthy' ? 'status-success' : 'status-danger'}`} style={{ padding: '0.05rem 0.3rem', fontSize: '0.6rem' }}>
                                  {c.status}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: '2rem 0', color: 'var(--text-muted)' }}>
                  Unable to retrieve metrics for this table.
                </div>
              )}
            </div>

            {/* Modal Foot */}
            <div style={{ padding: '1rem 1.5rem', borderTop: '1px solid var(--border-color)', display: 'flex', justifyContent: 'flex-end', flexShrink: 0 }}>
              <button 
                className="btn btn-secondary"
                onClick={() => setActiveQualityTable(null)}
                style={{ padding: '0.4rem 1rem', borderRadius: '8px', fontSize: '0.8rem', cursor: 'pointer' }}
              >
                Close Profile
              </button>
            </div>
          </div>
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
