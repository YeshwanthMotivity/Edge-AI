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
        <header className="bg-white/90 dark:bg-brand-obsidian/90 backdrop-blur-xl border-b border-slate-200 dark:border-white/10 shadow-2xl transition-all duration-500 sticky top-0 z-[60]">

            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5">
                <div className="flex items-center justify-between">
                    <button
                        onClick={() => onNavigate('dashboard')}
                        className="flex items-center gap-4 group transition-transform active:scale-95"
                    >
                        <div className="w-12 h-12 bg-gradient-to-br from-brand-violet-600 to-brand-violet-400 rounded-2xl flex items-center justify-center shadow-[0_0_20px_rgba(107,70,255,0.3)] group-hover:shadow-[0_0_30px_rgba(107,70,255,0.5)] transition-all duration-500 group-hover:rotate-3">
                            <Shield className="w-7 h-7 text-white" />
                        </div>

                        <div className="text-left">
                            <h1 className="text-2xl font-black tracking-tight text-slate-900 dark:text-white group-hover:text-brand-violet-600 dark:group-hover:text-brand-violet-400 transition-colors duration-300">
                                EdgeAI Policy
                            </h1>
                            <p className="text-xs text-slate-500 dark:text-brand-violet-400/60 font-black uppercase tracking-[0.2em]">Privacy-First AI Sanitization</p>
                        </div>
                    </button>


                    <div className="flex items-center gap-6">
                        <button
                            onClick={toggleTheme}
                            className="p-3 rounded-2xl bg-slate-100 dark:bg-brand-violet-950/50 text-slate-600 dark:text-brand-violet-400 border border-transparent dark:border-brand-violet-600/20 hover:bg-slate-200 dark:hover:bg-brand-violet-600/20 transition-all duration-300 shadow-sm"
                            aria-label="Toggle dark mode"
                        >
                            {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
                        </button>

                        <div className="flex items-center gap-3 px-5 py-2 bg-brand-violet-950/30 dark:bg-brand-violet-950/40 border border-brand-violet-600/20 rounded-2xl shadow-inner group hover:border-brand-violet-600/50 transition-colors">
                            <div className="w-2.5 h-2.5 bg-brand-violet-600 rounded-full animate-[pulse_2s_infinite] shadow-[0_0_10px_rgba(107,70,255,0.6)]"></div>
                            <span className="text-xs font-black text-brand-violet-600 dark:text-brand-violet-400 uppercase tracking-widest">Local Mode</span>
                        </div>
                    </div>
                </div>
            </div>
        </header>
    );
}

