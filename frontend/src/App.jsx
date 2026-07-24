import React, { useState, useEffect } from 'react';
import { ClerkProvider, SignedIn, SignedOut, useUser, useAuth } from '@clerk/clerk-react';
import Sidebar from './components/Sidebar';
import FileUpload from './components/FileUpload';
import ChatWindow from './components/ChatWindow';
import DashboardView from './components/DashboardView';
import Login from './components/Login';

const API_BASE_URL = 'http://localhost:8000';
const CLERK_PUBLISHABLE_KEY = 'pk_test_cXVhbGl0eS1nbG93d29ybS0zOS5jbGVyay5hY2NvdW50cy5kZXYk';

function Dashboard() {
  const { user } = useUser();
  const { getToken, signOut } = useAuth();
  const username = user?.username || user?.primaryEmailAddress?.emailAddress || 'Clerk User';

  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [schema, setSchema] = useState({});
  const [selectedTables, setSelectedTables] = useState([]); // User selected active tables
  const [loading, setLoading] = useState(false);
  const [apiStatus, setApiStatus] = useState({ backend: false, ollama: false, duckdb: true });

  // Model Backend Provider: 'auto' (default), 'ollama' or 'groq'
  const [modelProvider, setModelProvider] = useState('auto');

  // Sidebar navigation view toggle: 'chat' or 'dashboard'
  const [activeView, setActiveView] = useState('chat');
  const [dashboardWidgets, setDashboardWidgets] = useState([]);
  const [dashboardLoading, setDashboardLoading] = useState(false);

  // 1. Initial fetches
  useEffect(() => {
    checkBackendHealth();
    fetchSessions();
    fetchUploadedFiles();
    fetchSchema();
  }, []);

  // 2. Fetch messages on session change
  useEffect(() => {
    if (currentSessionId) {
      fetchMessages(currentSessionId);
    } else {
      setMessages([]);
    }
  }, [currentSessionId]);

  // 3. Fetch dashboard data when dashboard view is active
  useEffect(() => {
    if (activeView === 'dashboard') {
      fetchDashboard();
    }
  }, [activeView]);

  const getHeaders = async () => {
    const token = await getToken();
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    };
  };

  const handleLogout = () => {
    if (window.confirm('Are you sure you want to log out of your session?')) {
      signOut();
    }
  };

  const handleToggleTableSelection = (tableName) => {
    setSelectedTables(prev => {
      if (prev.includes(tableName)) {
        return prev.filter(t => t !== tableName);
      } else {
        return [...prev, tableName];
      }
    });
  };

  // Test backend connectivity
  const checkBackendHealth = async () => {
    try {
      const headers = await getHeaders();
      const res = await fetch(`${API_BASE_URL}/api/schema`, {
        headers
      });
      if (res.status === 200 || res.status === 401) {
        setApiStatus(prev => ({ ...prev, backend: true, ollama: true }));
      }
    } catch (e) {
      setApiStatus(prev => ({ ...prev, backend: false, ollama: false }));
    }
  };

  // Sessions API calls
  const fetchSessions = async () => {
    try {
      const headers = await getHeaders();
      const response = await fetch(`${API_BASE_URL}/api/sessions`, {
        headers
      });
      if (!response.ok) throw new Error();
      const data = await response.json();
      setSessions(data);
      
      if (data.length > 0 && !currentSessionId) {
        setCurrentSessionId(data[0].id);
      } else if (data.length === 0) {
        handleCreateSession();
      }
    } catch (error) {
      console.error('Failed to fetch sessions:', error);
    }
  };

  const handleCreateSession = async () => {
    try {
      const headers = await getHeaders();
      const response = await fetch(`${API_BASE_URL}/api/sessions`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ title: 'New Chat' })
      });
      if (!response.ok) throw new Error();
      const newSession = await response.json();
      setSessions(prev => [newSession, ...prev]);
      setCurrentSessionId(newSession.id);
    } catch (error) {
      console.error('Failed to create session:', error);
    }
  };

  const handleDeleteSession = async (sessionId) => {
    if (!window.confirm('Are you sure you want to delete this conversation thread?')) return;
    try {
      const headers = await getHeaders();
      const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}`, {
        method: 'DELETE',
        headers
      });
      if (!response.ok) throw new Error();
      
      setSessions(prev => prev.filter(s => s.id !== sessionId));
      if (currentSessionId === sessionId) {
        const remaining = sessions.filter(s => s.id !== sessionId);
        setCurrentSessionId(remaining.length > 0 ? remaining[0].id : null);
      }
    } catch (error) {
      console.error('Failed to delete session:', error);
    }
  };

  const fetchMessages = async (sessionId) => {
    try {
      const headers = await getHeaders();
      const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}/messages`, {
        headers
      });
      if (!response.ok) throw new Error();
      const data = await response.json();
      setMessages(data);
    } catch (error) {
      console.error('Failed to fetch messages:', error);
    }
  };

  // Uploaded Files API calls
  const fetchUploadedFiles = async () => {
    try {
      const headers = await getHeaders();
      const response = await fetch(`${API_BASE_URL}/api/files`, {
        headers
      });
      if (!response.ok) throw new Error();
      const data = await response.json();
      setUploadedFiles(data);
      
      // Auto-select uploaded tables
      setSelectedTables(prev => {
        const currentTables = data.map(f => f.table_name);
        return [...new Set([...prev.filter(t => currentTables.includes(t)), ...currentTables])];
      });
    } catch (error) {
      console.error('Failed to fetch uploaded files:', error);
    }
  };

  const handleDeleteFile = async (tableName) => {
    if (!window.confirm(`Are you sure you want to delete table '${tableName}' from the database?`)) return;
    try {
      const headers = await getHeaders();
      const response = await fetch(`${API_BASE_URL}/api/files/${tableName}`, {
        method: 'DELETE',
        headers
      });
      if (!response.ok) throw new Error();
      
      setUploadedFiles(prev => prev.filter(f => f.table_name !== tableName));
      setSelectedTables(prev => prev.filter(t => t !== tableName));
      fetchSchema();
      // Invalidate local dashboard data
      setDashboardWidgets([]);
    } catch (error) {
      console.error('Failed to delete table:', error);
    }
  };

  const handleUploadSuccess = (uploadedInfo) => {
    fetchUploadedFiles();
    fetchSchema();
    setDashboardWidgets([]);
  };

  const fetchSchema = async () => {
    try {
      const headers = await getHeaders();
      const response = await fetch(`${API_BASE_URL}/api/schema`, {
        headers
      });
      if (!response.ok) throw new Error();
      const data = await response.json();
      setSchema(data);
    } catch (error) {
      console.error('Failed to fetch schema:', error);
    }
  };

  // Dashboard API calls
  const fetchDashboard = async () => {
    try {
      const headers = await getHeaders();
      const response = await fetch(`${API_BASE_URL}/api/dashboard`, {
        headers
      });
      if (!response.ok) throw new Error();
      const data = await response.json();
      setDashboardWidgets(data);
    } catch (error) {
      console.error('Failed to fetch dashboard widgets:', error);
    }
  };

  const handleGenerateDashboard = async () => {
    setDashboardLoading(true);
    try {
      const headers = await getHeaders();
      const response = await fetch(`${API_BASE_URL}/api/dashboard/generate`, {
        method: 'POST',
        headers
      });
      if (!response.ok) throw new Error();
      const data = await response.json();
      setDashboardWidgets(data.widgets);
    } catch (error) {
      console.error('Failed to generate dashboard:', error);
      alert('Dashboard generation failed. Make sure tables are active.');
    } finally {
      setDashboardLoading(false);
    }
  };

  // Submit Query to Agent
  const handleSubmitQuestion = async (questionText) => {
    if (!currentSessionId) {
      alert('Please start or select a chat session first.');
      return;
    }

    setLoading(true);
    
    // Add user message optimistically
    const tempUserMsg = {
      id: Date.now(),
      session_id: currentSessionId,
      role: 'user',
      text: questionText,
      created_at: new Date().toISOString()
    };
    setMessages(prev => [...prev, tempUserMsg]);

    // Optimistically update the session title in local state if it is currently default
    setSessions(prev => 
      prev.map(s => {
        if (s.id === currentSessionId && (s.title === 'New Chat' || s.title.toLowerCase() === 'new chat')) {
          const snippet = questionText.length > 40 ? questionText.substring(0, 40) + '...' : questionText;
          return { ...s, title: snippet };
        }
        return s;
      })
    );

    try {
      const headers = await getHeaders();
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          session_id: currentSessionId,
          question: questionText,
          selected_tables: selectedTables,
          model_provider: modelProvider  // Explicit routing parameter
        })
      });

      if (!response.ok) {
        throw new Error('Agent execution returned an error status.');
      }

      await fetchMessages(currentSessionId);
      await fetchSessions();
    } catch (error) {
      console.error('Submit query failed:', error);
      setMessages(prev => [
        ...prev,
        {
          id: Date.now() + 1,
          session_id: currentSessionId,
          role: 'assistant',
          text: 'An error occurred while connecting to the LLM agent. Make sure both Ollama and uvicorn backend servers are running.',
          created_at: new Date().toISOString()
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      {/* 1. Sidebar Panel (Conversations + Nav Toggles + Logout) */}
      <Sidebar 
        sessions={sessions}
        currentSessionId={currentSessionId}
        onSelectSession={setCurrentSessionId}
        onCreateSession={handleCreateSession}
        onDeleteSession={handleDeleteSession}
        username={username}
        onLogout={handleLogout}
        activeView={activeView}
        onViewChange={setActiveView}
      />

      {/* 2. Main Analytics Workspace */}
      <main className="main-content">
        <header className="app-header" style={{ justifyContent: 'center' }}>
          <div className="app-title-group" style={{ textAlign: 'center' }}>
            <span className="app-title" style={{ fontSize: '1.25rem', fontWeight: 800 }}>
              Datly — <span style={{ background: 'linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', color: 'var(--primary)' }}>Talk to Your Data.</span>
            </span>
          </div>
        </header>

        {/* Workspace views split */}
        {activeView === 'chat' ? (
          <div className="dashboard-grid" style={{ flexGrow: 1, minHeight: 0 }}>
            {/* Left panel: secure dataset upload & catalog schemas */}
            <FileUpload 
              uploadedFiles={uploadedFiles}
              onUploadSuccess={handleUploadSuccess}
              onDeleteFile={handleDeleteFile}
              schema={schema}
              getToken={getToken}
              selectedTables={selectedTables}
              onToggleTableSelection={handleToggleTableSelection}
              apiBaseUrl={API_BASE_URL}
            />

            {/* Right panel: secure Chat dialogue and answers */}
            <ChatWindow 
              messages={messages}
              loading={loading}
              onSubmitQuestion={handleSubmitQuestion}
              uploadedFiles={uploadedFiles}
              modelProvider={modelProvider}
              setModelProvider={setModelProvider}
            />
          </div>
        ) : (
          <div style={{ flexGrow: 1, minHeight: 0, overflow: 'hidden' }}>
            <DashboardView 
              widgets={dashboardWidgets}
              onGenerate={handleGenerateDashboard}
              loading={dashboardLoading}
            />
          </div>
        )}
      </main>
    </div>
  );
}

export default function App() {
  return (
    <ClerkProvider publishableKey={CLERK_PUBLISHABLE_KEY}>
      <SignedIn>
        <Dashboard />
      </SignedIn>
      <SignedOut>
        <Login />
      </SignedOut>
    </ClerkProvider>
  );
}
