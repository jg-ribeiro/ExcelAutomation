import { 
  Job, 
  JobFormData, 
  Execution, 
  Alert, 
  SystemStatus, 
  LogEntry, 
  User, 
  AuthResponse, 
  BootstrapStatus 
} from '../types';

const API_BASE = '/api';
const TOKEN_KEY = 'excel_auto_token';
const USER_KEY = 'excel_auto_user';

export const authStorage = {
  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  },
  setToken(token: string) {
    localStorage.setItem(TOKEN_KEY, token);
  },
  getUser(): User | null {
    const raw = localStorage.getItem(USER_KEY);
    if (!raw) return null;
    try {
      return JSON.parse(raw);
    } catch {
      return null;
    }
  },
  setUser(user: User) {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  },
  clear() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }
};

async function customFetch(endpoint: string, options: RequestInit = {}): Promise<Response> {
  const headers = new Headers(options.headers || {});
  const token = authStorage.getToken();
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status === 401 && !endpoint.includes('/auth/login')) {
    authStorage.clear();
    window.dispatchEvent(new Event('auth:unauthorized'));
  }

  return response;
}

export const api = {
  // Autenticação AD
  async getBootstrapStatus(): Promise<BootstrapStatus> {
    const res = await customFetch('/auth/bootstrap-status');
    if (!res.ok) throw new Error('Falha ao verificar status de inicialização');
    return res.json();
  },

  async login(username: string, password: string): Promise<AuthResponse> {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Falha de autenticação no Active Directory');
    }

    const data: AuthResponse = await res.json();
    authStorage.setToken(data.access_token);
    authStorage.setUser(data.user);
    return data;
  },

  async getMe(): Promise<User> {
    const res = await customFetch('/auth/me');
    if (!res.ok) throw new Error('Sessão expirada');
    const user: User = await res.json();
    authStorage.setUser(user);
    return user;
  },

  // System Status
  async getSystemStatus(): Promise<SystemStatus> {
    const res = await customFetch('/system/status');
    if (!res.ok) throw new Error('Falha ao obter status do sistema');
    return res.json();
  },

  // Jobs
  async getJobs(): Promise<Job[]> {
    const res = await customFetch('/jobs');
    if (!res.ok) throw new Error('Falha ao listar jobs');
    return res.json();
  },

  async getJob(id: number): Promise<Job> {
    const res = await customFetch(`/jobs/${id}`);
    if (!res.ok) throw new Error(`Falha ao obter job #${id}`);
    return res.json();
  },

  async createJob(data: JobFormData): Promise<Job> {
    const res = await customFetch('/jobs', {
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
    const res = await customFetch(`/jobs/${id}`, {
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
    const res = await customFetch(`/jobs/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error(`Falha ao excluir job #${id}`);
  },

  async runJobNow(id: number): Promise<{ success: boolean; message: string; execution_id: number }> {
    const res = await customFetch(`/jobs/${id}/run`, { method: 'POST' });
    if (!res.ok) throw new Error(`Falha ao disparar execução para job #${id}`);
    return res.json();
  },

  async toggleJobActive(id: number): Promise<{ success: boolean; is_active: boolean; message: string }> {
    const res = await customFetch(`/jobs/${id}/toggle-active`, { method: 'POST' });
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

    const res = await customFetch(`/executions?${query.toString()}`);
    if (!res.ok) throw new Error('Falha ao listar execuções');
    return res.json();
  },

  async getExecution(id: number): Promise<Execution> {
    const res = await customFetch(`/executions/${id}`);
    if (!res.ok) throw new Error(`Falha ao obter execução #${id}`);
    return res.json();
  },

  // Alerts
  async getAlerts(status?: string): Promise<Alert[]> {
    const query = status ? `?status=${encodeURIComponent(status)}` : '';
    const res = await customFetch(`/alerts${query}`);
    if (!res.ok) throw new Error('Falha ao obter alertas');
    return res.json();
  },

  async dismissAlert(id: number): Promise<void> {
    const res = await customFetch(`/alerts/${id}/dismiss`, { method: 'POST' });
    if (!res.ok) throw new Error(`Falha ao dispensar alerta #${id}`);
  },

  async resolveAlert(id: number): Promise<void> {
    const res = await customFetch(`/alerts/${id}/resolve`, { method: 'POST' });
    if (!res.ok) throw new Error(`Falha ao resolver alerta #${id}`);
  },

  // Logs
  async getLogs(params?: { limit?: number; level?: string; search?: string }): Promise<{ total: number; logs: LogEntry[] }> {
    const query = new URLSearchParams();
    if (params?.limit) query.append('limit', params.limit.toString());
    if (params?.level) query.append('level', params.level);
    if (params?.search) query.append('search', params.search);

    const res = await customFetch(`/logs?${query.toString()}`);
    if (!res.ok) throw new Error('Falha ao buscar logs');
    return res.json();
  },

  // Gestão de Usuários (Apenas Administrador)
  async getUsers(): Promise<User[]> {
    const res = await customFetch('/users');
    if (!res.ok) throw new Error('Falha ao carregar lista de usuários');
    return res.json();
  },

  async authorizeUser(data: { username: string; display_name?: string; role: 'ADMIN' | 'OPERATOR'; is_active?: boolean }): Promise<User> {
    const res = await customFetch('/users', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Falha ao autorizar usuário');
    }
    return res.json();
  },

  async updateUser(id: number, data: { display_name?: string; role?: 'ADMIN' | 'OPERATOR'; is_active?: boolean }): Promise<User> {
    const res = await customFetch(`/users/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Falha ao atualizar usuário');
    }
    return res.json();
  },

  async deleteUser(id: number): Promise<void> {
    const res = await customFetch(`/users/${id}`, { method: 'DELETE' });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Falha ao revogar usuário');
    }
  },

  async toggleUserActive(id: number): Promise<{ success: boolean; is_active: boolean; message: string }> {
    const res = await customFetch(`/users/${id}/toggle-active`, { method: 'POST' });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Falha ao alterar status do usuário');
    }
    return res.json();
  },
};
