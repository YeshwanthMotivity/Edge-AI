import { Shield, Sun, Moon } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';

type View = 'dashboard' | 'process' | 'audit' | 'about';

interface HeaderProps {
    currentView: View;
    onNavigate: (view: View) => void;
}

export default function Header({ onNavigate }: HeaderProps) {
    const { theme, toggleTheme } = useTheme();

    return (
        <header className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 shadow-sm transition-colors duration-200">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                <div className="flex items-center justify-between">
                    <button
                        onClick={() => onNavigate('dashboard')}
                        className="flex items-center gap-3 group"
                    >
                        <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-cyan-600 rounded-lg flex items-center justify-center shadow-md group-hover:shadow-lg transition-shadow">
                            <Shield className="w-6 h-6 text-white" />
                        </div>
                        <div className="text-left">
                            <h1 className="text-xl font-bold text-slate-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-cyan-400 transition-colors">
                                Edge Policy AI
                            </h1>
                            <p className="text-xs text-slate-500 dark:text-slate-400">Privacy-First Document Processing</p>
                        </div>
                    </button>

                    <div className="flex items-center gap-4">
                        <button
                            onClick={toggleTheme}
                            className="p-2 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
                            aria-label="Toggle dark mode"
                        >
                            {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
                        </button>
                        <div className="flex items-center gap-2 px-3 py-1.5 bg-green-50 dark:bg-green-900/30 border border-green-200 dark:border-green-800/50 rounded-full">
                            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                            <span className="text-xs font-medium text-green-700 dark:text-green-400">Local Processing</span>
                        </div>
                    </div>
                </div>
            </div>
        </header>
    );
}
