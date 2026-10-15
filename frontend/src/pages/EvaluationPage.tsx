import React, { useEffect, useState } from 'react';
import { BarChart3, Play, RefreshCw, CheckCircle2, AlertOctagon, TrendingUp, Cpu } from 'lucide-react';
import { api } from '../services/api';
import { EvaluationReport } from '../types';

export const EvaluationPage: React.FC = () => {
  const [report, setReport] = useState<EvaluationReport | null>(null);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    loadResults();
  }, []);

  async function loadResults() {
    try {
      const data = await api.getEvaluationResults();
      setReport(data);
    } catch (err) {
      console.error(err);
    }
  }

  async function handleRunEvaluation() {
    try {
      setRunning(true);
      const data = await api.runEvaluation();
      setReport(data);
    } catch (err: any) {
      alert(err.message || 'Benchmark run failed');
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-white flex items-center gap-3">
            <BarChart3 className="w-8 h-8 text-teal-400" />
            Research Benchmark & Empirical Evaluation
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Quantitative comparison of Static LLM Planning, Baseline Heuristic Scheduling, and AURA Adaptive LangGraph.
          </p>
        </div>

        <button
          onClick={handleRunEvaluation}
          disabled={running}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-teal-500 hover:bg-teal-400 disabled:opacity-50 text-slate-950 font-bold text-sm shadow-lg transition-all shrink-0"
        >
          {running ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              Running Benchmark...
            </>
          ) : (
            <>
              <Play className="w-4 h-4" />
              Execute Benchmark Suite
            </>
          )}
        </button>
      </div>

      {/* Research Question Card */}
      <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-2">
        <h2 className="text-xs font-bold text-teal-400 uppercase tracking-wider">
          Primary Research Question
        </h2>
        <p className="text-sm text-slate-200 italic font-medium leading-relaxed">
          "Does utility-aware adaptive replanning improve task completion and schedule feasibility compared with static LLM planning and conventional constraint-based scheduling?"
        </p>
      </div>

      {/* Summary Cards */}
      {report && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {Object.entries(report.method_summary).map(([mName, mStats]) => {
              const isAura = mName.includes('AURA');
              return (
                <div
                  key={mName}
                  className={`p-6 rounded-2xl border space-y-4 ${
                    isAura
                      ? 'bg-gradient-to-b from-teal-950/40 to-slate-900 border-teal-500/40 shadow-lg shadow-teal-500/10'
                      : 'bg-slate-900 border-slate-800'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <h3 className="font-bold text-sm text-white">{mName}</h3>
                    {isAura && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-teal-500/20 text-teal-300">
                        Proposed System
                      </span>
                    )}
                  </div>

                  <div className="space-y-2.5 text-xs">
                    <div className="flex justify-between items-center">
                      <span className="text-slate-400">Schedule Feasibility:</span>
                      <span
                        className={`font-mono font-bold ${
                          mStats.feasibility_rate_pct === 100
                            ? 'text-emerald-400'
                            : mStats.feasibility_rate_pct > 0
                            ? 'text-amber-400'
                            : 'text-rose-400'
                        }`}
                      >
                        {mStats.feasibility_rate_pct}%
                      </span>
                    </div>

                    <div className="flex justify-between items-center">
                      <span className="text-slate-400">Constraint Violations:</span>
                      <span
                        className={`font-mono font-bold ${
                          mStats.hard_constraint_violations === 0 ? 'text-emerald-400' : 'text-rose-400'
                        }`}
                      >
                        {mStats.hard_constraint_violations}
                      </span>
                    </div>

                    <div className="flex justify-between items-center">
                      <span className="text-slate-400">Weighted Utility Achieved:</span>
                      <span className="font-mono font-bold text-teal-300">
                        {mStats.total_utility_achieved.toFixed(2)}
                      </span>
                    </div>

                    <div className="flex justify-between items-center">
                      <span className="text-slate-400">Task Completion Rate:</span>
                      <span className="font-mono font-bold text-slate-200">
                        {mStats.scheduled_task_completion_pct}%
                      </span>
                    </div>

                    <div className="flex justify-between items-center">
                      <span className="text-slate-400">Average Solve Latency:</span>
                      <span className="font-mono text-slate-400">{mStats.avg_latency_ms} ms</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Scenario Details Breakdown */}
          <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
            <h3 className="text-base font-bold text-white">Scenario-by-Scenario Performance Breakdown</h3>
            <div className="space-y-4">
              {report.scenario_details.map((sc, i) => (
                <div key={i} className="p-4 rounded-xl bg-slate-950 border border-slate-800/80 space-y-2 text-xs">
                  <h4 className="font-semibold text-sm text-slate-200">{sc.scenario_name}</h4>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
                    <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                      <p className="font-semibold text-slate-400 mb-1">Static LLM / Heuristic:</p>
                      <p className="text-rose-400 font-mono">Violations: {sc.method_a.violations}</p>
                      <p className="text-slate-300 font-mono">Scheduled: {sc.method_a.scheduled}</p>
                      <p className="text-teal-400 font-mono">Utility: {sc.method_a.utility}</p>
                    </div>

                    <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                      <p className="font-semibold text-slate-400 mb-1">Unweighted Constraint:</p>
                      <p className="text-emerald-400 font-mono">Conflicts: {sc.method_b.violations}</p>
                      <p className="text-slate-300 font-mono">Scheduled: {sc.method_b.scheduled}</p>
                      <p className="text-teal-400 font-mono">Utility: {sc.method_b.utility}</p>
                    </div>

                    <div className="p-3 rounded-lg bg-teal-950/20 border border-teal-500/30">
                      <p className="font-semibold text-teal-300 mb-1">AURA Hybrid System:</p>
                      <p className="text-emerald-400 font-mono">Conflicts: {sc.method_c.violations}</p>
                      <p className="text-slate-200 font-mono">Scheduled: {sc.method_c.scheduled}</p>
                      <p className="text-teal-400 font-mono font-bold">Utility: {sc.method_c.utility}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
