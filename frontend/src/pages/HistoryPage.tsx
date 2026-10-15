import React, { useEffect, useState } from 'react';
import {
  History,
  ShieldCheck,
  RefreshCw,
  Clock,
  Layers,
  ArrowRight,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';
import { api } from '../services/api';
import { Plan, ReplanningAudit, ToolExecutionLog } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { format, parseISO } from 'date-fns';

export const HistoryPage: React.FC = () => {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [audits, setAudits] = useState<ReplanningAudit[]>([]);
  const [toolLogs, setToolLogs] = useState<ToolExecutionLog[]>([]);
  const [activeSubTab, setActiveSubTab] = useState<'plans' | 'audits' | 'tools'>('plans');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadHistory();
  }, []);

  async function loadHistory() {
    try {
      setLoading(true);
      const [pList, aList, tList] = await Promise.all([
        api.listPlans(),
        api.listAudits(),
        api.listToolLogs(),
      ]);
      setPlans(pList);
      setAudits(aList);
      setToolLogs(tList);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Title */}
      <div>
        <h1 className="text-3xl font-extrabold text-white flex items-center gap-3">
          <History className="w-8 h-8 text-teal-400" />
          Plan Version History & Audit Trail
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Complete auditability of stateful LangGraph iterations, replanning triggers, diff summaries, and tool verification records.
        </p>
      </div>

      {/* Sub-navigation */}
      <div className="flex border-b border-slate-800 gap-4">
        <button
          onClick={() => setActiveSubTab('plans')}
          className={`pb-3 text-sm font-semibold transition-all border-b-2 flex items-center gap-2 ${
            activeSubTab === 'plans'
              ? 'border-teal-400 text-teal-300'
              : 'border-transparent text-slate-400 hover:text-white'
          }`}
        >
          <Layers className="w-4 h-4" />
          Plan Versions ({plans.length})
        </button>
        <button
          onClick={() => setActiveSubTab('audits')}
          className={`pb-3 text-sm font-semibold transition-all border-b-2 flex items-center gap-2 ${
            activeSubTab === 'audits'
              ? 'border-teal-400 text-teal-300'
              : 'border-transparent text-slate-400 hover:text-white'
          }`}
        >
          <RefreshCw className="w-4 h-4" />
          Replanning Diffs ({audits.length})
        </button>
        <button
          onClick={() => setActiveSubTab('tools')}
          className={`pb-3 text-sm font-semibold transition-all border-b-2 flex items-center gap-2 ${
            activeSubTab === 'tools'
              ? 'border-teal-400 text-teal-300'
              : 'border-transparent text-slate-400 hover:text-white'
          }`}
        >
          <ShieldCheck className="w-4 h-4" />
          Tool Execution Audit ({toolLogs.length})
        </button>
      </div>

      {/* Plans View */}
      {activeSubTab === 'plans' && (
        <div className="space-y-4">
          {loading ? (
            <div className="py-12 text-center text-slate-500 text-sm">Loading history...</div>
          ) : plans.length === 0 ? (
            <div className="py-12 text-center text-slate-500 text-sm p-6 rounded-2xl bg-slate-900 border border-slate-800">
              No plans generated yet. Head over to the AI Planner to formulate your first plan!
            </div>
          ) : (
            plans.map((p) => (
              <div
                key={p.id}
                className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-3"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-3">
                    <span className="text-base font-bold text-white">Version {p.version}</span>
                    <StatusBadge status={p.status} />
                    {p.parent_plan_id && (
                      <span className="text-xs text-purple-400 bg-purple-500/10 border border-purple-500/20 px-2 py-0.5 rounded">
                        Replanned from parent
                      </span>
                    )}
                  </div>
                  <span className="text-xs text-slate-500 font-mono">
                    {format(parseISO(p.created_at), 'yyyy-MM-dd HH:mm:ss')}
                  </span>
                </div>

                <p className="text-sm text-slate-300">
                  <strong className="text-slate-400">Goal:</strong> "{p.goal_prompt}"
                </p>

                {p.explanation && (
                  <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800/80 text-xs text-slate-400 whitespace-pre-line">
                    {p.explanation}
                  </div>
                )}

                <div className="flex items-center justify-between pt-2 border-t border-slate-800 text-xs text-slate-400">
                  <span>Objective Score: {p.objective_score.toFixed(2)}</span>
                  <span>
                    Items: {p.items.filter((i) => i.is_scheduled).length} scheduled •{' '}
                    {p.items.filter((i) => !i.is_scheduled).length} unscheduled
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Replanning Audits View */}
      {activeSubTab === 'audits' && (
        <div className="space-y-4">
          {audits.length === 0 ? (
            <div className="py-12 text-center text-slate-500 text-sm p-6 rounded-2xl bg-slate-900 border border-slate-800">
              No replanning triggers recorded yet.
            </div>
          ) : (
            audits.map((au) => (
              <div
                key={au.id}
                className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4"
              >
                <div className="flex items-center justify-between">
                  <span className="px-2.5 py-1 rounded text-xs font-bold bg-purple-500/10 text-purple-300 border border-purple-500/30">
                    Trigger: {au.trigger_reason}
                  </span>
                  <span className="text-xs text-slate-500 font-mono">
                    {format(parseISO(au.created_at), 'yyyy-MM-dd HH:mm:ss')}
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                  <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                    <p className="font-semibold text-rose-400 mb-1">Before State:</p>
                    <p className="text-slate-300">{au.before_summary}</p>
                  </div>
                  <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                    <p className="font-semibold text-teal-400 mb-1">After (Revised State):</p>
                    <p className="text-slate-300">{au.after_summary}</p>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Tool Logs View */}
      {activeSubTab === 'tools' && (
        <div className="space-y-4">
          {toolLogs.length === 0 ? (
            <div className="py-12 text-center text-slate-500 text-sm p-6 rounded-2xl bg-slate-900 border border-slate-800">
              No tool executions logged yet.
            </div>
          ) : (
            toolLogs.map((tl) => (
              <div
                key={tl.id}
                className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4 text-xs"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-teal-400">{tl.tool_name}</span>
                    <StatusBadge status={tl.status} />
                    {tl.verified && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3" />
                        Verified
                      </span>
                    )}
                  </div>
                  <p className="text-slate-400 mt-1 font-mono">
                    Latency: {tl.latency_ms}ms • Recorded:{' '}
                    {format(parseISO(tl.created_at), 'yyyy-MM-dd HH:mm:ss')}
                  </p>
                  {tl.error_message && (
                    <p className="text-rose-400 mt-1 font-mono">Error: {tl.error_message}</p>
                  )}
                </div>

                <div className="text-right text-slate-500 font-mono text-[11px] max-w-sm truncate">
                  Input: {JSON.stringify(tl.input_payload)}
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};
