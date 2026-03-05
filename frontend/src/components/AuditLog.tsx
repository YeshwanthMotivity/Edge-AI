import { useState, useEffect } from 'react';
import { Shield, Clock, FileText, CheckCircle, AlertCircle, Search, Download } from 'lucide-react';

interface AuditEntry {
    id: string;
    timestamp: string;
    filename: string;
    status: 'success' | 'failed';
    entitiesFound: number;
    processingTime: number;
    fileSize: number;
}

export default function AuditLog() {
    const [auditEntries, setAuditEntries] = useState<AuditEntry[]>([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [filterStatus, setFilterStatus] = useState<'all' | 'success' | 'failed'>('all');
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetchAuditLog();
    }, []);

    const fetchAuditLog = async () => {
        try {
            const response = await fetch('/api/v1/audit');
            if (response.ok) {
                const data = await response.json();
                setAuditEntries(data.entries || []);
                setError(null);
            } else {
                setError("Failed to retrieve audit records");
            }
        } catch (err) {
            console.error('Failed to fetch audit log:', err);
            setError("Connection failed. Audit logs are currently unavailable.");
        }
    };

    const filteredEntries = auditEntries.filter((entry) => {
        const matchesSearch = entry.filename.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesFilter = filterStatus === 'all' || entry.status === filterStatus;
        return matchesSearch && matchesFilter;
    });

    const formatDate = (timestamp: string) => {
        // Append 'Z' to treat the backend naive datetime as UTC, 
        // which forces the browser to convert it to the user's local timezone
        const dateStr = timestamp.endsWith('Z') ? timestamp : `${timestamp}Z`;
        return new Date(dateStr).toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        });
    };

    const formatFileSize = (bytes: number) => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    };

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 transition-colors duration-200">
            {error && (
                <div className="mb-8 p-4 bg-red-50/50 dark:bg-red-900/10 border border-red-100 dark:border-red-500/10 rounded-2xl flex items-center gap-3 text-red-600 dark:text-red-400 backdrop-blur-sm">
                    <AlertCircle className="w-5 h-5 opacity-70" />
                    <p className="text-sm font-bold tracking-tight">{error}</p>
                </div>
            )}

            <div className="mb-10 flex flex-col md:flex-row md:items-end md:justify-between gap-6">
                <div>
                    <h2 className="text-4xl font-black text-slate-900 dark:text-white mb-3 tracking-tighter">Audit Log</h2>
                    <p className="text-lg text-slate-600 dark:text-brand-violet-400/80 font-medium">
                        Complete traceability for <span className="text-brand-violet-600 dark:text-brand-violet-400 font-black">EdgeAI Policy</span> sanitization events.
                    </p>
                </div>
                <button
                    onClick={() => window.open('/api/v1/audit/export', '_blank')}
                    className="flex items-center justify-center gap-3 bg-brand-violet-600 dark:bg-white text-white dark:text-brand-obsidian px-6 py-3 rounded-2xl font-black uppercase tracking-widest hover:bg-brand-violet-500 dark:hover:bg-slate-100 transition-all shrink-0 shadow-xl shadow-brand-violet-600/20 active:scale-95 border border-transparent"
                >
                    <Download className="w-5 h-5" />
                    <span>Download Logs</span>
                </button>

            </div>


            <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-100 dark:border-white/5 shadow-2xl shadow-slate-200/50 transition-colors duration-200 overflow-hidden">


                <div className="p-6 border-b border-slate-100 dark:border-white/5">
                    <div className="flex flex-col sm:flex-row gap-6">
                        <div className="flex-1 relative">
                            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400 dark:text-brand-violet-400/50" />
                            <input
                                type="text"
                                placeholder="Filter by filename..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="w-full pl-12 pr-4 py-3 bg-slate-50 dark:bg-brand-obsidian-light/20 border border-slate-200 dark:border-white/5 text-slate-900 dark:text-white rounded-2xl focus:outline-none focus:ring-2 focus:ring-brand-violet-600 focus:border-transparent transition-all placeholder:text-slate-400 placeholder:dark:text-white/20 font-medium"
                            />
                        </div>

                        <div className="flex bg-slate-100 dark:bg-brand-obsidian-light/30 p-1.5 rounded-2xl border border-slate-200 dark:border-white/5">
                            <button
                                onClick={() => setFilterStatus('all')}
                                className={`px-5 py-2 rounded-xl font-black text-[10px] uppercase tracking-widest transition-all ${filterStatus === 'all'
                                    ? 'bg-white dark:bg-brand-violet-600 text-slate-900 dark:text-white shadow-xl'
                                    : 'text-slate-500 dark:text-brand-violet-400/60 hover:text-slate-700 dark:hover:text-brand-violet-400'
                                    }`}
                            >
                                All Entries
                            </button>
                            <button
                                onClick={() => setFilterStatus('success')}
                                className={`px-5 py-2 rounded-xl font-black text-[10px] uppercase tracking-widest transition-all ${filterStatus === 'success'
                                    ? 'bg-emerald-500 text-white shadow-xl'
                                    : 'text-slate-500 dark:text-emerald-400/60 hover:text-emerald-600 dark:hover:text-emerald-400'
                                    }`}
                            >
                                Success
                            </button>
                            <button
                                onClick={() => setFilterStatus('failed')}
                                className={`px-5 py-2 rounded-xl font-black text-[10px] uppercase tracking-widest transition-all ${filterStatus === 'failed'
                                    ? 'bg-red-500 text-white shadow-xl'
                                    : 'text-slate-500 dark:text-red-400/60 hover:text-red-600 dark:hover:text-red-400'
                                    }`}
                            >
                                Failed
                            </button>
                        </div>
                    </div>
                </div>


                <div className="divide-y divide-slate-100 dark:divide-white/5">
                    {filteredEntries.length === 0 ? (
                        <div className="p-16 text-center">
                            <div className="w-20 h-20 bg-slate-50 dark:bg-slate-800/50 rounded-full flex items-center justify-center mx-auto mb-6 border border-slate-100 dark:border-slate-700/50">
                                <Shield className="w-10 h-10 text-slate-300 dark:text-slate-600" />
                            </div>
                            <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-2">No Audit Entries Found</h3>
                            <p className="text-slate-500 dark:text-slate-400 max-w-xs mx-auto">
                                {searchTerm || filterStatus !== 'all'
                                    ? 'Try adjusting your search filters to find what you are looking for.'
                                    : 'Start processing documents to see your activity trail here.'}
                            </p>
                        </div>
                    ) : (
                        filteredEntries.map((entry) => (
                            <div key={entry.id} className="p-8 hover:bg-slate-50 dark:hover:bg-brand-violet-600/5 transition-all group">
                                <div className="flex items-start justify-between gap-6">
                                    <div className="flex items-center gap-6 flex-1">
                                        <div
                                            className={`w-14 h-14 rounded-2xl flex items-center justify-center flex-shrink-0 transition-all duration-500 group-hover:rotate-3 shadow-inner ${entry.status === 'success' ? 'bg-emerald-100 dark:bg-emerald-900/20 border border-emerald-200/50 dark:border-emerald-500/20' : 'bg-red-100 dark:bg-red-900/20 border border-red-200/50 dark:border-red-500/20'
                                                }`}
                                        >
                                            {entry.status === 'success' ? (
                                                <CheckCircle className="w-7 h-7 text-emerald-600 dark:text-emerald-400" />
                                            ) : (
                                                <AlertCircle className="w-7 h-7 text-red-600 dark:text-red-400" />
                                            )}
                                        </div>

                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-4 mb-2">
                                                <h3 className="text-lg font-black text-slate-900 dark:text-white truncate transition-colors group-hover:text-brand-violet-600 dark:group-hover:text-brand-violet-400">
                                                    {entry.filename}
                                                </h3>
                                                <span
                                                    className={`px-3 py-1 text-[9px] font-black uppercase tracking-[0.2em] rounded-lg border ${entry.status === 'success'
                                                        ? 'bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-400 border-emerald-200 dark:border-emerald-500/20'
                                                        : 'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-400 border-red-200 dark:border-red-500/20'
                                                        }`}
                                                >
                                                    {entry.status}
                                                </span>
                                            </div>

                                            <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-[11px] font-black uppercase tracking-widest text-slate-500 dark:text-brand-violet-400/60">
                                                <div className="flex items-center gap-2 hover:text-slate-900 dark:hover:text-brand-violet-400 transition-colors">
                                                    <Clock className="w-4 h-4 text-brand-violet-600/50" />
                                                    <span>{formatDate(entry.timestamp)}</span>
                                                </div>
                                                <div className="flex items-center gap-2 hover:text-slate-900 dark:hover:text-brand-violet-400 transition-colors">
                                                    <FileText className="w-4 h-4 text-brand-violet-600/50" />
                                                    <span>{formatFileSize(entry.fileSize)}</span>
                                                </div>
                                                <div className="flex items-center gap-2 hover:text-slate-900 dark:hover:text-brand-violet-400 transition-colors">
                                                    <Shield className="w-4 h-4 text-emerald-500/50" />
                                                    <span>{entry.entitiesFound} Redactions</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="text-right flex flex-col items-end">
                                        <div className="text-base font-black text-slate-900 dark:text-white font-mono bg-slate-100 dark:bg-brand-obsidian-light/30 px-3 py-1 rounded-xl border border-slate-200 dark:border-white/5 shadow-inner group-hover:border-brand-violet-600/30 transition-all">
                                            {entry.processingTime}<span className="text-[10px] ml-0.5 opacity-50">ms</span>
                                        </div>
                                        <div className="text-[9px] font-black text-slate-400 dark:text-brand-violet-400/40 uppercase tracking-widest mt-2 px-1">Latency</div>
                                    </div>
                                </div>
                            </div>

                        ))
                    )}
                </div>
            </div>
        </div>
    );
}

