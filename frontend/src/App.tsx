import { useState } from 'react';
import { Shield, FileText, Activity, Archive } from 'lucide-react';
import Dashboard from './components/Dashboard';
import ProcessDocument from './components/ProcessDocument';
import AuditLog from './components/AuditLog';
import Header from './components/Header';

type View = 'dashboard' | 'process' | 'audit' | 'about';

function App() {
  const [currentView, setCurrentView] = useState<View>('dashboard');

  const renderView = () => {
    switch (currentView) {
      case 'dashboard':
        return <Dashboard onNavigate={setCurrentView} />;
      case 'process':
        return <ProcessDocument />;
      case 'audit':
        return <AuditLog />;
      case 'about':
        return <AboutView />;
      default:
        return <Dashboard onNavigate={setCurrentView} />;
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 transition-colors duration-200">
      <Header currentView={currentView} onNavigate={setCurrentView} />

      <nav className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 transition-colors duration-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            <button
              onClick={() => setCurrentView('dashboard')}
              className={`flex items-center gap-2 px-3 py-4 text-sm font-medium border-b-2 transition-colors ${currentView === 'dashboard'
                ? 'border-blue-600 dark:border-blue-500 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:border-slate-300 dark:hover:border-slate-700'
                }`}
            >
              <Shield className="w-4 h-4" />
              Dashboard
            </button>
            <button
              onClick={() => setCurrentView('process')}
              className={`flex items-center gap-2 px-3 py-4 text-sm font-medium border-b-2 transition-colors ${currentView === 'process'
                ? 'border-blue-600 dark:border-blue-500 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:border-slate-300 dark:hover:border-slate-700'
                }`}
            >
              <FileText className="w-4 h-4" />
              Process Document
            </button>
            <button
              onClick={() => setCurrentView('audit')}
              className={`flex items-center gap-2 px-3 py-4 text-sm font-medium border-b-2 transition-colors ${currentView === 'audit'
                ? 'border-blue-600 dark:border-blue-500 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:border-slate-300 dark:hover:border-slate-700'
                }`}
            >
              <Activity className="w-4 h-4" />
              Audit Log
            </button>
            <button
              onClick={() => setCurrentView('about')}
              className={`flex items-center gap-2 px-3 py-4 text-sm font-medium border-b-2 transition-colors ${currentView === 'about'
                ? 'border-blue-600 dark:border-blue-500 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:border-slate-300 dark:hover:border-slate-700'
                }`}
            >
              <Archive className="w-4 h-4" />
              About
            </button>
          </div>
        </div>
      </nav>

      <main>{renderView()}</main>
    </div>
  );
}

function AboutView() {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="bg-white dark:bg-slate-900 rounded-lg shadow-sm border border-slate-200 dark:border-slate-800 p-8 transition-colors duration-200">
        <h2 className="text-2xl font-semibold text-slate-900 dark:text-white mb-4">About Edge Policy AI</h2>
        <div className="prose prose-slate dark:prose-invert max-w-none">
          <p className="text-slate-600 dark:text-slate-300 mb-4">
            Edge Policy AI is a privacy-preserving text document processing application designed to run locally
            on edge devices. It acts as a Local Security Gateway between raw, sensitive documents and external
            cloud processing layers.
          </p>

          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mt-6 mb-3">Core Workflow</h3>
          <ol className="list-decimal list-inside space-y-2 text-slate-600 dark:text-slate-300">
            <li><strong>Upload:</strong> Authenticate and upload documents containing sensitive information</li>
            <li><strong>Extraction:</strong> Extract raw text from documents using native or OCR methods</li>
            <li><strong>Detection:</strong> Use AI and NER to identify sensitive entities in the text</li>
            <li><strong>Redaction:</strong> Mask sensitive data with typed placeholders</li>
            <li><strong>Reconstruction:</strong> Create sanitized documents with cryptographic sealing</li>
            <li><strong>Audit:</strong> Track all processing activities securely without storing sensitive data</li>
          </ol>

          <div className="mt-8 p-4 bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800/50 rounded-lg">
            <p className="text-sm text-blue-900 dark:text-blue-300 font-medium">
              🔒 Security Principle: No unredacted PII/PCI/PHI ever leaves your device
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
