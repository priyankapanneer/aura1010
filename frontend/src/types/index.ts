export type TaskStatus = 'PENDING' | 'SCHEDULED' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED' | 'CANCELLED';

export interface Task {
  id: string;
  user_id: string;
  title: string;
  description?: string | null;
  estimated_duration_minutes: number;
  deadline?: string | null;
  priority: number;
  utility_score: number;
  status: TaskStatus;
  mandatory: boolean;
  source: string;
  confidence: number;
  created_at: string;
  updated_at: string;
  dependencies: string[];
}

export interface CalendarEvent {
  id: string;
  user_id: string;
  title: string;
  description?: string | null;
  start_time: string;
  end_time: string;
  is_fixed: boolean;
  external_event_id?: string | null;
  source: string;
  created_at: string;
}

export interface PlanItem {
  id: string;
  task_id: string;
  task_title?: string;
  scheduled_start?: string | null;
  scheduled_end?: string | null;
  order_index: number;
  is_scheduled: boolean;
  unscheduled_reason?: string | null;
  utility_score: number;
  status: string;
}

export interface ApprovalRequest {
  id: string;
  action_type: string;
  payload: any;
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
  response_reason?: string | null;
  created_at: string;
  resolved_at?: string | null;
}

export interface ToolExecutionLog {
  id: string;
  tool_name: string;
  input_payload: any;
  output_payload?: any;
  status: string;
  verified: boolean;
  verification_details?: any;
  error_message?: string | null;
  latency_ms: number;
  created_at: string;
}

export interface ReplanningAudit {
  id: string;
  trigger_reason: string;
  before_summary: string;
  after_summary: string;
  changes: any;
  created_at: string;
}

export interface Plan {
  id: string;
  user_id: string;
  goal_prompt: string;
  status: 'DRAFT' | 'PROPOSED' | 'APPROVED' | 'REJECTED' | 'EXECUTED' | 'REPLANNED';
  version: number;
  parent_plan_id?: string | null;
  objective_score: number;
  explanation?: string | null;
  items: PlanItem[];
  approval_requests: ApprovalRequest[];
  tool_logs: ToolExecutionLog[];
  replanning_audits: ReplanningAudit[];
  created_at: string;
  updated_at: string;
}

export interface UserSettings {
  id: string;
  user_id: string;
  work_start_time: string;
  work_end_time: string;
  break_duration_minutes: string;
  buffer_minutes_between_tasks: string;
  utility_weights: {
    urgency: number;
    importance: number;
    impact: number;
    dependency: number;
    efficiency: number;
  };
  demo_mode: boolean;
  auto_replan_on_conflict: boolean;
}

export interface IntegrationStatus {
  llm_provider: string;
  llm_model: string;
  is_mock_llm: boolean;
  has_gemini_key: boolean;
  has_openai_key: boolean;
  has_anthropic_key: boolean;
  calendar_provider: string;
  is_simulated_calendar: boolean;
  demo_mode: boolean;
}

export interface EvaluationScenarioResult {
  scenario_name: string;
  total_tasks: number;
  method_a: { violations: number; scheduled: number; utility: number };
  method_b: { violations: number; scheduled: number; utility: number };
  method_c: { violations: number; scheduled: number; utility: number };
}

export interface EvaluationReport {
  timestamp: string;
  scenarios_evaluated: number;
  method_summary: {
    [methodName: string]: {
      feasibility_rate_pct: number;
      hard_constraint_violations: number;
      total_utility_achieved: number;
      scheduled_task_completion_pct: number;
      avg_latency_ms: number;
    };
  };
  scenario_details: EvaluationScenarioResult[];
}
