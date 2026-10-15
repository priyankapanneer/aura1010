import React, { useState } from 'react';
import {
  Sparkles,
  Send,
  CheckCircle2,
  XCircle,
  RefreshCw,
  AlertOctagon,
  Clock,
  Layers,
  ArrowRight,
  ShieldAlert,
} from 'lucide-react';
import { api } from '../services/api';
import { Plan } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { format, parseISO } from 'date-fns';

const EXAMPLE_PROMPTS = [
  'Plan my day. I have a project deadline at 5 PM, two meetings, three pending tasks, and I need one hour to study.',
  'I need to schedule urgent code review before 3 PM, write documentation for 45 minutes, and take a 30-minute break.',
  'Prioritize my mandatory deliverables today, avoid scheduling anything during lunch, and maximize deep work.',
];

const WORKFLOW_STAGES = [
  'parse_goal',
  'load_user_context',
  'decompose_tasks',
  'calculate_utility',
  'generate_schedule',
  'validate_constraints',
  'present_plan',
];

export const PlannerPage: React.FC = () => {
  const [goalPrompt, setGoalPrompt] = useState('');
  const [planning, setPlanning] = useState(false);
  const [currentStageIdx, setCurrentStageIdx] = useState<number>(-1);
  const [plan, setPlan] = useState<Plan | null>(null);
  const [rejectionModalOpen, setRejectionModalOpen] = useState(false);
  const [rejectionReason, setRejectionReason] = useState('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  async function handleGeneratePlan(promptText?: string) {
    const textToSubmit = promptText || goalPrompt;
    if (!textToSubmit.trim()) return;

    try {
      setPlanning(true);
      setErrorMsg(null);
      setPlan(null);

      // Simulate stepper progression through LangGraph stages
      for (let i = 0; i < WORKFLOW_STAGES.length; i++) {
        setCurrentStageIdx(i);
        await new Promise((r) => setTimeout(r, 200));
      }

      const generatedPlan = await api.generatePlan(textToSubmit, false);
      setPlan(generatedPlan);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to generate plan');
    } finally {
      setPlanning(false);
      setCurrentStageIdx(-1);
    }
  }

  async function handleApprove() {
    if (!plan) return;
    try {
      setPlanning(true);
      const approvedPlan = await api.approvePlan(plan.id, 'Approved via AI Planner dashboard');
      setPlan(approvedPlan);
    } catch (err: any) {
      setErrorMsg(err.message || 'Approval execution failed');
    } finally {
      setPlanning(false);
    }
  }

  async function handleReject() {
    if (!plan) return;
    try {
      setPlanning(true);
      const rejectedPlan = await api.rejectPlan(plan.id, rejectionReason || 'User rejected proposed plan');
      setPlan(rejectedPlan);
      setRejectionModalOpen(false);
      setRejectionReason('');
    } catch (err: any) {
      setErrorMsg(err.message || 'Rejection failed');
    } finally {
      setPlanning(false);
    }
  }

  async function handleTriggerReplan(reason: string) {
    if (!plan) return;
    try {
      setPlanning(true);
      setErrorMsg(null);
      const replanned = await api.triggerReplan(plan.id, reason);
      setPlan(replanned);
    } catch (err: any) {
      setErrorMsg(err.message || 'Replanning failed');
    } finally {
      setPlanning(false);
    }
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Title */}
      <div>
        <h1 className="text-3xl font-extrabold text-white flex items-center gap-3">
          <Sparkles className="w-8 h-8 text-teal-400" />
          Autonomous AI Planner & HITL Execution
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Stateful LangGraph workflow paired with Google OR-Tools constraint satisfaction and human-in-the-loop approval.
        </p>
      </div>

      {/* Input Box */}
      <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
        <label className="block text-sm font-semibold text-slate-200">
          State Your Planning Objective
        </label>
        <div className="flex gap-2">
          <textarea
            value={goalPrompt}
            onChange={(e) => setGoalPrompt(e.target.value)}
            placeholder="e.g. Plan my day. I have a project deadline at 5 PM, two meetings, three pending tasks, and I need one hour to study."
            rows={3}
            className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-800 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-teal-500 text-sm"
          />
        </div>

        {/* Example Prompt Chips */}
        <div className="space-y-1.5">
          <p className="text-xs font-medium text-slate-400">Quick Test Scenarios:</p>
          <div className="flex flex-wrap gap-2">
            {EXAMPLE_PROMPTS.map((ex, i) => (
              <button
                key={i}
                onClick={() => {
                  setGoalPrompt(ex);
                  handleGeneratePlan(ex);
                }}
                className="text-xs px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/80 transition-all text-left"
              >
                {ex}
              </button>
            ))}
          </div>
        </div>

        <div className="flex justify-end pt-2">
          <button
            onClick={() => handleGeneratePlan()}
            disabled={planning || !goalPrompt.trim()}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-teal-500 hover:bg-teal-400 disabled:opacity-50 text-slate-950 font-bold text-sm transition-all shadow-lg shadow-teal-500/20"
          >
            {planning ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Optimizing Workflow...
              </>
            ) : (
              <>
                <Send className="w-4 h-4" />
                Generate Plan
              </>
            )}
          </button>
        </div>
      </div>

      {/* Error Message */}
      {errorMsg && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm flex items-center gap-2">
          <AlertOctagon className="w-5 h-5 shrink-0" />
          {errorMsg}
        </div>
      )}

      {/* Progress Stepper Visualizer */}
      {planning && (
        <div className="p-6 rounded-2xl bg-slate-900 border border-teal-500/30 space-y-4">
          <h3 className="text-sm font-bold text-teal-400 uppercase tracking-wider flex items-center gap-2">
            <Layers className="w-4 h-4" />
            LangGraph Execution Pipeline In Progress
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2">
            {WORKFLOW_STAGES.map((stg, idx) => (
              <div
                key={stg}
                className={`p-2.5 rounded-lg border text-xs font-mono text-center transition-all ${
                  idx === currentStageIdx
                    ? 'bg-teal-500/20 text-teal-300 border-teal-400 animate-pulse'
                    : idx < currentStageIdx
                    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                    : 'bg-slate-950 text-slate-500 border-slate-800'
                }`}
              >
                {stg}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Plan Results View */}
      {plan && (
        <div className="space-y-6">
          {/* Header Card */}
          <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-3">
                <h2 className="text-xl font-bold text-white">Plan Version {plan.version}</h2>
                <StatusBadge status={plan.status} />
              </div>
              <p className="text-xs text-slate-400 mt-1">Goal: "{plan.goal_prompt}"</p>
            </div>

            {/* Approval Controls */}
            {plan.status === 'PROPOSED' && (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setRejectionModalOpen(true)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-rose-950/40 text-rose-300 hover:text-rose-200 border border-rose-500/30 font-semibold text-sm transition-all"
                >
                  <XCircle className="w-4 h-4 inline mr-1.5" />
                  Reject
                </button>
                <button
                  onClick={handleApprove}
                  className="px-5 py-2 rounded-xl bg-teal-500 hover:bg-teal-400 text-slate-950 font-bold text-sm transition-all shadow-lg shadow-teal-500/20"
                >
                  <CheckCircle2 className="w-4 h-4 inline mr-1.5" />
                  Approve & Commit
                </button>
              </div>
            )}

            {/* Replanning Controls */}
            {plan.status === 'EXECUTED' && (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleTriggerReplan('DYNAMIC_TASK_SLIPPAGE_60_MIN')}
                  className="px-3.5 py-2 rounded-xl bg-purple-500/10 hover:bg-purple-500/20 text-purple-300 border border-purple-500/30 text-xs font-semibold transition-all flex items-center gap-1.5"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  Simulate Delay & Replan
                </button>
                <button
                  onClick={() => handleTriggerReplan('UNEXPECTED_URGENT_TASK_INSERTED')}
                  className="px-3.5 py-2 rounded-xl bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/30 text-xs font-semibold transition-all flex items-center gap-1.5"
                >
                  <AlertOctagon className="w-3.5 h-3.5" />
                  Insert Urgent Task & Replan
                </button>
              </div>
            )}
          </div>

          {/* Rationale & Explanation */}
          {plan.explanation && (
            <div className="p-5 rounded-xl bg-slate-900 border border-slate-800">
              <h3 className="text-xs font-bold text-teal-400 uppercase tracking-wider mb-2">
                Decision Explanation & Rationale
              </h3>
              <p className="text-sm text-slate-300 whitespace-pre-line leading-relaxed">
                {plan.explanation}
              </p>
            </div>
          )}

          {/* Two Columns: Scheduled vs Unscheduled */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Scheduled Tasks */}
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                Scheduled Tasks ({plan.items.filter((i) => i.is_scheduled).length})
              </h3>
              <div className="space-y-3">
                {plan.items
                  .filter((it) => it.is_scheduled)
                  .map((it) => (
                    <div
                      key={it.id}
                      className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between"
                    >
                      <div>
                        <h4 className="font-semibold text-sm text-white">{it.task_title || it.task_id}</h4>
                        <div className="flex items-center gap-3 mt-1 text-xs text-slate-400">
                          <span>Slot #{it.order_index + 1}</span>
                          <span className="text-teal-400">Utility: {it.utility_score.toFixed(2)}</span>
                        </div>
                      </div>
                      <div className="text-right text-xs font-mono text-teal-300">
                        {it.scheduled_start && it.scheduled_end
                          ? `${format(parseISO(it.scheduled_start), 'HH:mm')} - ${format(
                              parseISO(it.scheduled_end),
                              'HH:mm'
                            )}`
                          : 'TBD'}
                      </div>
                    </div>
                  ))}
              </div>
            </div>

            {/* Unscheduled Tasks / Conflicts */}
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <ShieldAlert className="w-5 h-5 text-amber-400" />
                Unscheduled Items & Conflict Diagnostics ({plan.items.filter((i) => !i.is_scheduled).length})
              </h3>
              {plan.items.filter((i) => !i.is_scheduled).length === 0 ? (
                <p className="text-sm text-slate-500 py-6 text-center">
                  All candidate tasks were feasible and successfully scheduled! Zero conflicts.
                </p>
              ) : (
                <div className="space-y-3">
                  {plan.items
                    .filter((it) => !it.is_scheduled)
                    .map((it) => (
                      <div
                        key={it.id}
                        className="p-3.5 rounded-xl bg-amber-950/20 border border-amber-500/30"
                      >
                        <h4 className="font-semibold text-sm text-amber-200">{it.task_title || it.task_id}</h4>
                        <p className="text-xs text-slate-300 mt-1">
                          <strong className="text-amber-400">Conflict Reason:</strong> {it.unscheduled_reason}
                        </p>
                      </div>
                    ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Rejection Modal */}
      {rejectionModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
          <div className="max-w-md w-full bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <XCircle className="w-5 h-5 text-rose-400" />
              Reject Proposed Plan
            </h3>
            <p className="text-sm text-slate-400">
              Please specify why you are rejecting this proposed schedule. The agent will record this reasoning and abort calendar commits.
            </p>
            <textarea
              value={rejectionReason}
              onChange={(e) => setRejectionReason(e.target.value)}
              placeholder="e.g. Schedule is too crowded; prefer shifting tasks to tomorrow."
              rows={3}
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-teal-500 text-sm"
            />
            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setRejectionModalOpen(false)}
                className="px-4 py-2 rounded-xl text-slate-400 hover:text-white text-sm"
              >
                Cancel
              </button>
              <button
                onClick={handleReject}
                className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-semibold text-sm transition-all"
              >
                Confirm Rejection
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
