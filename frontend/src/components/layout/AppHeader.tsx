import React from 'react';
import { 
  FileSpreadsheet, 
  Clock, 
  RotateCw,
  Terminal
} from 'lucide-react';
import { SystemStatus } from '../../types';

interface AppHeaderProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  status: SystemStatus | null;
  onRefresh: () => void;
  isLoading: boolean;
}

export const AppHeader: React.FC<AppHeaderProps> = ({
  activeTab,
  setActiveTab,
  status,
  onRefresh,
  isLoading
}) => {
  const isRunning = status?.is_worker_running ?? false;
  const currentJobName = status?.current_job?.job_name;
  const queueLength = status?.queue_length ?? 0;
  const pendingAlerts = status?.pending_alerts ?? 0;

  return (
    <header className="sticky top-0 z-40 bg-slate-900 border-b border-slate-800 text-white shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Marca */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400 shadow-inner">
              <FileSpreadsheet className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg tracking-tight text-white">Excel Automate</span>
                <span className="text-[11px] font-semibold uppercase px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-400 border border-blue-500/30">
                  VM Headless
                </span>
              </div>
              <p className="text-xs text-slate-400">Automação e Agendador Resiliente</p>
            </div>
          </div>

          {/* Navegação Principal */}
          <nav className="hidden md:flex items-center space-x-1">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`px-3.5 py-2 rounded-lg text-sm font-medium transition-all duration-150 ${
                activeTab === 'dashboard'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800'
              }`}
            >
              Visão Geral
            </button>

            <button
              onClick={() => setActiveTab('jobs')}
              className={`px-3.5 py-2 rounded-lg text-sm font-medium transition-all duration-150 ${
                activeTab === 'jobs'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800'
              }`}
            >
              Planilhas & Jobs
            </button>

            <button
              onClick={() => setActiveTab('history')}
              className={`px-3.5 py-2 rounded-lg text-sm font-medium transition-all duration-150 ${
                activeTab === 'history'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800'
              }`}
            >
              Histórico
            </button>

            <button
              onClick={() => setActiveTab('logs')}
              className={`px-3.5 py-2 rounded-lg text-sm font-medium transition-all duration-150 flex items-center space-x-1.5 ${
                activeTab === 'logs'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800'
              }`}
            >
              <Terminal className="w-4 h-4" />
              <span>Logs ao Vivo</span>
            </button>

            <button
              onClick={() => setActiveTab('alerts')}
              className={`px-3.5 py-2 rounded-lg text-sm font-medium transition-all duration-150 flex items-center space-x-1.5 ${
                activeTab === 'alerts'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800'
              }`}
            >
              <span>Conflitos</span>
              {pendingAlerts > 0 && (
                <span className="px-1.5 py-0.2 rounded-full text-[10px] font-bold bg-amber-500 text-slate-950 animate-pulse">
                  {pendingAlerts}
                </span>
              )}
            </button>
          </nav>

          {/* Status do Worker e Botão de Atualizar */}
          <div className="flex items-center space-x-3">
            {/* Indicador de Fila / Concorrência 1 */}
            {isRunning ? (
              <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-blue-500/15 border border-blue-500/30 text-blue-300 text-xs font-medium">
                <span className="w-2 h-2 rounded-full bg-blue-400 animate-ping" />
                <span className="truncate max-w-[160px]">
                  Executando: {currentJobName}
                </span>
              </div>
            ) : queueLength > 0 ? (
              <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-amber-500/15 border border-amber-500/30 text-amber-300 text-xs font-medium">
                <Clock className="w-3.5 h-3.5 animate-spin" />
                <span>{queueLength} na fila</span>
              </div>
            ) : (
              <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-xs font-medium">
                <span className="w-2 h-2 rounded-full bg-emerald-400" />
                <span>Fila Livre (1 por vez)</span>
              </div>
            )}

            {/* Botão de Atualização Rápida */}
            <button
              onClick={onRefresh}
              disabled={isLoading}
              title="Atualizar dados"
              className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors disabled:opacity-50"
            >
              <RotateCw className={`w-4 h-4 ${isLoading ? 'animate-spin text-blue-400' : ''}`} />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
