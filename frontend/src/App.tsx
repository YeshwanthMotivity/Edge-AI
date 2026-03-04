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
    <div className="min-h-screen bg-white dark:bg-brand-obsidian text-slate-900 dark:text-white transition-colors duration-500 font-sans">
      <Header currentView={currentView} onNavigate={setCurrentView} />



      <nav className="bg-white/80 dark:bg-brand-obsidian/80 backdrop-blur-md border-b border-slate-200 dark:border-white/5 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            <button
              onClick={() => setCurrentView('dashboard')}
              className={`flex items-center gap-2 px-4 py-4 text-sm font-bold border-b-2 transition-all duration-300 ${currentView === 'dashboard'
                ? 'border-brand-violet-600 text-brand-violet-600 dark:text-brand-violet-400 dark:border-brand-violet-400 drop-shadow-[0_0_8px_rgba(107,70,255,0.4)]'
                : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-brand-violet-600 dark:hover:text-brand-violet-400 hover:border-slate-300 dark:hover:border-white/10'
                }`}
            >
              <Shield className="w-4 h-4" />
              Dashboard
            </button>

            <button
              onClick={() => setCurrentView('process')}
              className={`flex items-center gap-2 px-4 py-4 text-sm font-bold border-b-2 transition-all duration-300 ${currentView === 'process'
                ? 'border-brand-violet-600 text-brand-violet-600 dark:text-brand-violet-400 dark:border-brand-violet-400 drop-shadow-[0_0_8px_rgba(107,70,255,0.4)]'
                : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-brand-violet-600 dark:hover:text-brand-violet-400 hover:border-slate-300 dark:hover:border-white/10'
                }`}
            >
              <FileText className="w-4 h-4" />
              Process Document
            </button>

            <button
              onClick={() => setCurrentView('audit')}
              className={`flex items-center gap-2 px-4 py-4 text-sm font-bold border-b-2 transition-all duration-300 ${currentView === 'audit'
                ? 'border-brand-violet-600 text-brand-violet-600 dark:text-brand-violet-400 dark:border-brand-violet-400 drop-shadow-[0_0_8px_rgba(107,70,255,0.4)]'
                : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-brand-violet-600 dark:hover:text-brand-violet-400 hover:border-slate-300 dark:hover:border-white/10'
                }`}
            >
              <Activity className="w-4 h-4" />
              Audit Log
            </button>

            <button
              onClick={() => setCurrentView('about')}
              className={`flex items-center gap-2 px-4 py-4 text-sm font-bold border-b-2 transition-all duration-300 ${currentView === 'about'
                ? 'border-brand-violet-600 text-brand-violet-600 dark:text-brand-violet-400 dark:border-brand-violet-400 drop-shadow-[0_0_8px_rgba(107,70,255,0.4)]'
                : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-brand-violet-600 dark:hover:text-brand-violet-400 hover:border-slate-300 dark:hover:border-white/10'
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
      <div className="bg-white dark:bg-brand-obsidian-light/30 rounded-4xl shadow-2xl border border-slate-200 dark:border-white/5 p-10 transition-all backdrop-blur-sm relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-brand-violet-600/5 rounded-full blur-3xl -mr-32 -mt-32"></div>
        <h2 className="text-4xl font-black text-slate-900 dark:text-white mb-6 tracking-tight">About EdgeAI Policy</h2>
        <div className="prose prose-slate dark:prose-invert max-w-none">
          <p className="text-xl text-slate-600 dark:text-slate-300 mb-8 leading-relaxed font-medium">
            EdgeAI Policy is a high-performance, privacy-preserving document sanitization engine.
            Designed as an <span className="text-brand-violet-600 dark:text-brand-violet-400 font-black drop-shadow-[0_0_10px_rgba(107,70,255,0.3)]">Edge AI Security Gateway</span>,
            it ensures that sensitive information is never exposed to external networks or third-party AI models.
          </p>

          <h3 className="text-2xl font-black text-slate-900 dark:text-white mt-12 mb-6 flex items-center gap-3">
            <Activity className="w-6 h-6 text-brand-violet-600 dark:text-brand-violet-400" />
            The Security Pipeline
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="p-6 bg-slate-50 dark:bg-brand-violet-950/40 rounded-3xl border border-slate-100 dark:border-brand-violet-600/20 group hover:border-brand-violet-600/50 transition-all duration-300">
              <p className="text-base font-bold text-slate-900 dark:text-slate-100 italic">Local Authentication & Secure Ingest</p>
            </div>


            <div className="p-6 bg-slate-50 dark:bg-brand-violet-950/40 rounded-3xl border border-slate-100 dark:border-brand-violet-600/20 group hover:border-brand-violet-600/50 transition-all duration-300">
              <p className="text-base font-bold text-slate-900 dark:text-slate-100 italic">Advanced NLP Entity Extraction</p>
            </div>


            <div className="p-6 bg-slate-50 dark:bg-brand-violet-950/40 rounded-3xl border border-slate-100 dark:border-brand-violet-600/20 group hover:border-brand-violet-600/50 transition-all duration-300">
              <p className="text-base font-bold text-slate-900 dark:text-slate-100 italic">Deterministic Masking & Sanitization</p>
            </div>


            <div className="p-6 bg-slate-50 dark:bg-brand-violet-950/40 rounded-3xl border border-slate-100 dark:border-brand-violet-600/20 group hover:border-brand-violet-600/50 transition-all duration-300">
              <p className="text-base font-bold text-slate-900 dark:text-slate-100 italic">Cryptographic Digital Sealing</p>
            </div>

          </div>

          <div className="mt-16 p-8 bg-gradient-to-r from-brand-violet-600/20 to-brand-obsidian dark:from-brand-violet-600/20 dark:to-brand-obsidian border border-brand-violet-600/30 rounded-4xl relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-8 opacity-5 group-hover:scale-110 transition-transform duration-700">
              <Shield className="w-48 h-48 -mr-16 -mt-16" />
            </div>
            <div className="flex items-center gap-6 relative z-10">
              <div className="w-16 h-16 bg-brand-violet-600 dark:bg-brand-violet-600 text-white rounded-2xl flex items-center justify-center shadow-[0_0_20px_rgba(107,70,255,0.4)] group-hover:scale-105 transition-transform duration-300">
                <Shield className="w-8 h-8" />
              </div>
              <div>
                <h4 className="text-2xl font-black text-slate-900 dark:text-white">Zero Trust Architecture</h4>
                <p className="text-lg text-slate-700 dark:text-slate-300 font-bold opacity-80 decoration-brand-violet-600/50 decoration-2 underline-offset-4">Enterprise-Grade Security</p>
                <p className="text-sm text-slate-600 dark:text-slate-400 font-medium">No PII, PCI, or PHI ever leaves this device unredacted.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;

