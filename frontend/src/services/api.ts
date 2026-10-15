import {
  Task,
  CalendarEvent,
  Plan,
  UserSettings,
  IntegrationStatus,
  EvaluationReport,
  ToolExecutionLog,
  ReplanningAudit,
} from '../types';

const API_BASE = '/api/v1';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${url}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    let errorDetail = 'API Request Failed';
    try {
      const err = await response.json();
      errorDetail = err.detail || JSON.stringify(err);
    } catch {
      errorDetail = await response.text();
    }
    throw new Error(errorDetail);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

export const api = {
  // Tasks
  async listTasks(params?: { status?: string; mandatory?: boolean }): Promise<Task[]> {
    const query = new URLSearchParams();
    if (params?.status) query.append('status', params.status);
    if (params?.mandatory !== undefined) query.append('mandatory', String(params.mandatory));
    const qs = query.toString() ? `?${query.toString()}` : '';
    return fetchJson<Task[]>(`/tasks${qs}`);
  },

  async createTask(data: Partial<Task>): Promise<Task> {
    return fetchJson<Task>('/tasks', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async updateTask(id: string, updates: Partial<Task>): Promise<Task> {
    return fetchJson<Task>(`/tasks/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
  },

  async deleteTask(id: string): Promise<void> {
    return fetchJson<void>(`/tasks/${id}`, {
      method: 'DELETE',
    });
  },

  // Calendar
  async listEvents(): Promise<CalendarEvent[]> {
    return fetchJson<CalendarEvent[]>('/calendar/events');
  },

  async createEvent(data: Partial<CalendarEvent>): Promise<CalendarEvent> {
    return fetchJson<CalendarEvent>('/calendar/events', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async deleteEvent(id: string): Promise<void> {
    return fetchJson<void>(`/calendar/events/${id}`, {
      method: 'DELETE',
    });
  },

  // Plans
  async generatePlan(goalPrompt: string, autoApprove: boolean = false): Promise<Plan> {
    return fetchJson<Plan>('/plans', {
      method: 'POST',
      body: JSON.stringify({ goal_prompt: goalPrompt, auto_approve_simulated: autoApprove }),
    });
  },

  async listPlans(): Promise<Plan[]> {
    return fetchJson<Plan[]>('/plans');
  },

  async getPlan(id: string): Promise<Plan> {
    return fetchJson<Plan>(`/plans/${id}`);
  },

  async approvePlan(id: string, reason?: string): Promise<Plan> {
    return fetchJson<Plan>(`/plans/${id}/approve`, {
      method: 'POST',
      body: JSON.stringify({ approved: true, response_reason: reason }),
    });
  },

  async rejectPlan(id: string, reason?: string): Promise<Plan> {
    return fetchJson<Plan>(`/plans/${id}/reject`, {
      method: 'POST',
      body: JSON.stringify({ approved: false, response_reason: reason }),
    });
  },

  async triggerReplan(id: string, reason: string): Promise<Plan> {
    return fetchJson<Plan>(`/plans/${id}/replan`, {
      method: 'POST',
      body: JSON.stringify({ trigger_reason: reason }),
    });
  },

  // Settings
  async getSettings(): Promise<UserSettings> {
    return fetchJson<UserSettings>('/settings');
  },

  async updateSettings(updates: Partial<UserSettings>): Promise<UserSettings> {
    return fetchJson<UserSettings>('/settings', {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
  },

  async getIntegrations(): Promise<IntegrationStatus> {
    return fetchJson<IntegrationStatus>('/settings/integrations');
  },

  // History
  async listAudits(): Promise<ReplanningAudit[]> {
    return fetchJson<ReplanningAudit[]>('/history/audits');
  },

  async listToolLogs(): Promise<ToolExecutionLog[]> {
    return fetchJson<ToolExecutionLog[]>('/history/tools');
  },

  // Evaluation
  async runEvaluation(): Promise<EvaluationReport> {
    return fetchJson<EvaluationReport>('/evaluation/run', {
      method: 'POST',
    });
  },

  async getEvaluationResults(): Promise<EvaluationReport> {
    return fetchJson<EvaluationReport>('/evaluation/results');
  },
};
