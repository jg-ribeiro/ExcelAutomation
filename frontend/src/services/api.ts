import { Job, JobFormData, Execution, Alert, SystemStatus, LogEntry } from '../types';

const API_BASE = '/api';

export const api = {
  // System Status
  async getSystemStatus(): Promise<SystemStatus> {
    const res = await fetch(`${API_BASE}/system/status`);
    if (!res.ok) throw new Error('Falha ao obter status do sistema');
    return res.json();
  },

  // Jobs
  async getJobs(): Promise<Job[]> {
    const res = await fetch(`${API_BASE}/jobs`);
    if (!res.ok) throw new Error('Falha ao listar jobs');
    return res.json();
  },

  async getJob(id: number): Promise<Job> {
    const res = await fetch(`${API_BASE}/jobs/${id}`);
    if (!res.ok) throw new Error(`Falha ao obter job #${id}`);
    return res.json();
  },

  async createJob(data: JobFormData): Promise<Job> {
    const res = await fetch(`${API_BASE}/jobs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Falha ao criar job');
    }
    return res.json();
  },

  async updateJob(id: number, data: Partial<JobFormData>): Promise<Job> {
    const res = await fetch(`${API_BASE}/jobs/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Falha ao atualizar job #${id}`);
    }
    return res.json();
  },

  async deleteJob(id: number): Promise<void> {
    const res = await fetch(`${API_BASE}/jobs/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error(`Falha ao excluir job #${id}`);
  },

  async runJobNow(id: number): Promise<{ success: boolean; message: string; execution_id: number }> {
    const res = await fetch(`${API_BASE}/jobs/${id}/run`, { method: 'POST' });
    if (!res.ok) throw new Error(`Falha ao disparar execução para job #${id}`);
    return res.json();
  },

  async toggleJobActive(id: number): Promise<{ success: boolean; is_active: boolean; message: string }> {
    const res = await fetch(`${API_BASE}/jobs/${id}/toggle-active`, { method: 'POST' });
    if (!res.ok) throw new Error(`Falha ao alterar estado do job #${id}`);
    return res.json();
  },

  // Executions
  async getExecutions(params?: { job_id?: number; status?: string; limit?: number; offset?: number }): Promise<Execution[]> {
    const query = new URLSearchParams();
    if (params?.job_id) query.append('job_id', params.job_id.toString());
    if (params?.status) query.append('status', params.status);
    if (params?.limit) query.append('limit', params.limit.toString());
    if (params?.offset) query.append('offset', params.offset.toString());

    const res = await fetch(`${API_BASE}/executions?${query.toString()}`);
    if (!res.ok) throw new Error('Falha ao listar execuções');
    return res.json();
  },

  async getExecution(id: number): Promise<Execution> {
    const res = await fetch(`${API_BASE}/executions/${id}`);
    if (!res.ok) throw new Error(`Falha ao obter execução #${id}`);
    return res.json();
  },

  // Alerts
  async getAlerts(status?: string): Promise<Alert[]> {
    const query = status ? `?status=${encodeURIComponent(status)}` : '';
    const res = await fetch(`${API_BASE}/alerts${query}`);
    if (!res.ok) throw new Error('Falha ao obter alertas');
    return res.json();
  },

  async dismissAlert(id: number): Promise<void> {
    const res = await fetch(`${API_BASE}/alerts/${id}/dismiss`, { method: 'POST' });
    if (!res.ok) throw new Error(`Falha ao dispensar alerta #${id}`);
  },

  async resolveAlert(id: number): Promise<void> {
    const res = await fetch(`${API_BASE}/alerts/${id}/resolve`, { method: 'POST' });
    if (!res.ok) throw new Error(`Falha ao resolver alerta #${id}`);
  },

  // Logs
  async getLogs(params?: { limit?: number; level?: string; search?: string }): Promise<{ total: number; logs: LogEntry[] }> {
    const query = new URLSearchParams();
    if (params?.limit) query.append('limit', params.limit.toString());
    if (params?.level) query.append('level', params.level);
    if (params?.search) query.append('search', params.search);

    const res = await fetch(`${API_BASE}/logs?${query.toString()}`);
    if (!res.ok) throw new Error('Falha ao buscar logs');
    return res.json();
  },
};
