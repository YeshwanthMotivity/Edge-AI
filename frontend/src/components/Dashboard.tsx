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
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchMetrics = async () => {
            try {
                const response = await fetch('/api/v1/audit/summary');
                if (response.ok) {
                    const data = await response.json();
                    setMetrics(data);
                    setError(null);
                } else {
                    setError("Failed to connect to security gateway");
                }
            } catch (err) {
                console.error("Failed to fetch dashboard metrics:", err);
                setError("Backend connection refused. Please ensure the server is running on port 8000.");
            }
        };

        fetchMetrics();
        // Refresh every 30 seconds
        const interval = setInterval(fetchMetrics, 30000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
            {error && (
                <div className="mb-8 p-4 bg-red-50/50 dark:bg-red-900/10 border border-red-100 dark:border-red-500/10 rounded-2xl flex items-center gap-3 text-red-600 dark:text-red-400 backdrop-blur-sm">
                    <Activity className="w-5 h-5 opacity-70" />
                    <p className="text-sm font-bold tracking-tight">{error}</p>
                </div>
            )}


            <div className="relative mb-12 overflow-hidden rounded-4xl bg-white dark:bg-brand-obsidian-light/20 border border-slate-200 dark:border-brand-violet-600/20 p-10 lg:p-12 group transition-all duration-700 shadow-2xl shadow-brand-violet-600/5">

                {/* Advanced glow effects */}
                <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-brand-violet-600/5 dark:bg-brand-violet-600/10 rounded-full blur-[120px] -mr-64 -mt-64 animate-pulse"></div>
                <div className="absolute bottom-0 left-0 w-96 h-96 bg-brand-violet-600/5 dark:bg-brand-violet-600/10 rounded-full blur-[100px] -ml-48 -mb-48 opacity-50"></div>

                <div className="relative z-10 max-w-3xl text-left">
                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-violet-600/10 border border-brand-violet-600/20 mb-8 transition-all group-hover:bg-brand-violet-600/20">
                        <span className="w-1.5 h-1.5 bg-brand-violet-600 rounded-full animate-ping"></span>
                        <span className="text-[10px] font-black text-brand-violet-600 dark:text-brand-violet-400 uppercase tracking-widest leading-none">Enterprise Protection Active</span>
                    </div>

                    <div className="space-y-2 mb-8">
                        <h2 className="text-4xl lg:text-5xl font-black text-slate-400 dark:text-slate-500 leading-none tracking-tighter opacity-80">
                            Welcome to
                        </h2>
                        <h2 className="text-5xl lg:text-7xl font-black text-brand-violet-600 dark:text-brand-violet-400 leading-none tracking-tighter drop-shadow-[0_0_30px_rgba(107,70,255,0.4)]">
                            EdgeAI Policy
                        </h2>

                    </div>

                    <p className="text-xl lg:text-2xl text-slate-600 dark:text-slate-300 font-medium leading-relaxed max-w-xl">
                        High-performance document sanitization powered by <span className="text-slate-900 dark:text-white font-black underline decoration-brand-violet-600/50 decoration-4 underline-offset-4">Local AI</span>.
                        Zero trust, zero leakage, maximum privacy.
                    </p>
                </div>
            </div>



            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
                <div className="bg-white dark:glass-card-purple rounded-3xl p-8 border border-slate-100 dark:border-brand-violet-600/20 group hover:neon-border-purple transition-all duration-500 relative overflow-hidden shadow-xl shadow-slate-200/50 dark:shadow-brand-violet-600/10 hover:shadow-2xl">

                    <div className="absolute bottom-0 right-0 w-32 h-32 bg-brand-violet-600/5 rounded-full blur-2xl -mb-16 -mr-16"></div>
                    <div className="relative z-10">
                        <div className="w-14 h-14 bg-brand-violet-600/10 rounded-2xl flex items-center justify-center mb-6 border border-brand-violet-600/20 shadow-inner group-hover:scale-110 transition-transform">
                            <Shield className="w-7 h-7 text-brand-violet-600 dark:text-brand-violet-400" />
                        </div>
                        <h3 className="text-xl font-black text-slate-900 dark:text-white mb-3 tracking-tight">Local Processing</h3>
                        <p className="text-slate-600 dark:text-slate-400 text-sm font-medium leading-relaxed">
                            Data never leaves your secure perimeter. All AI inference happens strictly within your local environment.
                        </p>
                    </div>
                </div>

                <div className="bg-white dark:glass-card-purple rounded-3xl p-8 border border-slate-100 dark:border-brand-violet-600/20 group hover:neon-border-purple transition-all duration-500 relative overflow-hidden shadow-xl shadow-slate-200/50 dark:shadow-brand-violet-600/10 hover:shadow-2xl">

                    <div className="relative z-10">
                        <div className="w-14 h-14 bg-brand-violet-600/10 rounded-2xl flex items-center justify-center mb-6 border border-brand-violet-600/20 shadow-inner group-hover:rotate-6 transition-transform">
                            <Lock className="w-7 h-7 text-brand-violet-600 dark:text-brand-violet-400" />
                        </div>
                        <h3 className="text-xl font-black text-slate-900 dark:text-white mb-3 tracking-tight">AI Redaction</h3>
                        <p className="text-slate-600 dark:text-slate-400 text-sm font-medium leading-relaxed">
                            Advanced Transformers automatically identify and mask sensitive entities (PII, PCI, PHI) with 99.9% accuracy.
                        </p>
                    </div>
                </div>

                <div className="bg-white dark:glass-card-purple rounded-3xl p-8 border border-slate-100 dark:border-brand-violet-600/20 group hover:neon-border-purple transition-all duration-500 relative overflow-hidden shadow-xl shadow-slate-200/50 dark:shadow-brand-violet-600/10 hover:shadow-2xl">

                    <div className="relative z-10">
                        <div className="w-14 h-14 bg-brand-violet-600/10 rounded-2xl flex items-center justify-center mb-6 border border-brand-violet-600/20 shadow-inner group-hover:scale-110 transition-transform">
                            <CheckCircle className="w-7 h-7 text-brand-violet-600 dark:text-brand-violet-400" />
                        </div>
                        <h3 className="text-xl font-black text-slate-900 dark:text-white mb-3 tracking-tight">Digital Sealing</h3>
                        <p className="text-slate-600 dark:text-slate-400 text-sm font-medium leading-relaxed">
                            Every sanitized document is cryptographically signed to ensure non-repudiation and lifecycle integrity.
                        </p>
                    </div>
                </div>
            </div>




            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-16">
                <button
                    onClick={() => onNavigate('process')}
                    className="group relative overflow-hidden rounded-4xl bg-brand-violet-600 p-10 text-left transition-all hover:scale-[1.02] active:scale-[0.98] shadow-2xl shadow-brand-violet-600/20"
                >
                    <div className="absolute top-0 right-0 p-6 opacity-10 group-hover:scale-125 transition-transform duration-700">
                        <Shield className="w-48 h-48 -mr-12 -mt-12" />
                    </div>
                    <div className="relative z-10">
                        <div className="mb-6 flex items-center justify-between">
                            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-white/20 backdrop-blur-md border border-white/20">
                                <Shield className="h-8 w-8 text-white" />
                            </div>
                            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity">
                                <span className="text-white text-2xl font-light">→</span>
                            </div>
                        </div>
                        <h3 className="text-3xl font-black text-white mb-3">Process New Document</h3>
                        <p className="text-lg font-medium text-white/80 leading-snug">
                            Scaleable local sanitization. Upload documents for AI-driven PII removal.
                        </p>
                    </div>
                </button>

                <button
                    onClick={() => onNavigate('audit')}
                    className="group relative overflow-hidden rounded-4xl bg-white dark:bg-brand-obsidian-light/40 border border-slate-100 dark:border-white/5 p-10 text-left transition-all hover:bg-slate-50 dark:hover:bg-brand-obsidian-light/60 shadow-xl shadow-slate-200/50 dark:shadow-none"
                >

                    <div className="relative z-10">
                        <div className="mb-6 flex items-center justify-between">
                            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-slate-100 dark:bg-brand-violet-950/50 border border-slate-200 dark:border-brand-violet-600/30 group-hover:border-brand-violet-600/50 transition-all">
                                <Activity className="h-8 w-8 text-slate-700 dark:text-brand-violet-400" />
                            </div>
                            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-50 dark:bg-brand-violet-950/20 opacity-0 group-hover:opacity-100 transition-opacity">
                                <span className="text-slate-900 dark:text-white text-2xl font-light">→</span>
                            </div>
                        </div>
                        <h3 className="text-3xl font-black text-slate-900 dark:text-white mb-3">View Audit Logs</h3>
                        <p className="text-lg font-medium text-slate-600 dark:text-slate-400 leading-snug">
                            Legally defensible audit trails. Track every sanitization event with full integrity.
                        </p>
                    </div>
                </button>
            </div>




            <div className="bg-brand-violet-600 dark:bg-brand-obsidian-light/30 rounded-4xl shadow-2xl shadow-brand-violet-600/20 p-12 relative overflow-hidden group transition-all duration-500">
                <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-white/10 dark:bg-brand-violet-600/10 rounded-full -mr-64 -mt-64 blur-[120px] transition-transform group-hover:scale-110 duration-1000"></div>
                <div className="absolute bottom-0 left-0 w-96 h-96 bg-white/5 dark:bg-brand-violet-600/10 rounded-full -ml-48 -mb-48 blur-[100px] transition-transform group-hover:scale-110 duration-1000"></div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-12 relative z-10">
                    <div className="text-center md:text-left transition-transform hover:translate-y-[-4px]">
                        <div className="text-5xl lg:text-6xl font-black text-white mb-2 tracking-tighter drop-shadow-[0_0_15px_rgba(255,255,255,0.2)]">
                            {metrics.total_documents.toLocaleString()}
                        </div>
                        <div className="text-xs font-black text-white/70 dark:text-brand-violet-400 uppercase tracking-[0.4em]">Total Documents</div>

                    </div>
                    <div className="text-center md:text-left transition-transform hover:translate-y-[-4px]">
                        <div className="text-5xl lg:text-6xl font-black text-white mb-2 tracking-tighter drop-shadow-[0_0_15px_rgba(255,255,255,0.2)]">
                            {metrics.total_redacted.toLocaleString()}
                        </div>
                        <div className="text-xs font-black text-white/70 dark:text-brand-violet-400 uppercase tracking-[0.4em]">Redactions</div>

                    </div>
                    <div className="text-center md:text-left transition-transform hover:translate-y-[-4px]">
                        <div className="text-5xl lg:text-6xl font-black text-white mb-2 tracking-tighter drop-shadow-[0_0_15px_rgba(255,255,255,0.2)]">
                            {metrics.privacy_protected_percentage}%
                        </div>
                        <div className="text-xs font-black text-white/90 dark:text-emerald-400 uppercase tracking-[0.4em]">Integrity</div>

                    </div>
                    <div className="text-center md:text-left transition-transform hover:translate-y-[-4px]">
                        <div className="text-5xl lg:text-6xl font-black text-white mb-2 tracking-tighter drop-shadow-[0_0_15px_rgba(255,255,255,0.2)]">
                            {metrics.avg_processing_time}<span className="text-2xl opacity-50 ml-1">ms</span>
                        </div>
                        <div className="text-xs font-black text-white/70 dark:text-slate-400 uppercase tracking-[0.4em]">Avg Latency</div>

                    </div>
                </div>
            </div>


        </div>
    );
}
