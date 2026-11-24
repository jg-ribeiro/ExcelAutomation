import React, { useState } from 'react';
import { 
  CheckCircle2, 
  XCircle, 
  Clock, 
  RotateCw, 
  FileText,
  AlertOctagon,
  X
} from 'lucide-react';
import { Execution } from '../../types';

interface ExecutionHistoryProps {
  executions: Execution[];
  onRefresh: () => void;
}

export const ExecutionHistory: React.FC<ExecutionHistoryProps> = ({ executions, onRefresh }) => {
  const [selectedLog, setSelectedLog] = useState<{ title: string; log: string } | null>(null);

  const formatDuration = (seconds?: number | null) => {
    if (seconds == null) return '-';
    const m = Math.floor(seconds / 60);
    const s = Math.round(seconds % 60);
    if (m === 0) return `${s}s`;
    return `${m}m ${s}s`;
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'success':
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center space-x-1">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
            <span>Sucesso</span>
          </span>
        );
      case 'running':
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200 flex items-center space-x-1 animate-pulse">
            <RotateCw className="w-3.5 h-3.5 text-blue-500 animate-spin" />
            <span>Em Execução</span>
          </span>
        );
      case 'queued':
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200 flex items-center space-x-1">
            <Clock className="w-3.5 h-3.5 text-amber-500" />
            <span>Na Fila</span>
          </span>
        );
      case 'lock_timeout':
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200 flex items-center space-x-1">
            <AlertOctagon className="w-3.5 h-3.5 text-amber-600" />
            <span>Arquivo Bloqueado</span>
          </span>
        );
      case 'failed':
      default:
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200 flex items-center space-x-1">
            <XCircle className="w-3.5 h-3.5 text-rose-500" />
            <span>Falha</span>
          </span>
        );
    }
  };

  return (
    <div className="space-y-4">
      {/* Cabeçalho */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-900">
            Histórico de Execuções
          </h2>
          <p className="text-xs text-slate-500">
            Registro detalhado de duração, PIDs e diagnósticos de cada automação
          </p>
        </div>

        <button
          onClick={onRefresh}
          className="px-3 py-1.5 rounded-lg text-xs font-semibold border border-slate-300 text-slate-700 hover:bg-slate-50 flex items-center space-x-1"
        >
          <RotateCw className="w-3.5 h-3.5" />
          <span>Atualizar Histórico</span>
        </button>
      </div>

      {/* Tabela de Execuções */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        {executions.length === 0 ? (
          <div className="p-12 text-center text-slate-500 text-xs">
            Nenhuma execução registrada até o momento.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="px-5 py-3">ID</th>
                  <th className="px-5 py-3">Planilha / Job</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3">Início</th>
                  <th className="px-5 py-3">Duração</th>
                  <th className="px-5 py-3">PID Excel</th>
                  <th className="px-5 py-3">Disparo</th>
                  <th className="px-5 py-3 text-right">Ação</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium">
                {executions.map((exec) => (
                  <tr key={exec.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-5 py-3 text-slate-400 font-mono">#{exec.id}</td>
                    <td className="px-5 py-3 text-slate-900 font-semibold">
                      {exec.job_name || `Job #${exec.job_id}`}
                    </td>
                    <td className="px-5 py-3">{getStatusBadge(exec.status)}</td>
                    <td className="px-5 py-3 text-slate-600">
                      {exec.started_at
                        ? new Date(exec.started_at).toLocaleString('pt-BR')
                        : '-'}
                    </td>
                    <td className="px-5 py-3 text-slate-900 font-mono">
                      {formatDuration(exec.duration_seconds)}
                    </td>
                    <td className="px-5 py-3 text-slate-500 font-mono">
                      {exec.excel_pid ? `PID ${exec.excel_pid}` : '-'}
                    </td>
                    <td className="px-5 py-3">
                      <span className="capitalize px-2 py-0.5 rounded text-[10px] bg-slate-100 text-slate-600">
                        {exec.trigger_type === 'schedule' ? 'Agendado' : 'Manual'}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-right">
                      {exec.log_snippet ? (
                        <button
                          onClick={() => setSelectedLog({
                            title: `Log da Execução #${exec.id} — ${exec.job_name || `Job #${exec.job_id}`}`,
                            log: exec.log_snippet!
                          })}
                          className="px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold transition-colors flex items-center space-x-1 ml-auto"
                        >
                          <FileText className="w-3.5 h-3.5" />
                          <span>Ver Log</span>
                        </button>
                      ) : (
                        <span className="text-slate-400 text-[11px]">-</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal de Detalhes do Log */}
      {selectedLog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/60 backdrop-blur-sm animate-fade-in">
          <div className="bg-slate-950 text-slate-100 rounded-2xl max-w-3xl w-full border border-slate-800 shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
            <div className="px-5 py-3.5 bg-slate-900 border-b border-slate-800 flex items-center justify-between">
              <span className="font-mono text-xs font-bold text-white">
                {selectedLog.title}
              </span>
              <button
                onClick={() => setSelectedLog(null)}
                className="p-1 rounded text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-4 overflow-y-auto font-mono text-xs leading-relaxed terminal-scroll select-text text-slate-300 whitespace-pre-wrap">
              {selectedLog.log}
            </div>
            <div className="px-5 py-3 bg-slate-900 border-t border-slate-800 flex justify-end">
              <button
                onClick={() => setSelectedLog(null)}
                className="px-4 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-white"
              >
                Fechar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
