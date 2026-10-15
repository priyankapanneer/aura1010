import React, { useEffect, useState } from 'react';
import {
  CheckCircle2,
  Clock,
  AlertTriangle,
  Calendar as CalendarIcon,
  Sparkles,
  ArrowRight,
  TrendingUp,
  ShieldCheck,
} from 'lucide-react';
import { api } from '../services/api';
import { Task, CalendarEvent, Plan } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { format, parseISO } from 'date-fns';

interface DashboardPageProps {
  onNavigateToPlanner: () => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({ onNavigateToPlanner }) => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  async function loadDashboardData() {
    try {
      setLoading(true);
      const [tList, eList, pList] = await Promise.all([
        api.listTasks(),
        api.listEvents(),
        api.listPlans(),
      ]);
      setTasks(tList);
      setEvents(eList);
      setPlans(pList);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    } finally {
      setLoading(false);
    }
  }

  const completedCount = tasks.filter((t) => t.status === 'COMPLETED').length;
  const pendingCount = tasks.filter((t) => t.status === 'PENDING' || t.status === 'SCHEDULED').length;
  const highPriorityTasks = tasks
    .filter((t) => t.priority >= 4 && t.status !== 'COMPLETED')
    .slice(0, 4);

  const latestPlan = plans[0];

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Hero Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-teal-900/60 via-slate-900 to-slate-900 border border-teal-500/30 p-6 sm:p-8">
        <div className="max-w-2xl space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-teal-500/10 text-teal-300 border border-teal-500/20">
            <Sparkles className="w-3.5 h-3.5" />
            Adaptive Optimization Engine Active
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
            Daily Execution & Schedule Overview
          </h1>
          <p className="text-sm sm:text-base text-slate-300">
            AURA continuously monitors your calendar commitments, task deadlines, and mathematical utilities to optimize your schedule in real time.
          </p>
          <div className="pt-2">
            <button
              onClick={onNavigateToPlanner}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-teal-500 hover:bg-teal-400 text-slate-950 font-bold text-sm transition-all shadow-lg shadow-teal-500/20"
            >
              Plan with AI Assistant
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Pending Tasks</p>
            <p className="text-2xl font-bold text-white mt-1">{pendingCount}</p>
          </div>
          <div className="p-3 rounded-lg bg-cyan-500/10 text-cyan-400">
            <Clock className="w-5 h-5" />
          </div>
        </div>

        <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Completed Tasks</p>
            <p className="text-2xl font-bold text-emerald-400 mt-1">{completedCount}</p>
          </div>
          <div className="p-3 rounded-lg bg-emerald-500/10 text-emerald-400">
            <CheckCircle2 className="w-5 h-5" />
          </div>
        </div>

        <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Fixed Meetings</p>
            <p className="text-2xl font-bold text-white mt-1">{events.length}</p>
          </div>
          <div className="p-3 rounded-lg bg-purple-500/10 text-purple-400">
            <CalendarIcon className="w-5 h-5" />
          </div>
        </div>

        <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Active Plan Versions</p>
            <p className="text-2xl font-bold text-teal-400 mt-1">{latestPlan ? `v${latestPlan.version}` : 'None'}</p>
          </div>
          <div className="p-3 rounded-lg bg-teal-500/10 text-teal-400">
            <TrendingUp className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Main Grid: Schedule vs Priority Tasks */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Today's Schedule Timeline */}
        <div className="lg:col-span-2 space-y-4">
          <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <CalendarIcon className="w-5 h-5 text-teal-400" />
                Today's Timeline & Commitments
              </h2>
              <span className="text-xs text-slate-400">
                {events.length} fixed meetings • {latestPlan?.items?.filter((i) => i.is_scheduled).length || 0} scheduled tasks
              </span>
            </div>

