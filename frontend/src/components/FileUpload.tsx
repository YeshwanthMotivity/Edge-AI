import { useState, useRef } from 'react';
import { Upload, File, X, CheckCircle } from 'lucide-react';

interface FileUploadProps {
    onFileSelect: (file: File) => void;
    selectedFile: File | null;
    onClear: () => void;
}

export default function FileUpload({ onFileSelect, selectedFile, onClear }: FileUploadProps) {
    const [isDragging, setIsDragging] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleDragEnter = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(true);
    };

    const handleDragLeave = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
    };

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);

        const files = e.dataTransfer.files;
        if (files && files.length > 0) {
            const file = files[0];
            if (file.type === 'application/pdf' || file.type === 'text/plain') {
                onFileSelect(file);
            }
        }
    };

    const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = e.target.files;
        if (files && files.length > 0) {
            onFileSelect(files[0]);
        }
    };

    const formatFileSize = (bytes: number) => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    };

    if (selectedFile) {
        return (
            <div className="bg-white dark:bg-brand-obsidian-light/30 rounded-3xl border-2 border-emerald-200 dark:border-emerald-500/20 p-8 shadow-2xl transition-all">
                <div className="flex items-start justify-between">
                    <div className="flex items-start gap-6">
                        <div className="w-14 h-14 bg-emerald-100 dark:bg-emerald-900/30 rounded-2xl flex items-center justify-center flex-shrink-0 shadow-inner">
                            <CheckCircle className="w-8 h-8 text-emerald-600 dark:text-emerald-500" />
                        </div>
                        <div className="flex-1">
                            <h3 className="text-lg font-black text-slate-900 dark:text-white mb-1 tracking-tight">Source Ready</h3>
                            <p className="text-base text-slate-600 dark:text-brand-violet-400 font-bold italic">{selectedFile.name}</p>
                            <div className="flex items-center gap-4 text-xs font-black uppercase tracking-widest text-slate-500 dark:text-brand-violet-400/60 mt-2">
                                <span>{formatFileSize(selectedFile.size)}</span>
                                <span className="w-1 h-1 bg-slate-300 dark:bg-brand-violet-600 rounded-full"></span>
                                <span>{selectedFile.type || 'Binary Data'}</span>
                            </div>
                        </div>
                    </div>
                    <button
                        onClick={onClear}
                        className="p-3 bg-slate-100 dark:bg-brand-violet-950/40 hover:bg-red-100 dark:hover:bg-red-900/40 rounded-xl transition-all group border border-transparent dark:border-brand-violet-600/20"
                        title="Remove file"
                    >
                        <X className="w-5 h-5 text-slate-500 dark:text-brand-violet-400 group-hover:text-red-500" />
                    </button>
                </div>
            </div>

        );
    }

    return (
        <div
            onDragEnter={handleDragEnter}
            onDragLeave={handleDragLeave}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            className={`
        border-2 border-dashed rounded-4xl p-16 text-center transition-all cursor-pointer group
        ${isDragging
                    ? 'border-brand-violet-600 bg-brand-violet-600/5 shadow-[0_0_30px_rgba(107,70,255,0.1)]'
                    : 'border-slate-300 dark:border-white/10 bg-white dark:bg-brand-obsidian-light/20 hover:border-brand-violet-600/50 dark:hover:border-brand-violet-600/40 hover:bg-slate-50 dark:hover:bg-brand-obsidian-light/30'
                }
      `}
            onClick={() => fileInputRef.current?.click()}
        >
            <div className="max-w-md mx-auto">
                <div className={`
          w-20 h-20 mx-auto mb-6 rounded-3xl flex items-center justify-center transition-all duration-500 shadow-inner group-hover:scale-110 group-hover:rotate-3
          ${isDragging ? 'bg-brand-violet-600 text-white shadow-brand-violet-600/40 rotate-12' : 'bg-slate-100 dark:bg-brand-violet-950/40 text-slate-400 dark:text-brand-violet-400/60'}
        `}>
                    <Upload className={`w-10 h-10 ${isDragging ? 'text-white' : ''}`} />
                </div>

                <h3 className="text-2xl font-black text-slate-900 dark:text-white mb-3 tracking-tight">
                    {isDragging ? 'Ready for Capture' : 'Secure Document Ingest'}
                </h3>

                <p className="text-base text-slate-600 dark:text-slate-400 mb-6 font-medium">
                    Drag and drop your file here, or <span className="text-brand-violet-600 dark:text-brand-violet-400 font-bold underline decoration-brand-violet-600/30">browse securely</span>
                </p>

                <div className="flex items-center justify-center gap-3 text-[10px] font-black uppercase tracking-widest text-slate-400 dark:text-brand-violet-400/40">
                    <File className="w-4 h-4" />
                    <span>Compliant with PDF & Plaintext</span>
                </div>


                <input
                    ref={fileInputRef}
                    type="file"
                    accept=".pdf,.txt,text/plain,application/pdf"
                    onChange={handleFileInput}
                    className="hidden"
                />
            </div>
        </div>
    );
}
