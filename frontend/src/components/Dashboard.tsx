import { useState, useEffect } from 'react';
import { Shield, Lock, CheckCircle, Activity } from 'lucide-react';

type View = 'dashboard' | 'process' | 'audit' | 'about';

interface DashboardProps {
    onNavigate: (view: View) => void;
}

interface Metrics {
    total_documents: number;
    total_redacted: number;
    avg_processing_time: number;
    privacy_protected_percentage: number;
}

export default function Dashboard({ onNavigate }: DashboardProps) {
    const [metrics, setMetrics] = useState<Metrics>({
        total_documents: 0,
        total_redacted: 0,
        avg_processing_time: 0,
        privacy_protected_percentage: 100
    });

    useEffect(() => {
        const fetchMetrics = async () => {
            try {
                const response = await fetch('/api/v1/audit/summary');
                if (response.ok) {
                    const data = await response.json();
                    setMetrics(data);
                }
            } catch (err) {
                console.error("Failed to fetch dashboard metrics:", err);
            }
        };

        fetchMetrics();
        // Refresh every 30 seconds
        const interval = setInterval(fetchMetrics, 30000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
            <div className="mb-12">
                <h2 className="text-3xl font-bold text-slate-900 dark:text-white mb-3">
                    Welcome to Edge Policy AI
                </h2>
                <p className="text-lg text-slate-600 dark:text-slate-400">
                    Process sensitive documents locally with AI-powered redaction and security
                </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
                <div className="bg-white dark:bg-slate-900/50 rounded-lg shadow-sm border border-slate-200 dark:border-slate-800 p-6">
                    <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center mb-4">
                        <Shield className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                    </div>
                    <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">Local Processing</h3>
                    <p className="text-slate-600 dark:text-slate-400 text-sm">
                        All sensitive data processing happens on your device. Nothing leaves your machine unredacted.
                    </p>
                </div>

                <div className="bg-white dark:bg-slate-900/50 rounded-lg shadow-sm border border-slate-200 dark:border-slate-800 p-6">
                    <div className="w-12 h-12 bg-cyan-100 dark:bg-cyan-900/30 rounded-lg flex items-center justify-center mb-4">
                        <Lock className="w-6 h-6 text-cyan-600 dark:text-cyan-400" />
                    </div>
                    <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">AI-Powered Detection</h3>
                    <p className="text-slate-600 dark:text-slate-400 text-sm">
                        Advanced NER models identify PII, PCI, and PHI with high accuracy and confidence scoring.
                    </p>
                </div>

                <div className="bg-white dark:bg-slate-900/50 rounded-lg shadow-sm border border-slate-200 dark:border-slate-800 p-6">
                    <div className="w-12 h-12 bg-green-100 dark:bg-green-900/30 rounded-lg flex items-center justify-center mb-4">
                        <CheckCircle className="w-6 h-6 text-green-600 dark:text-green-400" />
                    </div>
                    <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">Cryptographic Sealing</h3>
                    <p className="text-slate-600 dark:text-slate-400 text-sm">
                        Documents are digitally signed to ensure tamper detection and maintain audit integrity.
                    </p>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <button
                    onClick={() => onNavigate('process')}
                    className="bg-gradient-to-br from-blue-600 to-cyan-600 dark:from-indigo-600 dark:to-blue-600 rounded-lg shadow-md hover:shadow-xl transition-all p-8 text-left group"
                >
                    <div className="flex items-start justify-between mb-4">
                        <div className="w-14 h-14 bg-white/20 rounded-lg flex items-center justify-center backdrop-blur-sm">
                            <Shield className="w-7 h-7 text-white" />
                        </div>
                        <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center backdrop-blur-sm group-hover:bg-white/30 transition-colors">
                            <span className="text-white text-lg">→</span>
                        </div>
                    </div>
                    <h3 className="text-2xl font-bold text-white mb-2">Process New Document</h3>
                    <p className="text-blue-100">
                        Upload and redact sensitive information from text or PDF documents with AI-powered detection
                    </p>
                </button>

                <button
                    onClick={() => onNavigate('audit')}
                    className="bg-white dark:bg-slate-900 rounded-lg shadow-sm hover:shadow-md transition-all border border-slate-200 dark:border-slate-700 p-8 text-left group"
                >
                    <div className="flex items-start justify-between mb-4">
                        <div className="w-14 h-14 bg-slate-100 dark:bg-slate-800 rounded-lg flex items-center justify-center group-hover:bg-slate-200 dark:group-hover:bg-slate-700 transition-colors">
                            <Activity className="w-7 h-7 text-slate-700 dark:text-slate-300" />
                        </div>
                        <div className="w-8 h-8 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center group-hover:bg-slate-200 dark:group-hover:bg-slate-700 transition-colors">
                            <span className="text-slate-700 dark:text-slate-300 text-lg">→</span>
                        </div>
                    </div>
                    <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">View Audit Logs</h3>
                    <p className="text-slate-600 dark:text-slate-400">
                        Track all document processing activities and review security validation history
                    </p>
                </button>
            </div>

            <div className="mt-12 bg-slate-900 dark:bg-slate-950/50 rounded-lg shadow-lg border border-transparent dark:border-slate-800 p-8">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <div className="text-center">
                        <div className="text-3xl font-bold text-white mb-1">{metrics.total_documents}</div>
                        <div className="text-sm text-slate-400 dark:text-slate-500">Documents Processed</div>
                    </div>
                    <div className="text-center">
                        <div className="text-3xl font-bold text-white mb-1">{metrics.total_redacted}</div>
                        <div className="text-sm text-slate-400 dark:text-slate-500">Entities Redacted</div>
                    </div>
                    <div className="text-center">
                        <div className="text-3xl font-bold text-white mb-1">{metrics.privacy_protected_percentage}%</div>
                        <div className="text-sm text-slate-400 dark:text-slate-500">Privacy Protected</div>
                    </div>
                    <div className="text-center">
                        <div className="text-3xl font-bold text-white mb-1">{metrics.avg_processing_time}ms</div>
                        <div className="text-sm text-slate-400 dark:text-slate-500">Avg Processing Time</div>
                    </div>
                </div>
            </div>
        </div>
    );
}
