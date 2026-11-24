import React from 'react';
import { Clock } from 'lucide-react';

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
      <div className="flex items-center space-x-1.5 text-xs text-slate-400 italic">
        <Clock className="w-3.5 h-3.5 text-slate-300 shrink-0" />
        <span>Aguardando execuções para calcular média</span>
      </div>
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
      <div className="flex items-center justify-between text-xs">
        <span className="text-slate-600 font-medium">Duração média:</span>
        <span className="font-semibold text-slate-900 bg-white px-2 py-0.5 rounded border border-slate-200">
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
      <div className="flex items-center justify-between text-xs gap-1.5">
        <span className="text-slate-600 font-medium whitespace-nowrap">
          Duração média: <strong className="text-slate-900">{durText}</strong>
          <span className="text-slate-400 font-normal ml-1">/ {scheduleValue}</span>
        </span>
        <span className={`px-2 py-0.5 rounded-full text-[10px] border whitespace-nowrap shrink-0 ${badgeTone}`}>
          {label} ({percentage}%)
        </span>
      </div>

      <div className="w-full h-2 bg-slate-200/70 rounded-full overflow-hidden border border-slate-200">
        <div 
          className={`h-full transition-all duration-500 rounded-full ${barColor}`}
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>
    </div>
  );
};
