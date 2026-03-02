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

    useEffect(() => {
        fetchAuditLog();
    }, []);

    const fetchAuditLog = async () => {
        try {
            const response = await fetch('/api/v1/audit');
            if (response.ok) {
                const data = await response.json();
                setAuditEntries(data.entries || []);
            }
        } catch (err) {
            console.error('Failed to fetch audit log:', err);
        }
    };

    const filteredEntries = auditEntries.filter((entry) => {
        const matchesSearch = entry.filename.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesFilter = filterStatus === 'all' || entry.status === filterStatus;
        return matchesSearch && matchesFilter;
    });

    const formatDate = (timestamp: string) => {
        return new Date(timestamp).toLocaleString('en-US', {
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
            <div className="mb-8 flex flex-col md:flex-row md:items-end md:justify-between gap-4">
                <div>
                    <h2 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">Audit Log</h2>
                    <p className="text-slate-600 dark:text-slate-400">
                        Complete history of all document processing activities and security validations
                    </p>
                </div>
                <button
                    onClick={() => window.open('/api/v1/audit/export', '_blank')}
                    className="flex items-center justify-center gap-2 bg-slate-900 dark:bg-white text-white dark:text-slate-900 px-4 py-2.5 rounded-lg font-semibold hover:bg-slate-800 dark:hover:bg-slate-100 transition-all shrink-0 shadow-sm"
                >
                    <Download className="w-5 h-5" />
                    <span>Download Logs (CSV)</span>
                </button>
            </div>

            <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 shadow-sm transition-colors duration-200">
                <div className="p-6 border-b border-slate-200 dark:border-slate-800">
                    <div className="flex flex-col sm:flex-row gap-4">
                        <div className="flex-1 relative">
                            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400 dark:text-slate-500" />
                            <input
                                type="text"
                                placeholder="Search by filename..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="w-full pl-10 pr-4 py-2 border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 text-slate-900 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors duration-200"
                            />
                        </div>

                        <div className="flex gap-2">
                            <button
                                onClick={() => setFilterStatus('all')}
                                className={`px-4 py-2 rounded-lg font-medium text-sm transition-colors ${filterStatus === 'all'
                                    ? 'bg-blue-600 dark:bg-blue-500 text-white'
                                    : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
                                    }`}
                            >
                                All
                            </button>
                            <button
                                onClick={() => setFilterStatus('success')}
                                className={`px-4 py-2 rounded-lg font-medium text-sm transition-colors ${filterStatus === 'success'
                                    ? 'bg-green-600 dark:bg-green-500 text-white'
                                    : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
                                    }`}
                            >
                                Success
                            </button>
                            <button
                                onClick={() => setFilterStatus('failed')}
                                className={`px-4 py-2 rounded-lg font-medium text-sm transition-colors ${filterStatus === 'failed'
                                    ? 'bg-red-600 dark:bg-red-500 text-white'
                                    : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
                                    }`}
                            >
                                Failed
                            </button>
                        </div>
                    </div>
                </div>

                <div className="divide-y divide-slate-200 dark:divide-slate-800">
                    {filteredEntries.length === 0 ? (
                        <div className="p-12 text-center">
                            <div className="w-16 h-16 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center mx-auto mb-4">
                                <Shield className="w-8 h-8 text-slate-400 dark:text-slate-500" />
                            </div>
                            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">No Audit Entries</h3>
                            <p className="text-slate-600 dark:text-slate-400">
                                {searchTerm || filterStatus !== 'all'
                                    ? 'No entries match your search criteria'
                                    : 'Process your first document to see audit entries here'}
                            </p>
                        </div>
                    ) : (
                        filteredEntries.map((entry) => (
                            <div key={entry.id} className="p-6 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                                <div className="flex items-start justify-between">
                                    <div className="flex items-start gap-4 flex-1">
                                        <div
                                            className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${entry.status === 'success' ? 'bg-green-100 dark:bg-green-900/30' : 'bg-red-100 dark:bg-red-900/30'
                                                }`}
                                        >
                                            {entry.status === 'success' ? (
                                                <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />
                                            ) : (
                                                <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400" />
                                            )}
                                        </div>

                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-3 mb-2">
                                                <h3 className="text-sm font-semibold text-slate-900 dark:text-white truncate">
                                                    {entry.filename}
                                                </h3>
                                                <span
                                                    className={`px-2 py-0.5 text-xs font-medium rounded-full ${entry.status === 'success'
                                                        ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                                                        : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
                                                        }`}
                                                >
                                                    {entry.status}
                                                </span>
                                            </div>

                                            <div className="flex flex-wrap items-center gap-4 text-sm text-slate-600 dark:text-slate-400">
                                                <div className="flex items-center gap-1.5">
                                                    <Clock className="w-4 h-4" />
                                                    <span>{formatDate(entry.timestamp)}</span>
                                                </div>
                                                <div className="flex items-center gap-1.5">
                                                    <FileText className="w-4 h-4" />
                                                    <span>{formatFileSize(entry.fileSize)}</span>
                                                </div>
                                                <div className="flex items-center gap-1.5">
                                                    <Shield className="w-4 h-4" />
                                                    <span>{entry.entitiesFound} entities detected</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="text-right ml-4">
                                        <div className="text-sm font-semibold text-slate-900 dark:text-white">
                                            {entry.processingTime}ms
                                        </div>
                                        <div className="text-xs text-slate-500 dark:text-slate-500">Processing Time</div>
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
