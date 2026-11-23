export type ScheduleType = 'daily' | 'interval' | 'manual';

export interface Job {
  id: number;
  name: string;
  file_path: string;
  macro_name: string | null;
  schedule_type: ScheduleType;
  schedule_value: string;
  is_active: boolean;
  pause_reason: string | null;
  query_timeout: number;
  lock_timeout: number;
  created_at?: string;
  updated_at?: string;
  avg_duration_seconds?: number | null;
  last_status?: string | null;
  last_run_at?: string | null;
  next_run_at?: string | null;
  has_conflict: boolean;
  conflict_message?: string | null;
  duration_ratio?: number | null;
}

export interface JobFormData {
  name: string;
  file_path: string;
  macro_name: string;
  schedule_type: ScheduleType;
  schedule_value: string;
  is_active: boolean;
  query_timeout: number;
  lock_timeout: number;
}

export interface Execution {
  id: number;
  job_id: number;
  job_name?: string;
  status: 'queued' | 'running' | 'success' | 'failed' | 'timeout' | 'lock_timeout' | 'aborted';
  trigger_type: 'schedule' | 'manual' | 'retry';
  started_at?: string | null;
  finished_at?: string | null;
  duration_seconds?: number | null;
  excel_pid?: number | null;
  error_message?: string | null;
  log_snippet?: string | null;
}

export interface Alert {
  id: number;
  job_id: number;
  job_name?: string;
  alert_type: string;
  severity: 'warning' | 'critical';
  title: string;
  message: string;
  details_json?: string | null;
  status: 'pending' | 'acknowledged' | 'auto_paused' | 'resolved';
  consecutive_count: number;
  action_deadline?: string | null;
  created_at: string;
  resolved_at?: string | null;
}

export interface QueuedJob {
  job_id: number;
  job_name: string;
  execution_id: number;
}

export interface SystemStatus {
  is_worker_running: boolean;
  current_job?: {
    job_id: number;
    job_name: string;
    execution_id: number;
    started_at: string;
  } | null;
  queue_length: number;
  queued_jobs: QueuedJob[];
  total_jobs: number;
  active_jobs: number;
  pending_alerts: number;
  last_execution?: Execution | null;
  server_time: string;
}

export interface LogEntry {
  id: string;
  timestamp: string;
  level: 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';
  name: string;
  message: string;
}
