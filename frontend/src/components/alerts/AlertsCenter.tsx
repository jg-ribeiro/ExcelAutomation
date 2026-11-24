import React from 'react';
import { 
  AlertTriangle, 
  ShieldAlert, 
  CheckCircle2, 
  Info, 
  ArrowRight,
  ShieldCheck
} from 'lucide-react';
import { Alert, Job } from '../../types';

interface AlertsCenterProps {
  alerts: Alert[];
  jobs: Job[];
  onDismiss: (alertId: number) => void;
  onResolve: (alertId: number) => void;
  onEditJob: (job: Job) => void;
}

export const AlertsCenter: React.FC<AlertsCenterProps> = ({
  alerts,
  jobs,
  onDismiss,
  onResolve,
  onEditJob
}) => {
  const pendingAlerts = alerts.filter(a => a.status === 'pending' || a.status === 'auto_paused');
  const resolvedAlerts = alerts.filter(a => a.status === 'resolved' || a.status === 'acknowledged');

  const getJobForAlert = (jobId: number) => {
    return jobs.find(j => j.id === jobId);
  };

  return (
    <div className="space-y-6">
      {/* Cabeçalho */}
      <div>
        <h2 className="text-xl font-bold tracking-tight text-slate-900">
          Central de Alertas & Conflitos de Agendamento
        </h2>
        <p className="text-xs text-slate-500">
          Monitoramento estatístico de sobreposições de horários com política de auto-pause inteligente
        </p>
      </div>

      {/* Cartão Educativo: Como Funciona a Política de Auto-Pause */}
      <div className="bg-blue-50/70 border border-blue-200 rounded-xl p-4.5 text-xs text-blue-900 shadow-sm">
        <div className="flex items-start space-x-3">
          <div className="p-2 rounded-lg bg-blue-100 text-blue-700 shrink-0 mt-0.5">
            <Info className="w-5 h-5" />
          </div>
          <div className="space-y-1.5 leading-relaxed">
            <h3 className="font-bold text-sm text-blue-950">
              Política de Proteção contra Sobreposição de Execuções
            </h3>
            <p>
              O Microsoft Excel opera sob concorrência estrita (apenas 1 execução por vez). 
              Se uma planilha demora em média <strong>20 minutos</strong> e está agendada a cada <strong>10 minutos</strong>,
              uma sobreposição perpétua sobrecarregaria a fila do servidor.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-2.5 pt-2">
              <div className="bg-white/80 p-2.5 rounded-lg border border-blue-100">
                <strong className="block text-blue-900 font-semibold mb-0.5">1. Cálculo Estatístico</strong>
                <span>Média móvel calculada continuamente a partir das durações reais gravadas no SQLite.</span>
              </div>
              <div className="bg-white/80 p-2.5 rounded-lg border border-blue-100">
                <strong className="block text-blue-900 font-semibold mb-0.5">2. Alerta Preventivo</strong>
                <span>Emitido imediatamente quando o tempo médio ultrapassa 85% do intervalo programado.</span>
              </div>
              <div className="bg-white/80 p-2.5 rounded-lg border border-blue-100">
                <strong className="block text-blue-900 font-semibold mb-0.5">3. Auto-Pause (Sem exclusão)</strong>
                <span>Após 3 ciclos consecutivos sem intervenção, o job é pausado com segurança para proteger o sistema.</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Alertas Pendentes e Auto-Pausados */}
      <div className="space-y-3">
        <h3 className="text-sm font-bold uppercase tracking-wider text-slate-700 flex items-center space-x-2">
          <span>Alertas Ativos</span>
          <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-amber-100 text-amber-800">
            {pendingAlerts.length}
          </span>
        </h3>

        {pendingAlerts.length === 0 ? (
          <div className="bg-white border border-slate-200 rounded-xl p-8 text-center shadow-sm">
            <div className="w-10 h-10 rounded-full bg-emerald-100 text-emerald-600 mx-auto flex items-center justify-center mb-2">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h4 className="text-sm font-bold text-slate-800">Nenhum conflito de agendamento ativo</h4>
            <p className="text-xs text-slate-500 mt-0.5">
              Todas as automações cadastradas estão operando com margem de segurança temporal saudável.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {pendingAlerts.map(alert => {
              const job = getJobForAlert(alert.job_id);
              const isAutoPaused = alert.status === 'auto_paused';

              return (
                <div
                  key={alert.id}
                  className={`bg-white border rounded-xl p-4.5 shadow-sm transition-all ${
                    isAutoPaused ? 'border-rose-300 bg-rose-50/20' : 'border-amber-300 bg-amber-50/20'
                  }`}
                >
                  <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                    <div className="flex items-start space-x-3 flex-1">
                      <div className={`p-2 rounded-lg shrink-0 mt-0.5 ${
                        isAutoPaused ? 'bg-rose-100 text-rose-700' : 'bg-amber-100 text-amber-700'
                      }`}>
                        {isAutoPaused ? <ShieldAlert className="w-5 h-5" /> : <AlertTriangle className="w-5 h-5" />}
                      </div>

                      <div className="space-y-1">
                        <div className="flex items-center space-x-2 flex-wrap">
                          <span className="font-bold text-sm text-slate-900">
                            {alert.title}
                          </span>
                          <span className={`px-2 py-0.5 rounded-full text-[11px] font-bold uppercase ${
                            isAutoPaused ? 'bg-rose-100 text-rose-800 border border-rose-200' : 'bg-amber-100 text-amber-800 border border-amber-200'
                          }`}>
                            {isAutoPaused ? 'Auto-Pausado' : `Ciclo ${alert.consecutive_count} de 3`}
                          </span>
                        </div>

                        <p className="text-xs text-slate-700 leading-relaxed">
                          {alert.message}
                        </p>

                        <div className="flex items-center space-x-4 text-[11px] text-slate-500 pt-1">
                          <span>Detectado em: {new Date(alert.created_at).toLocaleString('pt-BR')}</span>
                          {alert.action_deadline && !isAutoPaused && (
                            <span className="text-amber-700 font-medium">
                              Prazo para auto-pause: {new Date(alert.action_deadline).toLocaleString('pt-BR')}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Botões de Ação para o Alerta */}
                    <div className="flex items-center space-x-2 self-end sm:self-center shrink-0">
                      {job && (
                        <button
                          onClick={() => onEditJob(job)}
                          className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white shadow-sm flex items-center space-x-1"
                        >
                          <span>Ajustar Agendamento</span>
                          <ArrowRight className="w-3.5 h-3.5" />
                        </button>
                      )}

                      {!isAutoPaused && (
                        <button
                          onClick={() => onDismiss(alert.id)}
                          className="px-3 py-1.5 rounded-lg text-xs font-medium border border-slate-300 text-slate-700 hover:bg-slate-50"
                        >
                          Dispensar
                        </button>
                      )}

                      <button
                        onClick={() => onResolve(alert.id)}
                        className="px-3 py-1.5 rounded-lg text-xs font-medium border border-emerald-300 text-emerald-700 bg-emerald-50 hover:bg-emerald-100 flex items-center space-x-1"
                      >
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>Resolver</span>
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Histórico de Alertas Resolvidos */}
      {resolvedAlerts.length > 0 && (
        <div className="space-y-3 pt-4 border-t border-slate-200">
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-500">
            Histórico de Alertas Resolvidos ({resolvedAlerts.length})
          </h3>
          <div className="space-y-2 opacity-80">
            {resolvedAlerts.slice(0, 5).map(alert => (
              <div
                key={alert.id}
                className="bg-white border border-slate-200 rounded-lg p-3 text-xs flex items-center justify-between"
              >
                <div className="flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                  <span className="font-semibold text-slate-800">{alert.title}</span>
                  <span className="text-slate-500 truncate max-w-md">— {alert.message}</span>
                </div>
                <span className="text-slate-400 text-[11px] shrink-0">
                  Resolvido em {alert.resolved_at ? new Date(alert.resolved_at).toLocaleDateString('pt-BR') : '-'}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
