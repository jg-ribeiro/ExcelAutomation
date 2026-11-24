import React from 'react';
import { 
  FileSpreadsheet, 
  PlayCircle, 
  Layers, 
  AlertTriangle,
  CheckCircle2,
  Clock
} from 'lucide-react';
import { SystemStatus } from '../../types';

interface KpiCardsProps {
  status: SystemStatus | null;
  onNavigate: (tab: string) => void;
}

export const KpiCards: React.FC<KpiCardsProps> = ({ status, onNavigate }) => {
  const totalJobs = status?.total_jobs ?? 0;
  const activeJobs = status?.active_jobs ?? 0;
  const pendingAlerts = status?.pending_alerts ?? 0;
  const isRunning = status?.is_worker_running ?? false;
  const queueLength = status?.queue_length ?? 0;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Total de Planilhas */}
      <div 
        onClick={() => onNavigate('jobs')}
        className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm hover:shadow-md transition-all duration-200 hover:-translate-y-0.5 cursor-pointer"
      >
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Total de Planilhas
          </span>
          <div className="w-9 h-9 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
            <FileSpreadsheet className="w-5 h-5" />
          </div>
        </div>
        <div className="mt-3 flex items-baseline space-x-2">
          <span className="text-2xl font-bold text-slate-900">{totalJobs}</span>
          <span className="text-xs text-slate-500">arquivos cadastrados</span>
        </div>
      </div>

      {/* Planilhas Ativas */}
      <div 
        onClick={() => onNavigate('jobs')}
        className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm hover:shadow-md transition-all duration-200 hover:-translate-y-0.5 cursor-pointer"
      >
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Automações Ativas
          </span>
          <div className="w-9 h-9 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
            <PlayCircle className="w-5 h-5" />
          </div>
        </div>
        <div className="mt-3 flex items-baseline space-x-2">
          <span className="text-2xl font-bold text-emerald-700">{activeJobs}</span>
          <span className="text-xs text-slate-500">
            de {totalJobs} no agendador
          </span>
        </div>
      </div>

      {/* Fila de Execução (Concorrência 1) */}
      <div 
        onClick={() => onNavigate('history')}
        className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm hover:shadow-md transition-all duration-200 hover:-translate-y-0.5 cursor-pointer"
      >
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 whitespace-nowrap">
            Status da Fila (Excel)
          </span>
          <div className="w-9 h-9 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
            <Layers className="w-5 h-5" />
          </div>
        </div>
        <div className="mt-3 flex items-center space-x-2">
          {isRunning ? (
            <div className="flex items-center space-x-1.5 text-blue-600 whitespace-nowrap">
              <span className="w-2.5 h-2.5 rounded-full bg-blue-600 animate-ping shrink-0" />
              <span className="text-sm font-semibold truncate max-w-[170px]">
                {status?.current_job?.job_name}
              </span>
            </div>
          ) : queueLength > 0 ? (
            <div className="flex items-center space-x-1.5 text-amber-600 whitespace-nowrap">
              <Clock className="w-4 h-4 animate-spin shrink-0" />
              <span className="text-sm font-semibold">{queueLength} em espera</span>
            </div>
          ) : (
            <div className="flex items-center space-x-1.5 text-emerald-600 whitespace-nowrap">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span className="text-sm font-semibold">Fila Livre</span>
            </div>
          )}
        </div>
      </div>

      {/* Alertas de Conflito */}
      <div 
        onClick={() => onNavigate('alerts')}
        className={`bg-white border rounded-xl p-5 shadow-sm hover:shadow-md transition-all duration-200 hover:-translate-y-0.5 cursor-pointer ${
          pendingAlerts > 0 ? 'border-amber-300 bg-amber-50/30' : 'border-slate-200'
        }`}
      >
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Alertas de Sobreposição
          </span>
          <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${
            pendingAlerts > 0 ? 'bg-amber-100 text-amber-700' : 'bg-slate-100 text-slate-500'
          }`}>
            <AlertTriangle className={`w-5 h-5 ${pendingAlerts > 0 ? 'animate-bounce' : ''}`} />
          </div>
        </div>
        <div className="mt-3 flex items-baseline space-x-2">
          <span className={`text-2xl font-bold ${pendingAlerts > 0 ? 'text-amber-700' : 'text-slate-800'}`}>
            {pendingAlerts}
          </span>
          <span className="text-xs text-slate-500">
            {pendingAlerts === 0 ? 'nenhum conflito' : 'requer atenção'}
          </span>
        </div>
      </div>
    </div>
  );
};
