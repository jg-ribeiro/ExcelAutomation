import React from 'react';
import { 
  FileSpreadsheet, 
  Clock, 
  RotateCw,
  Terminal,
  LogOut,
  User as UserIcon,
  LayoutDashboard,
  Layers,
  History,
  AlertTriangle
} from 'lucide-react';
import { SystemStatus, User } from '../../types';

interface AppHeaderProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  status: SystemStatus | null;
  onRefresh: () => void;
  isLoading: boolean;
  user: User | null;
  onLogout: () => void;
}

export const AppHeader: React.FC<AppHeaderProps> = ({
  activeTab,
  setActiveTab,
  status,
  onRefresh,
  isLoading,
  user,
  onLogout
}) => {
  const isRunning = status?.is_worker_running ?? false;
  const currentJobName = status?.current_job?.job_name;
  const queueLength = status?.queue_length ?? 0;
  const pendingAlerts = status?.pending_alerts ?? 0;

  return (
    <header className="sticky top-0 z-40 bg-slate-900 border-b border-slate-800 text-white shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 gap-3">
          
          {/* Logo & Marca (Fixado, sem quebras de linha indesejadas) */}
          <div className="flex items-center space-x-2.5 shrink-0">
            <div className="w-9 h-9 rounded-xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400 shadow-inner shrink-0">
              <FileSpreadsheet className="w-5 h-5" />
            </div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-base tracking-tight text-white whitespace-nowrap">
                Excel Automate
              </span>
              <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-300 border border-blue-500/30 whitespace-nowrap">
                VM Headless
              </span>
            </div>
          </div>

          {/* Navegação Principal com abas e ícones compactos */}
          <nav className="hidden md:flex items-center space-x-1 shrink-0">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all duration-150 flex items-center space-x-1.5 ${
                activeTab === 'dashboard'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800'
              }`}
            >
              <LayoutDashboard className="w-3.5 h-3.5 shrink-0" />
              <span>Visão Geral</span>
            </button>

            <button
              onClick={() => setActiveTab('jobs')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all duration-150 flex items-center space-x-1.5 ${
                activeTab === 'jobs'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800'
              }`}
            >
              <Layers className="w-3.5 h-3.5 shrink-0" />
              <span>Planilhas & Jobs</span>
            </button>

            <button
              onClick={() => setActiveTab('history')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all duration-150 flex items-center space-x-1.5 ${
                activeTab === 'history'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800'
              }`}
            >
              <History className="w-3.5 h-3.5 shrink-0" />
              <span>Histórico</span>
            </button>

            <button
              onClick={() => setActiveTab('logs')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all duration-150 flex items-center space-x-1.5 ${
                activeTab === 'logs'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800'
              }`}
            >
              <Terminal className="w-3.5 h-3.5 shrink-0" />
              <span>Logs ao Vivo</span>
            </button>

            <button
              onClick={() => setActiveTab('alerts')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all duration-150 flex items-center space-x-1.5 ${
                activeTab === 'alerts'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800'
              }`}
            >
              <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
              <span>Conflitos</span>
              {pendingAlerts > 0 && (
                <span className="px-1.5 py-0.2 rounded-full text-[10px] font-bold bg-amber-500 text-slate-950 animate-pulse">
                  {pendingAlerts}
                </span>
              )}
            </button>
          </nav>

          {/* Área da Direita: Status da Fila, Botão Atualizar e Perfil */}
          <div className="flex items-center space-x-2.5 shrink-0">
            {/* Indicador de Fila (Concorrência Estrita = 1) */}
            {isRunning ? (
              <div 
                title={`Executando agora: ${currentJobName}`}
                className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-blue-500/15 border border-blue-500/30 text-blue-300 text-xs font-medium whitespace-nowrap shrink-0"
              >
                <span className="w-2 h-2 rounded-full bg-blue-400 animate-ping shrink-0" />
                <span className="truncate max-w-[120px] lg:max-w-[160px]">
                  Executando: {currentJobName}
                </span>
              </div>
            ) : queueLength > 0 ? (
              <div 
                title={`${queueLength} automações aguardando na fila`}
                className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-amber-500/15 border border-amber-500/30 text-amber-300 text-xs font-medium whitespace-nowrap shrink-0"
              >
                <Clock className="w-3.5 h-3.5 animate-spin shrink-0" />
                <span>{queueLength} na fila</span>
              </div>
            ) : (
              <div 
                title="Apenas 1 job executa por vez no Excel. Fila livre no momento."
                className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-xs font-medium whitespace-nowrap shrink-0"
              >
                <span className="w-2 h-2 rounded-full bg-emerald-400 shrink-0" />
                <span>Fila Livre</span>
              </div>
            )}

            {/* Botão de Atualização Rápida */}
            <button
              onClick={onRefresh}
              disabled={isLoading}
              title="Atualizar dados do servidor"
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors disabled:opacity-50 shrink-0"
            >
              <RotateCw className={`w-4 h-4 ${isLoading ? 'animate-spin text-blue-400' : ''}`} />
            </button>

            {/* Usuário Logado e Logout */}
            {user && (
              <div className="flex items-center space-x-2 border-l border-slate-800 pl-2.5 shrink-0">
                <div className="flex items-center space-x-2 shrink-0">
                  <div className="w-7 h-7 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300 shrink-0">
                    <UserIcon className="w-3.5 h-3.5" />
                  </div>
                  <div className="hidden xl:block text-left whitespace-nowrap">
                    <p className="text-xs font-bold text-white leading-none truncate max-w-[120px]">
                      {user.display_name || user.username}
                    </p>
                    <span className={`text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded border inline-block mt-0.5 ${
                      user.role === 'ADMIN'
                        ? 'bg-blue-500/20 text-blue-300 border-blue-500/30'
                        : 'bg-slate-800 text-slate-400 border-slate-700'
                    }`}>
                      {user.role}
                    </span>
                  </div>
                </div>

                <button
                  onClick={onLogout}
                  title="Sair do sistema (Logout)"
                  className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition-colors shrink-0"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
