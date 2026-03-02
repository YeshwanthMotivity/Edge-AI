import { useState } from 'react';
import { Play, Download, Eye, EyeOff, Loader2, AlertCircle } from 'lucide-react';
import FileUpload from './FileUpload';
import EntityVisualization from './EntityVisualization';

interface Entity {
    type: string;
    value: string;
    start: number;
    end: number;
    score?: number; // Backend might send 'score' instead of 'confidence'
    confidence?: number;
}

interface ProcessingResult {
    original_text: string;
    redacted_text: string;
    entities_detected: number;
    entities_redacted: number;
    entity_summary: Record<string, number>;
    processing_time_ms: number;
    entities: Entity[];
    document_id?: string;
    sanitized_path?: string;
    signed_path?: string;
}

export default function ProcessDocument() {
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [isProcessing, setIsProcessing] = useState(false);
    const [result, setResult] = useState<ProcessingResult | null>(null);
    const [showOriginal, setShowOriginal] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const handleFileSelect = (file: File) => {
        setSelectedFile(file);
        setResult(null);
        setError(null);
    };

    const handleClearFile = () => {
        setSelectedFile(null);
        setResult(null);
        setError(null);
    };

    const handleProcess = async () => {
        if (!selectedFile) return;

        setIsProcessing(true);
        setError(null);

        try {
            const formData = new FormData();
            formData.append('file', selectedFile);

            const response = await fetch('/api/v1/process', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                throw new Error('Processing failed');
            }

            const data = await response.json();
            setResult(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred during processing');
        } finally {
            setIsProcessing(false);
        }
    };

    const handleDownload = async () => {
        if (!result) return;

        if (result.document_id) {
            try {
                // Determine preferred download type: signed if available, otherwise sanitized
                const preferredType = result.signed_path ? 'signed' : 'sanitized';
                const downloadUrl = `/api/v1/documents/${result.document_id}/download?type=${preferredType}`;

                const response = await fetch(downloadUrl);

                // If signed fails (404), try sanitized as a fallback
                let finalResponse = response;
                let actualType = preferredType;

                if (!response.ok && preferredType === 'signed') {
                    console.warn("Signed document missing, falling back to sanitized...");
                    const fallbackResponse = await fetch(`/api/v1/documents/${result.document_id}/download?type=sanitized`);
                    if (fallbackResponse.ok) {
                        finalResponse = fallbackResponse;
                        actualType = 'sanitized';
                    }
                }

                if (!finalResponse.ok) throw new Error('Failed to download document from server');

                const blob = await finalResponse.blob();
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;

                // Build clever filename based on original
                let filename = `redacted_document_${actualType}.pdf`;
                if (selectedFile?.name) {
                    const parts = selectedFile.name.split('.');
                    const ext = parts.length > 1 ? parts.pop() : 'pdf';
                    filename = `${parts.join('.')}_${actualType}.${ext}`;
                }

                a.download = filename;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
                return;
            } catch (err) {
                console.error("Binary download failed:", err);
            }
        }

        // Final fallback: Text only (with correct extension!)
        const blob = new Blob([result.redacted_text || ""], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const baseName = selectedFile?.name ? selectedFile.name.split('.')[0] : 'document';
        a.download = `redacted_${baseName}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
            <div className="mb-8">
                <h2 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">Process Document</h2>
                <p className="text-slate-600 dark:text-slate-400">
                    Upload a document to detect and redact sensitive information with AI-powered analysis
                </p>
            </div>

            <div className="space-y-6">
                <FileUpload
                    onFileSelect={handleFileSelect}
                    selectedFile={selectedFile}
                    onClear={handleClearFile}
                />

                {selectedFile && !result && (
                    <div className="flex justify-end">
                        <button
                            onClick={handleProcess}
                            disabled={isProcessing}
                            className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:bg-slate-400 disabled:dark:bg-slate-700 disabled:cursor-not-allowed transition-colors shadow-sm hover:shadow-md"
                        >
                            {isProcessing ? (
                                <>
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                    Processing...
                                </>
                            ) : (
                                <>
                                    <Play className="w-5 h-5" />
                                    Process Document
                                </>
                            )}
                        </button>
                    </div>
                )}

                {error && (
                    <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex items-start gap-3">
                        <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
                        <div>
                            <h4 className="text-sm font-semibold text-red-900 dark:text-red-400 mb-1">Processing Error</h4>
                            <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
                        </div>
                    </div>
                )}

                {result && (
                    <>
                        <div className="bg-white dark:bg-slate-900/50 rounded-lg border border-slate-200 dark:border-slate-800 shadow-sm p-6">
                            <div className="flex items-center justify-between mb-6">
                                <div>
                                    <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-1">Processing Complete</h3>
                                    <p className="text-sm text-slate-600 dark:text-slate-400">
                                        Found {result.entities_detected || 0} sensitive entities ({result.entities_redacted || 0} redacted) in {result.processing_time_ms ? Math.round(result.processing_time_ms) : 0}ms
                                    </p>
                                </div>
                                <div className="flex items-center gap-3">
                                    <button
                                        onClick={() => setShowOriginal(!showOriginal)}
                                        className="flex items-center gap-2 px-4 py-2 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-lg font-medium hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors text-sm"
                                    >
                                        {showOriginal ? (
                                            <>
                                                <EyeOff className="w-4 h-4" />
                                                Hide Original
                                            </>
                                        ) : (
                                            <>
                                                <Eye className="w-4 h-4" />
                                                Show Original
                                            </>
                                        )}
                                    </button>
                                    <button
                                        onClick={handleDownload}
                                        className="flex items-center gap-2 px-4 py-2 bg-green-600 dark:bg-emerald-600 text-white rounded-lg font-medium hover:bg-green-700 dark:hover:bg-emerald-700 transition-colors text-sm shadow-sm"
                                    >
                                        <Download className="w-4 h-4" />
                                        Download
                                    </button>
                                </div>
                            </div>

                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                {showOriginal && (
                                    <div>
                                        <div className="mb-3 flex items-center justify-between">
                                            <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300">Original Text</h4>
                                            <span className="text-xs text-slate-500 dark:text-slate-400">Sensitive Data Visible</span>
                                        </div>
                                        <div className="bg-slate-50 dark:bg-slate-950 rounded-lg p-4 border border-slate-200 dark:border-slate-800 max-h-96 overflow-y-auto scrollbar-thin scrollbar-thumb-slate-300 dark:scrollbar-thumb-slate-700">
                                            <pre className="text-sm text-slate-700 dark:text-slate-300 whitespace-pre-wrap font-mono">
                                                {result.original_text || "Original text not available"}
                                            </pre>
                                        </div>
                                    </div>
                                )}

                                <div className={showOriginal ? '' : 'lg:col-span-2'}>
                                    <div className="mb-3 flex items-center justify-between">
                                        <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300">Redacted Text</h4>
                                        <span className="text-xs text-green-600 dark:text-emerald-500 font-medium">Privacy Protected</span>
                                    </div>
                                    <div className="bg-green-50 dark:bg-indigo-500/5 rounded-lg p-4 border border-green-200 dark:border-slate-800 max-h-96 overflow-y-auto scrollbar-thin scrollbar-thumb-slate-300 dark:scrollbar-thumb-slate-700">
                                        <pre className="text-sm text-slate-700 dark:text-slate-300 whitespace-pre-wrap font-mono">
                                            {result.redacted_text ? result.redacted_text.split(/(\[REDACTED_[A-Z_]+\])/).map((part, i) => (
                                                part.startsWith('[REDACTED') ?
                                                    <span key={i} className="px-1.5 py-0.5 mx-0.5 rounded bg-slate-200 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-indigo-700 dark:text-indigo-400 font-bold text-[11px] select-all cursor-help hover:bg-slate-300 dark:hover:bg-slate-700 transition-colors">
                                                        {part}
                                                    </span> : part
                                            )) : "Redacted text not available"}
                                        </pre>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Passing empty array for now since backend stops sending raw entities to frontend */}
                        <EntityVisualization entities={result.entities || []} entityCountSummary={result.entity_summary} />
                    </>
                )}
            </div>
        </div>
    );
}