            {loading ? (
              <div className="py-12 text-center text-slate-500 text-sm">Loading schedule data...</div>
            ) : events.length === 0 && (!latestPlan || latestPlan.items.length === 0) ? (
              <div className="py-12 text-center text-slate-500 text-sm">
                No events or planned items scheduled today. Click "Plan with AI Assistant" to build a schedule!
              </div>
            ) : (
              <div className="space-y-3">
                {/* Fixed Events */}
                {events.map((ev) => (
                  <div
                    key={ev.id}
                    className="p-3.5 rounded-xl bg-purple-950/20 border border-purple-500/30 flex items-start justify-between"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-purple-500/20 text-purple-300">
                          Fixed Meeting
                        </span>
                        <h3 className="font-semibold text-white text-sm">{ev.title}</h3>
                      </div>
                      {ev.description && <p className="text-xs text-slate-400 mt-1">{ev.description}</p>}
                    </div>
                    <div className="text-right text-xs font-mono text-purple-300 whitespace-nowrap ml-4">
                      {format(parseISO(ev.start_time), 'HH:mm')} - {format(parseISO(ev.end_time), 'HH:mm')}
                    </div>
                  </div>
                ))}

                {/* Scheduled Tasks from Latest Plan */}
                {latestPlan?.items
                  ?.filter((it) => it.is_scheduled && it.scheduled_start && it.scheduled_end)
                  .map((it) => (
                    <div
                      key={it.id}
                      className="p-3.5 rounded-xl bg-teal-950/20 border border-teal-500/30 flex items-start justify-between"
                    >
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-teal-500/20 text-teal-300">
                            Planned Task
                          </span>
                          <h3 className="font-semibold text-white text-sm">{it.task_title || it.task_id}</h3>
                        </div>
                        <div className="flex items-center gap-3 mt-1 text-xs text-slate-400">
                          <span>Utility Score: {it.utility_score.toFixed(2)}</span>
                          <StatusBadge status={it.status} />
                        </div>
                      </div>
                      <div className="text-right text-xs font-mono text-teal-300 whitespace-nowrap ml-4">
                        {format(parseISO(it.scheduled_start!), 'HH:mm')} -{' '}
                        {format(parseISO(it.scheduled_end!), 'HH:mm')}
                      </div>
                    </div>
                  ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: High-Priority Tasks & Recent Audits */}
        <div className="space-y-6">
          {/* Priority Tasks */}
          <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800">
            <h2 className="text-lg font-bold text-white flex items-center gap-2 mb-4">
              <AlertTriangle className="w-5 h-5 text-amber-400" />
              High-Priority Work
            </h2>
            {highPriorityTasks.length === 0 ? (
              <p className="text-sm text-slate-500">No urgent tasks pending.</p>
            ) : (
              <div className="space-y-3">
                {highPriorityTasks.map((t) => (
                  <div key={t.id} className="p-3 rounded-lg bg-slate-800/60 border border-slate-700/60">
                    <div className="flex items-start justify-between">
                      <h4 className="font-medium text-sm text-white line-clamp-1">{t.title}</h4>
                      <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-300">
                        P{t.priority}
                      </span>
                    </div>
                    <div className="flex items-center justify-between mt-2 text-xs text-slate-400">
                      <span>{t.estimated_duration_minutes} min</span>
                      {t.deadline && <span>Due: {format(parseISO(t.deadline), 'HH:mm')}</span>}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Verification & Audit Snapshot */}
          <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-3">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-emerald-400" />
              Verified Execution Status
            </h2>
            <p className="text-xs text-slate-400">
              Every external calendar write and task mutation is strictly authenticated and validated server-side with zero unverified claims.
            </p>
            {latestPlan?.tool_logs && latestPlan.tool_logs.length > 0 ? (
              <div className="text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 p-2.5 rounded-lg flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                <span>Last tool action ({latestPlan.tool_logs[0].tool_name}) verified in {latestPlan.tool_logs[0].latency_ms}ms</span>
              </div>
            ) : (
              <div className="text-xs text-slate-500">No tool actions recorded yet.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
