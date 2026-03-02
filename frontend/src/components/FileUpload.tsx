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
            <div className="bg-white dark:bg-slate-900/50 rounded-lg border-2 border-green-200 dark:border-emerald-800/50 p-6">
                <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4">
                        <div className="w-12 h-12 bg-green-100 dark:bg-emerald-900/30 rounded-lg flex items-center justify-center flex-shrink-0">
                            <CheckCircle className="w-6 h-6 text-green-600 dark:text-emerald-500" />
                        </div>
                        <div className="flex-1">
                            <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-1">File Selected</h3>
                            <p className="text-sm text-slate-600 dark:text-slate-300 mb-2">{selectedFile.name}</p>
                            <div className="flex items-center gap-4 text-xs text-slate-500 dark:text-slate-400">
                                <span>{formatFileSize(selectedFile.size)}</span>
                                <span>{selectedFile.type || 'Unknown type'}</span>
                            </div>
                        </div>
                    </div>
                    <button
                        onClick={onClear}
                        className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
                        title="Remove file"
                    >
                        <X className="w-5 h-5 text-slate-400 dark:text-slate-500" />
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
        border-2 border-dashed rounded-lg p-12 text-center transition-all cursor-pointer
        ${isDragging
                    ? 'border-blue-500 bg-blue-50 dark:border-indigo-500 dark:bg-indigo-500/10'
                    : 'border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900/30 hover:border-blue-400 dark:hover:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-900/50'
                }
      `}
            onClick={() => fileInputRef.current?.click()}
        >
            <div className="max-w-md mx-auto">
                <div className={`
          w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center transition-colors
          ${isDragging ? 'bg-blue-100 dark:bg-indigo-900/50' : 'bg-slate-100 dark:bg-slate-800'}
        `}>
                    <Upload className={`w-8 h-8 ${isDragging ? 'text-blue-600 dark:text-indigo-400' : 'text-slate-400 dark:text-slate-500'}`} />
                </div>

                <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
                    {isDragging ? 'Drop your file here' : 'Upload Document'}
                </h3>

                <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
                    Drag and drop your file here, or click to browse
                </p>

                <div className="flex items-center justify-center gap-2 text-xs text-slate-500 dark:text-slate-500">
                    <File className="w-4 h-4" />
                    <span>Supported formats: PDF, TXT</span>
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
