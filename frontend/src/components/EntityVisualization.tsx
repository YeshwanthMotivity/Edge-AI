import { Shield, Mail, CreditCard, Phone, User, MapPin, Calendar, Hash } from 'lucide-react';

interface Entity {
    type: string;
    value: string;
    start: number;
    end: number;
    score?: number;
    confidence?: number;
}

interface EntityVisualizationProps {
    entities: Entity[];
    entityCountSummary?: Record<string, number>;
}

const getEntityIcon = (type: string) => {
    const iconMap: Record<string, React.ReactNode> = {
        EMAIL: <Mail className="w-4 h-4" />,
        CREDIT_CARD: <CreditCard className="w-4 h-4" />,
        SSN: <Shield className="w-4 h-4" />,
        PHONE: <Phone className="w-4 h-4" />,
        PERSON: <User className="w-4 h-4" />,
        LOCATION: <MapPin className="w-4 h-4" />,
        DATE: <Calendar className="w-4 h-4" />,
        IP_ADDRESS: <Hash className="w-4 h-4" />,
    };
    return iconMap[type] || <Hash className="w-4 h-4" />;
};

const getEntityColor = (type: string) => {
    const colorMap: Record<string, { bg: string; text: string; border: string }> = {
        EMAIL: { bg: 'bg-brand-violet-600/10 dark:bg-brand-violet-950/40', text: 'text-brand-violet-600 dark:text-brand-violet-400', border: 'border-brand-violet-600/20 dark:border-brand-violet-600/30' },
        CREDIT_CARD: { bg: 'bg-rose-50 dark:bg-rose-900/20', text: 'text-rose-700 dark:text-rose-400', border: 'border-rose-200 dark:border-rose-800' },
        SSN: { bg: 'bg-indigo-50 dark:bg-indigo-900/20', text: 'text-indigo-700 dark:text-indigo-400', border: 'border-indigo-200 dark:border-indigo-800' },
        PHONE: { bg: 'bg-brand-violet-600/5 dark:bg-brand-obsidian-light/30', text: 'text-brand-violet-600 dark:text-brand-violet-400', border: 'border-brand-violet-600/20 dark:border-white/5' },
        PERSON: { bg: 'bg-violet-50 dark:bg-violet-900/20', text: 'text-violet-700 dark:text-violet-400', border: 'border-violet-200 dark:border-violet-800' },
        LOCATION: { bg: 'bg-slate-50 dark:bg-slate-800/50', text: 'text-slate-700 dark:text-slate-300', border: 'border-slate-200 dark:border-slate-700' },
        DATE: { bg: 'bg-amber-50 dark:bg-amber-900/20', text: 'text-amber-700 dark:text-amber-400', border: 'border-amber-200 dark:border-amber-800' },
        IP_ADDRESS: { bg: 'bg-blue-50 dark:bg-blue-900/20', text: 'text-blue-700 dark:text-blue-400', border: 'border-blue-200 dark:border-blue-800' },
    };
    return colorMap[type] || { bg: 'bg-slate-50 dark:bg-slate-800/50', text: 'text-slate-700 dark:text-slate-300', border: 'border-slate-200 dark:border-slate-700' };
};



const getConfidenceLabel = (confidence: number) => {
    if (confidence >= 0.9) return { label: 'High', color: 'text-green-600 dark:text-emerald-400' };
    if (confidence >= 0.7) return { label: 'Medium', color: 'text-amber-600 dark:text-amber-400' };
    return { label: 'Low', color: 'text-orange-600 dark:text-orange-400' };
};

export default function EntityVisualization({ entities, entityCountSummary }: EntityVisualizationProps) {
    const entityCounts = entityCountSummary || entities.reduce((acc, entity) => {
        acc[entity.type] = (acc[entity.type] || 0) + 1;
        return acc;
    }, {} as Record<string, number>);

    const uniqueTypes = Object.keys(entityCounts);

    return (
        <div className="bg-white dark:bg-brand-obsidian-light/30 border border-slate-100 dark:border-white/5 rounded-3xl shadow-2xl p-8 group">

            <div className="mb-8">
                <h3 className="text-2xl font-black text-slate-900 dark:text-white mb-2 tracking-tight">Intelligence Report</h3>
                <p className="text-sm font-bold text-slate-500 dark:text-brand-violet-400/60 uppercase tracking-widest">
                    Machine Learning entity extraction with high-fidelity validation
                </p>
            </div>


            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                {uniqueTypes.map((type) => {
                    const colors = getEntityColor(type);
                    return (
                        <div
                            key={type}
                            className={`${colors.bg} border ${colors.border} rounded-2xl p-5 shadow-inner transition-transform hover:scale-105 active:scale-95 cursor-default`}
                        >
                            <div className={`flex items-center gap-3 mb-3 ${colors.text}`}>
                                <div className="p-2 bg-white/10 rounded-lg">
                                    {getEntityIcon(type)}
                                </div>
                                <span className="text-[10px] font-black uppercase tracking-[0.2em]">{type}</span>
                            </div>
                            <div className="text-3xl font-black text-slate-900 dark:text-white tracking-tighter">{entityCounts[type]}</div>
                        </div>
                    );
                })}

            </div>

            <div className="space-y-3">
                <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">Entity Details</h4>
                {entities.length === 0 ? (
                    <div className="text-center py-8 text-slate-500 dark:text-slate-400">
                        {uniqueTypes.length > 0
                            ? "Raw entity locations have been securely stripped from the response by the gateway to prevent PII leakage."
                            : "No sensitive entities detected"}
                    </div>
                ) : (
                    <div className="space-y-2">
                        {entities.map((entity, index) => {
                            const colors = getEntityColor(entity.type);
                            const conf = entity.confidence ?? entity.score ?? 0;
                            const confidenceInfo = getConfidenceLabel(conf);
                            return (
                                <div
                                    key={index}
                                    className={`${colors.bg} border ${colors.border} rounded-lg p-4 flex items-start justify-between`}
                                >
                                    <div className="flex items-start gap-3 flex-1">
                                        <div className={`${colors.text} mt-1`}>
                                            {getEntityIcon(entity.type)}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2 mb-1">
                                                <span className={`text-xs font-semibold uppercase tracking-wide ${colors.text}`}>
                                                    {entity.type}
                                                </span>
                                                <span className="text-xs text-slate-500 dark:text-slate-400">
                                                    Position: {entity.start}-{entity.end}
                                                </span>
                                            </div>
                                            <div className="font-mono text-sm text-slate-700 dark:text-slate-300 break-all">
                                                {entity.value}
                                            </div>
                                        </div>
                                    </div>
                                    <div className="text-right ml-4">
                                        <div className={`text-xs font-semibold ${confidenceInfo.color} mb-1`}>
                                            {confidenceInfo.label}
                                        </div>
                                        <div className="text-xs text-slate-500 dark:text-slate-400">
                                            {Math.round(conf * 100)}%
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>
        </div>
    );
}
