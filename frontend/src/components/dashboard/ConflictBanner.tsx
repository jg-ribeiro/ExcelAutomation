import React from 'react';
import { AlertTriangle, ArrowRight, ShieldAlert } from 'lucide-react';
import { Alert } from '../../types';

interface ConflictBannerProps {
  alerts: Alert[];
  onNavigateToAlerts: () => void;
}

export const ConflictBanner: React.FC<ConflictBannerProps> = ({ alerts, onNavigateToAlerts }) => {
  const pending = alerts.filter(a => a.status === 'pending' || a.status === 'auto_paused');
  if (pending.length === 0) return null;

  const topAlert = pending[0];
  const isAutoPaused = topAlert.status === 'auto_paused';

  return (
    <div className={`rounded-xl border p-4 shadow-sm transition-all duration-200 ${
      isAutoPaused 
        ? 'bg-rose-50 border-rose-300 text-rose-900' 
        : 'bg-amber-50 border-amber-300 text-amber-900'
    }`}>
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div className="flex items-start space-x-3">
          <div className={`p-2 rounded-lg mt-0.5 sm:mt-0 ${
            isAutoPaused ? 'bg-rose-100 text-rose-700' : 'bg-amber-100 text-amber-700'
          }`}>
            {isAutoPaused ? <ShieldAlert className="w-5 h-5" /> : <AlertTriangle className="w-5 h-5" />}
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-sm whitespace-nowrap">
                {isAutoPaused ? 'Job Pausado Automaticamente' : 'Risco de Sobreposição Detectado'}
              </span>
              <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase whitespace-nowrap ${
                isAutoPaused ? 'bg-rose-200 text-rose-800' : 'bg-amber-200 text-amber-800'
              }`}>
                {topAlert.job_name || `Job #${topAlert.job_id}`}
              </span>
            </div>
            <p className="text-xs mt-1 leading-relaxed max-w-3xl">
              {topAlert.message}
            </p>
          </div>
        </div>

        <button
          onClick={onNavigateToAlerts}
          className={`shrink-0 flex items-center space-x-1.5 px-4 py-2 rounded-lg text-xs font-semibold shadow-sm transition-all duration-150 active:scale-98 ${
            isAutoPaused
              ? 'bg-rose-600 hover:bg-rose-700 text-white'
              : 'bg-amber-600 hover:bg-amber-700 text-white'
          }`}
        >
          <span>Gerenciar Conflitos ({pending.length})</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};
