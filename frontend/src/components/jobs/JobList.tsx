import React, { useState } from 'react';
import { 
  Plus, 
  Play, 
  Pause, 
  Edit3, 
  Trash2, 
  FileSpreadsheet, 
  Clock, 
  Calendar, 
  AlertTriangle,
  Copy,
  CheckCircle2
} from 'lucide-react';
import { Job } from '../../types';
import { DurationGauge } from './DurationGauge';

interface JobListProps {
  jobs: Job[];
  onNewJob: () => void;
  onEditJob: (job: Job) => void;
  onDeleteJob: (job: Job) => void;
  onRunNow: (job: Job) => void;
  onToggleActive: (job: Job) => void;
}

export const JobList: React.FC<JobListProps> = ({
  jobs,
  onNewJob,
  onEditJob,
  onDeleteJob,
  onRunNow,
  onToggleActive
}) => {
  const [copiedId, setCopiedId] = useState<number | null>(null);

  const copyPath = (id: number, path: string) => {
    navigator.clipboard.writeText(path);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const formatScheduleLabel = (type: string, value: string) => {
    if (type === 'daily') return `Diário às ${value}`;
    if (type === 'interval') return `A cada ${value}`;
    return 'Manual';
  };

  return (
    <div className="space-y-4">
      {/* Barra de Ações Superior */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-900">
            Planilhas & Agendamentos
          </h2>
          <p className="text-xs text-slate-500">
            Gerenciamento individual de workbooks, macros e frequência de atualização
          </p>
        </div>

        <button
          onClick={onNewJob}
          className="flex items-center space-x-1.5 px-4 py-2 rounded-lg text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 shadow-sm transition-all duration-150 active:scale-98"
        >
          <Plus className="w-4 h-4" />
          <span>Nova Planilha</span>
        </button>
      </div>

      {/* Lista de Jobs */}
      {jobs.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-xl p-12 text-center shadow-sm">
          <div className="w-12 h-12 rounded-full bg-slate-100 text-slate-400 mx-auto flex items-center justify-center mb-3">
            <FileSpreadsheet className="w-6 h-6" />
          </div>
          <h3 className="text-sm font-bold text-slate-800">Nenhuma planilha cadastrada</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            Cadastre seu primeiro arquivo Excel para iniciar os agendamentos automáticos headless.
          </p>
          <button
            onClick={onNewJob}
            className="mt-4 px-4 py-2 rounded-lg text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700"
          >
            Cadastrar Primeira Planilha
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {jobs.map(job => {
            const isPaused = !job.is_active;
            const hasConflict = job.has_conflict;
            const isAutoPaused = isPaused && job.pause_reason && job.pause_reason.includes('Pausado automaticamente');

            return (
              <div
                key={job.id}
                className={`bg-white border rounded-xl p-5 shadow-sm hover:shadow-md transition-all duration-200 ${
                  hasConflict ? 'border-amber-300' : 'border-slate-200'
                }`}
              >
                <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
                  {/* Bloco de Informações Principais */}
                  <div className="space-y-2 flex-1 min-w-0">
                    <div className="flex items-center space-x-2.5 flex-wrap gap-y-1.5">
                      <span className="font-bold text-base text-slate-900 truncate">
                        {job.name}
                      </span>

                      {/* Badge de Status */}
                      {isAutoPaused ? (
                        <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-50 text-rose-700 border border-rose-200 whitespace-nowrap">
                          Auto-Pausado (Sobreposição)
                        </span>
                      ) : isPaused ? (
                        <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200 whitespace-nowrap">
                          Pausado
                        </span>
                      ) : (
                        <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center space-x-1 whitespace-nowrap">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                          <span>Ativo</span>
                        </span>
                      )}

                      {/* Badge de Agendamento */}
                      <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200 flex items-center space-x-1 whitespace-nowrap">
                        <Clock className="w-3 h-3" />
                        <span>{formatScheduleLabel(job.schedule_type, job.schedule_value)}</span>
                      </span>

                      {/* Badge de Macro */}
                      {job.macro_name && (
                        <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-slate-100 text-slate-600 whitespace-nowrap">
                          Macro: {job.macro_name}
                        </span>
                      )}
                    </div>

                    {/* Caminho do Arquivo UNC */}
                    <div className="flex items-center space-x-2 text-xs text-slate-500 font-mono bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200/60 max-w-2xl">
                      <FileSpreadsheet className="w-3.5 h-3.5 shrink-0 text-slate-400" />
                      <span className="truncate">{job.file_path}</span>
                      <button
                        onClick={() => copyPath(job.id, job.file_path)}
                        title="Copiar caminho"
                        className="shrink-0 text-slate-400 hover:text-slate-700 p-1"
                      >
                        {copiedId === job.id ? (
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                        ) : (
                          <Copy className="w-3.5 h-3.5" />
                        )}
                      </button>
                    </div>

                    {/* Alerta de Conflito Inline */}
                    {job.conflict_message && (
                      <div className="p-2.5 rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-xs flex items-center space-x-2">
                        <AlertTriangle className="w-4 h-4 shrink-0 text-amber-600" />
                        <span>{job.conflict_message}</span>
                      </div>
                    )}

                    {/* Motivo de Auto-Pausa */}
                    {job.pause_reason && (
                      <p className="text-xs text-slate-500 italic">
                        Motivo: {job.pause_reason}
                      </p>
                    )}
                  </div>

                  {/* Bloco de Métricas & Barra de Segurança */}
                  <div className="w-full lg:w-72 shrink-0 bg-slate-50/70 p-3 rounded-lg border border-slate-100">
                    <DurationGauge
                      avgDurationSeconds={job.avg_duration_seconds}
                      durationRatio={job.duration_ratio}
                      scheduleType={job.schedule_type}
                      scheduleValue={job.schedule_value}
                    />

                    {job.next_run_at && job.is_active && (
                      <div className="mt-2 text-[11px] text-slate-500 flex items-center space-x-1">
                        <Calendar className="w-3 h-3 text-slate-400" />
                        <span>Próxima: {new Date(job.next_run_at).toLocaleString('pt-BR')}</span>
                      </div>
                    )}
                  </div>

                  {/* Bloco de Botões de Ação */}
                  <div className="flex items-center space-x-1.5 shrink-0 self-end lg:self-center">
                    <button
                      onClick={() => onRunNow(job)}
                      title="Executar agora"
                      className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white shadow-sm flex items-center space-x-1 transition-all duration-150 active:scale-95"
                    >
                      <Play className="w-3 h-3 fill-current" />
                      <span>Rodar</span>
                    </button>

                    <button
                      onClick={() => onToggleActive(job)}
                      title={job.is_active ? 'Pausar agendamento' : 'Retomar agendamento'}
                      className={`p-2 rounded-lg text-xs font-medium border transition-colors ${
                        job.is_active
                          ? 'border-slate-300 text-slate-700 hover:bg-slate-100'
                          : 'border-emerald-300 text-emerald-700 bg-emerald-50 hover:bg-emerald-100'
                      }`}
                    >
                      {job.is_active ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
                    </button>

                    <button
                      onClick={() => onEditJob(job)}
                      title="Editar configurações"
                      className="p-2 rounded-lg text-xs font-medium border border-slate-300 text-slate-700 hover:bg-slate-100 transition-colors"
                    >
                      <Edit3 className="w-3.5 h-3.5" />
                    </button>

                    <button
                      onClick={() => onDeleteJob(job)}
                      title="Excluir job"
                      className="p-2 rounded-lg text-xs font-medium border border-slate-200 text-slate-400 hover:text-rose-600 hover:border-rose-300 hover:bg-rose-50 transition-colors"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
