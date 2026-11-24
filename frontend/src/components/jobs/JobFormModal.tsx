import React, { useState, useEffect } from 'react';
import { X, FileSpreadsheet, Clock, Play, AlertCircle, Save } from 'lucide-react';
import { Job, JobFormData } from '../../types';

interface JobFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: JobFormData) => Promise<void>;
  editingJob?: Job | null;
}

export const JobFormModal: React.FC<JobFormModalProps> = ({
  isOpen,
  onClose,
  onSave,
  editingJob
}) => {
  const [formData, setFormData] = useState<JobFormData>({
    name: '',
    file_path: '',
    macro_name: 'SalvarTodos',
    schedule_type: 'daily',
    schedule_value: '03:00',
    is_active: true,
    query_timeout: 300,
    lock_timeout: 120
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (editingJob) {
      setFormData({
        name: editingJob.name,
        file_path: editingJob.file_path,
        macro_name: editingJob.macro_name || '',
        schedule_type: editingJob.schedule_type,
        schedule_value: editingJob.schedule_value,
        is_active: editingJob.is_active,
        query_timeout: editingJob.query_timeout,
        lock_timeout: editingJob.lock_timeout
      });
    } else {
      setFormData({
        name: '',
        file_path: '',
        macro_name: 'SalvarTodos',
        schedule_type: 'daily',
        schedule_value: '03:00',
        is_active: true,
        query_timeout: 300,
        lock_timeout: 120
      });
    }
    setError(null);
  }, [editingJob, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      setError('Por favor, informe o nome da automação.');
      return;
    }
    if (!formData.file_path.trim()) {
      setError('Por favor, informe o caminho do arquivo Excel (.xlsm ou .xlsx).');
      return;
    }
    if (!formData.schedule_value.trim()) {
      setError('Por favor, informe o horário ou intervalo de agendamento.');
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      await onSave(formData);
      onClose();
    } catch (err: any) {
      setError(err.message || 'Erro ao salvar automação.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleIntervalPreset = (preset: string) => {
    setFormData(prev => ({ ...prev, schedule_type: 'interval', schedule_value: preset }));
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/60 backdrop-blur-sm animate-fade-in">
      <div 
        className="bg-white rounded-2xl max-w-xl w-full border border-slate-200 shadow-2xl overflow-hidden flex flex-col max-h-[90vh]"
        onClick={e => e.stopPropagation()}
      >
        {/* Cabeçalho */}
        <div className="px-6 py-4 bg-slate-900 text-white flex items-center justify-between border-b border-slate-800">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-600/30 text-blue-400 flex items-center justify-center">
              <FileSpreadsheet className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white">
                {editingJob ? 'Editar Automação' : 'Nova Automação de Planilha'}
              </h2>
              <p className="text-xs text-slate-400">Configuração de execução headless do Excel</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Formulário com rolagem */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4 overflow-y-auto">
          {error && (
            <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Nome */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1">
              Nome Identificador *
            </label>
            <input
              type="text"
              required
              placeholder="ex: Placar da Moagem 2026"
              value={formData.name}
              onChange={e => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3.5 py-2 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600"
            />
          </div>

          {/* Caminho do Arquivo */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1">
              Caminho do Workbook (Rede UNC ou Local) *
            </label>
            <input
              type="text"
              required
              placeholder="\\\\servidor\\pasta\\arquivo.xlsm"
              value={formData.file_path}
              onChange={e => setFormData({ ...formData, file_path: e.target.value })}
              className="w-full px-3.5 py-2 rounded-lg border border-slate-300 text-sm font-mono text-xs focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600"
            />
            <p className="text-[11px] text-slate-500 mt-1">
              Dica: O serviço Windows executará sob a conta dedicada com acesso de leitura/escrita a este compartilhamento.
            </p>
          </div>

          {/* Macro */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1">
              Nome da Macro VBA (Opcional)
            </label>
            <input
              type="text"
              placeholder="ex: SalvarTodos"
              value={formData.macro_name}
              onChange={e => setFormData({ ...formData, macro_name: e.target.value })}
              className="w-full px-3.5 py-2 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600"
            />
            <p className="text-[11px] text-slate-500 mt-1">
              Executada imediatamente após a atualização síncrona de todas as conexões e recálculo total.
            </p>
          </div>

          {/* Tipo de Agendamento */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5">
              Tipo de Agendamento *
            </label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setFormData({ ...formData, schedule_type: 'daily', schedule_value: '03:00' })}
                className={`px-3 py-2 rounded-lg text-xs font-semibold border flex items-center justify-center space-x-1.5 transition-all ${
                  formData.schedule_type === 'daily'
                    ? 'bg-blue-50 border-blue-500 text-blue-700'
                    : 'bg-white border-slate-300 text-slate-600 hover:bg-slate-50'
                }`}
              >
                <Clock className="w-3.5 h-3.5" />
                <span>Diário (Horário Fixo)</span>
              </button>

              <button
                type="button"
                onClick={() => setFormData({ ...formData, schedule_type: 'interval', schedule_value: '30m' })}
                className={`px-3 py-2 rounded-lg text-xs font-semibold border flex items-center justify-center space-x-1.5 transition-all ${
                  formData.schedule_type === 'interval'
                    ? 'bg-blue-50 border-blue-500 text-blue-700'
                    : 'bg-white border-slate-300 text-slate-600 hover:bg-slate-50'
                }`}
              >
                <Play className="w-3.5 h-3.5" />
                <span>Intervalo Recorrente</span>
              </button>
            </div>
          </div>

          {/* Valor do Agendamento */}
          {formData.schedule_type === 'daily' ? (
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1">
                Horário da Execução Diária (HH:MM) *
              </label>
              <input
                type="time"
                required
                value={formData.schedule_value}
                onChange={e => setFormData({ ...formData, schedule_value: e.target.value })}
                className="w-full px-3.5 py-2 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600"
              />
            </div>
          ) : (
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1">
                Intervalo Entre Execuções *
              </label>
              <input
                type="text"
                required
                placeholder="ex: 10m, 30m, 1h, 2h"
                value={formData.schedule_value}
                onChange={e => setFormData({ ...formData, schedule_value: e.target.value })}
                className="w-full px-3.5 py-2 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600"
              />
              <div className="flex items-center space-x-1.5 mt-2">
                <span className="text-[11px] text-slate-500">Atalhos:</span>
                {['10m', '20m', '30m', '1h', '2h'].map(preset => (
                  <button
                    key={preset}
                    type="button"
                    onClick={() => handleIntervalPreset(preset)}
                    className="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors"
                  >
                    {preset}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Timeouts de Segurança */}
          <div className="grid grid-cols-2 gap-3 pt-2 border-t border-slate-100">
            <div>
              <label className="block text-[11px] font-semibold text-slate-600 mb-1">
                Timeout Consulta (segundos)
              </label>
              <input
                type="number"
                min="30"
                max="3600"
                value={formData.query_timeout}
                onChange={e => setFormData({ ...formData, query_timeout: parseInt(e.target.value) || 300 })}
                className="w-full px-3 py-1.5 rounded-lg border border-slate-300 text-xs focus:ring-1 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-600 mb-1">
                Timeout Lock Arquivo (segundos)
              </label>
              <input
                type="number"
                min="10"
                max="1800"
                value={formData.lock_timeout}
                onChange={e => setFormData({ ...formData, lock_timeout: parseInt(e.target.value) || 120 })}
                className="w-full px-3 py-1.5 rounded-lg border border-slate-300 text-xs focus:ring-1 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Rodapé de Ações */}
          <div className="pt-4 flex items-center justify-end space-x-2 border-t border-slate-200">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-4 py-2 rounded-lg text-sm font-semibold text-slate-700 hover:bg-slate-100 border border-slate-300 transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-5 py-2 rounded-lg text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 shadow-sm transition-all duration-150 flex items-center space-x-1.5 disabled:opacity-50"
            >
              <Save className="w-4 h-4" />
              <span>{isSubmitting ? 'Salvando...' : 'Salvar Automação'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
