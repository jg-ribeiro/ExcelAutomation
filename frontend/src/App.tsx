import React, { useState, useEffect, useCallback } from 'react';
import { api, authStorage } from './services/api';
import { Job, Execution, Alert, SystemStatus, JobFormData, User } from './types';
import { AppHeader } from './components/layout/AppHeader';
import { KpiCards } from './components/dashboard/KpiCards';
import { ConflictBanner } from './components/dashboard/ConflictBanner';
import { JobList } from './components/jobs/JobList';
import { JobFormModal } from './components/jobs/JobFormModal';
import { ExecutionHistory } from './components/history/ExecutionHistory';
import { LogTerminal } from './components/logs/LogTerminal';
import { AlertsCenter } from './components/alerts/AlertsCenter';
import { LoginPage } from './components/auth/LoginPage';
import { UserManagement } from './components/users/UserManagement';
import { Terminal } from 'lucide-react';

export const App: React.FC = () => {
  const [currentUser, setCurrentUser] = useState<User | null>(() => authStorage.getUser());
  const [isAuthChecking, setIsAuthChecking] = useState<boolean>(true);

  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Modal de formulário de Job
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingJob, setEditingJob] = useState<Job | null>(null);

  // Toast / feedback notification
  const [notification, setNotification] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  const showToast = (message: string, type: 'success' | 'error' = 'success') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 3500);
  };

  // Checagem de token e sessão ativa
  useEffect(() => {
    const token = authStorage.getToken();
    if (token) {
      api.getMe()
        .then(user => {
          setCurrentUser(user);
        })
        .catch(() => {
          authStorage.clear();
          setCurrentUser(null);
        })
        .finally(() => {
          setIsAuthChecking(false);
        });
    } else {
      setIsAuthChecking(false);
    }

    const handleUnauthorized = () => {
      setCurrentUser(null);
      showToast('Sessão expirada. Por favor, entre novamente.', 'error');
    };

    window.addEventListener('auth:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('auth:unauthorized', handleUnauthorized);
  }, []);

  const handleLogout = () => {
    authStorage.clear();
    setCurrentUser(null);
    showToast('Você saiu do sistema com segurança.');
  };

  const loadAllData = useCallback(async () => {
    try {
      setIsLoading(true);
      const [sysStatus, jobsData, execData, alertsData] = await Promise.all([
        api.getSystemStatus().catch(() => null),
        api.getJobs().catch(() => []),
        api.getExecutions({ limit: 50 }).catch(() => []),
        api.getAlerts().catch(() => []),
      ]);

      if (sysStatus) setStatus(sysStatus);
      setJobs(jobsData);
      setExecutions(execData);
      setAlerts(alertsData);
    } catch (err: any) {
      console.error('Erro ao carregar dados:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Carga inicial
  useEffect(() => {
    loadAllData();
  }, [loadAllData]);

  // Polling automático a cada 5 segundos para manter o status sempre vivo
  useEffect(() => {
    const timer = setInterval(() => {
      loadAllData();
    }, 5000);
    return () => clearInterval(timer);
  }, [loadAllData]);

  // Ações de Jobs
  const handleOpenNewModal = () => {
    setEditingJob(null);
    setIsModalOpen(true);
  };

  const handleOpenEditModal = (job: Job) => {
    setEditingJob(job);
    setIsModalOpen(true);
  };

  const handleSaveJob = async (formData: JobFormData) => {
    if (editingJob) {
      await api.updateJob(editingJob.id, formData);
      showToast(`Automação '${formData.name}' atualizada com sucesso!`);
    } else {
      await api.createJob(formData);
      showToast(`Automação '${formData.name}' cadastrada com sucesso!`);
    }
    await loadAllData();
  };

  const handleDeleteJob = async (job: Job) => {
    if (window.confirm(`Tem certeza que deseja excluir a automação '${job.name}'? Todos os registros serão removidos.`)) {
      try {
        await api.deleteJob(job.id);
        showToast(`Job '${job.name}' excluído com sucesso.`);
        await loadAllData();
      } catch (err: any) {
        showToast(err.message, 'error');
      }
    }
  };

  const handleRunNow = async (job: Job) => {
    try {
      const res = await api.runJobNow(job.id);
      showToast(res.message);
      await loadAllData();
    } catch (err: any) {
      showToast(err.message, 'error');
    }
  };

  const handleToggleActive = async (job: Job) => {
    try {
      const res = await api.toggleJobActive(job.id);
      showToast(res.message);
      await loadAllData();
    } catch (err: any) {
      showToast(err.message, 'error');
    }
  };

  // Ações de Alertas
  const handleDismissAlert = async (alertId: number) => {
    try {
      await api.dismissAlert(alertId);
      showToast('Alerta dispensado com sucesso.');
      await loadAllData();
    } catch (err: any) {
      showToast(err.message, 'error');
    }
  };

  const handleResolveAlert = async (alertId: number) => {
    try {
      await api.resolveAlert(alertId);
      showToast('Alerta resolvido com sucesso.');
      await loadAllData();
    } catch (err: any) {
      showToast(err.message, 'error');
    }
  };

  if (isAuthChecking) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-400 font-sans">
        <div className="flex items-center space-x-2 text-sm">
          <span className="w-2.5 h-2.5 rounded-full bg-blue-500 animate-ping" />
          <span>Verificando credenciais corporativas...</span>
        </div>
      </div>
    );
  }

  if (!currentUser) {
    return <LoginPage onLoginSuccess={setCurrentUser} />;
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      {/* Toast Notification */}
      {notification && (
        <div className="fixed bottom-6 right-6 z-50 animate-bounce">
          <div className={`px-4 py-2.5 rounded-xl shadow-xl text-xs font-semibold text-white ${
            notification.type === 'success' ? 'bg-emerald-600' : 'bg-rose-600'
          }`}>
            {notification.message}
          </div>
        </div>
      )}

      {/* Header Fixo Escuro */}
      <AppHeader
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        status={status}
        onRefresh={loadAllData}
        isLoading={isLoading}
        user={currentUser}
        onLogout={handleLogout}
      />

      {/* Conteúdo Principal com Container de 80rem */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Banner de Aviso de Conflito no topo */}
        <ConflictBanner
          alerts={alerts}
          onNavigateToAlerts={() => setActiveTab('alerts')}
        />

        {/* Visão Geral (Dashboard) */}
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            <KpiCards status={status} onNavigate={setActiveTab} />

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Coluna 1 & 2: Planilhas em Destaque */}
              <div className="lg:col-span-2 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-bold text-slate-900">
                    Planilhas Configuradas
                  </h3>
                  <button
                    onClick={() => setActiveTab('jobs')}
                    className="text-xs font-semibold text-blue-600 hover:text-blue-700"
                  >
                    Ver todas ({jobs.length})
                  </button>
                </div>

                <JobList
                  jobs={jobs.slice(0, 3)}
                  onNewJob={handleOpenNewModal}
                  onEditJob={handleOpenEditModal}
                  onDeleteJob={handleDeleteJob}
                  onRunNow={handleRunNow}
                  onToggleActive={handleToggleActive}
                />
              </div>

              {/* Coluna 3: Prévia de Execuções e Acesso aos Logs */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-bold text-slate-900">
                    Atividades Recentes
                  </h3>
                  <button
                    onClick={() => setActiveTab('history')}
                    className="text-xs font-semibold text-blue-600 hover:text-blue-700"
                  >
                    Histórico completo
                  </button>
                </div>

                <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm divide-y divide-slate-100">
                  {executions.length === 0 ? (
                    <p className="text-xs text-slate-400 text-center py-6">
                      Nenhuma atividade recente registrada.
                    </p>
                  ) : (
                    executions.slice(0, 5).map((e) => (
                      <div key={e.id} className="py-2.5 first:pt-0 last:pb-0 flex items-center justify-between text-xs">
                        <div>
                          <p className="font-semibold text-slate-900">{e.job_name || `Job #${e.job_id}`}</p>
                          <span className="text-[11px] text-slate-400">
                            {e.started_at ? new Date(e.started_at).toLocaleTimeString('pt-BR') : '-'}
                          </span>
                        </div>
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                          e.status === 'success' ? 'bg-emerald-50 text-emerald-700' :
                          e.status === 'running' ? 'bg-blue-50 text-blue-700 animate-pulse' :
                          'bg-rose-50 text-rose-700'
                        }`}>
                          {e.status}
                        </span>
                      </div>
                    ))
                  )}
                </div>

                {/* Card de Acesso Rápido ao Terminal */}
                <div 
                  onClick={() => setActiveTab('logs')}
                  className="bg-slate-950 text-white rounded-xl p-4 shadow-sm border border-slate-800 hover:border-slate-700 transition-colors cursor-pointer group"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Terminal className="w-4 h-4 text-blue-400 group-hover:scale-110 transition-transform" />
                      <span className="text-xs font-mono font-bold">Terminal ao Vivo</span>
                    </div>
                    <span className="text-[10px] text-slate-400 font-mono">Abrir Console →</span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-2 font-mono">
                    Acompanhe a emissão de logs em tempo real via streaming SSE.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Aba de Planilhas & Jobs */}
        {activeTab === 'jobs' && (
          <JobList
            jobs={jobs}
            onNewJob={handleOpenNewModal}
            onEditJob={handleOpenEditModal}
            onDeleteJob={handleDeleteJob}
            onRunNow={handleRunNow}
            onToggleActive={handleToggleActive}
          />
        )}

        {/* Aba de Histórico de Execuções */}
        {activeTab === 'history' && (
          <ExecutionHistory
            executions={executions}
            onRefresh={loadAllData}
          />
        )}

        {/* Aba do Terminal de Logs ao Vivo */}
        {activeTab === 'logs' && (
          <div className="space-y-4">
            <div>
              <h2 className="text-xl font-bold tracking-tight text-slate-900">
                Visualizador de Logs em Tempo Real
              </h2>
              <p className="text-xs text-slate-500">
                Transmissão contínua de eventos do Excel headless, agendador e watchdog de modais
              </p>
            </div>
            <LogTerminal />
          </div>
        )}

        {/* Aba de Alertas & Conflitos */}
        {activeTab === 'alerts' && (
          <AlertsCenter
            alerts={alerts}
            jobs={jobs}
            onDismiss={handleDismissAlert}
            onResolve={handleResolveAlert}
            onEditJob={handleOpenEditModal}
          />
        )}

        {/* Aba de Gestão de Usuários (Apenas Administrador) */}
        {activeTab === 'users' && currentUser?.role === 'ADMIN' && (
          <UserManagement currentUser={currentUser} />
        )}
      </main>

      {/* Modal de Criação / Edição de Job */}
      <JobFormModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSave={handleSaveJob}
        editingJob={editingJob}
      />
    </div>
  );
};
export default App;
