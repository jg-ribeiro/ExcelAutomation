import React from 'react';

interface DurationGaugeProps {
  avgDurationSeconds: number | null | undefined;
  durationRatio: number | null | undefined;
  scheduleType: string;
  scheduleValue: string;
}

export const DurationGauge: React.FC<DurationGaugeProps> = ({
  avgDurationSeconds,
  durationRatio,
  scheduleType,
  scheduleValue
}) => {
  if (avgDurationSeconds == null) {
    return (
      <span className="text-xs text-slate-400 italic">
        Aguardando execuções para calcular média
      </span>
    );
  }

  const formatDuration = (secs: number) => {
    const mins = Math.floor(secs / 60);
    const remainder = Math.round(secs % 60);
    if (mins === 0) return `${remainder}s`;
    return `${mins}m ${remainder > 0 ? `${remainder}s` : ''}`;
  };

  const durText = formatDuration(avgDurationSeconds);

  if (scheduleType !== 'interval' || durationRatio == null) {
    return (
      <div className="flex items-center space-x-2">
        <span className="text-xs font-medium text-slate-700">Duração média:</span>
        <span className="text-xs font-semibold text-slate-900 bg-slate-100 px-2 py-0.5 rounded">
          {durText}
        </span>
      </div>
    );
  }

  const percentage = Math.min(Math.round(durationRatio * 100), 200);

  // Cores por nível de ocupação do intervalo
  let barColor = 'bg-emerald-500';
  let badgeTone = 'text-emerald-700 bg-emerald-50 border-emerald-200';
  let label = 'Margem Segura';

  if (durationRatio >= 1.0) {
    barColor = 'bg-rose-600 animate-pulse';
    badgeTone = 'text-rose-700 bg-rose-50 border-rose-200 font-bold';
    label = 'Sobreposição Crítica';
  } else if (durationRatio >= 0.85) {
    barColor = 'bg-amber-500';
    badgeTone = 'text-amber-700 bg-amber-50 border-amber-200 font-bold';
    label = 'Risco Iminente';
  } else if (durationRatio >= 0.5) {
    barColor = 'bg-blue-500';
    badgeTone = 'text-blue-700 bg-blue-50 border-blue-200';
    label = 'Atenção';
  }

  return (
    <div className="w-full space-y-1.5">
      <div className="flex items-center justify-between text-xs gap-2">
        <span className="text-slate-600 font-medium whitespace-nowrap">
          Duração média: <strong className="text-slate-900">{durText}</strong> / {scheduleValue}
        </span>
        <span className={`px-2 py-0.5 rounded-full text-[10px] border whitespace-nowrap ${badgeTone}`}>
          {label} ({percentage}%)
        </span>
      </div>

      <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden border border-slate-200">
        <div 
          className={`h-full transition-all duration-500 rounded-full ${barColor}`}
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>
    </div>
  );
};
