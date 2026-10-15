import React, { useEffect, useState } from 'react';
import { Settings as SettingsIcon, Sliders, Cpu, Save, CheckCircle2 } from 'lucide-react';
import { api } from '../services/api';
import { UserSettings, IntegrationStatus } from '../types';

export const SettingsPage: React.FC = () => {
  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [integrations, setIntegrations] = useState<IntegrationStatus | null>(null);
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [loading, setLoading] = useState(true);

  // Form State
  const [workStart, setWorkStart] = useState('09:00');
  const [workEnd, setWorkEnd] = useState('18:00');
  const [weights, setWeights] = useState({
    urgency: 0.35,
    importance: 0.25,
    impact: 0.15,
    dependency: 0.15,
    efficiency: 0.10,
  });

  useEffect(() => {
    loadSettings();
  }, []);

  async function loadSettings() {
    try {
      setLoading(true);
      const [sData, iData] = await Promise.all([api.getSettings(), api.getIntegrations()]);
      setSettings(sData);
      setIntegrations(iData);
      setWorkStart(sData.work_start_time);
      setWorkEnd(sData.work_end_time);
      if (sData.utility_weights) setWeights(sData.utility_weights);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  function handleWeightChange(key: keyof typeof weights, value: number) {
    const newWeights = { ...weights, [key]: value };
    setWeights(newWeights);
  }

  async function handleSaveSettings() {
    try {
      await api.updateSettings({
        work_start_time: workStart,
        work_end_time: workEnd,
        utility_weights: weights,
      });
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
      loadSettings();
    } catch (err: any) {
      alert(err.message || 'Failed to update settings');
    }
  }

  const weightSum = Object.values(weights).reduce((a, b) => a + b, 0);

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Title */}
      <div>
        <h1 className="text-3xl font-extrabold text-white flex items-center gap-3">
          <SettingsIcon className="w-8 h-8 text-teal-400" />
          Settings & Optimization Parameters
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Configure working horizons, mathematical utility scoring weights, and check AI integration status.
        </p>
      </div>

      {savedSuccess && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-sm flex items-center gap-2">
          <CheckCircle2 className="w-5 h-5" />
          Settings updated successfully!
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Working Hours & Horizon */}
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Sliders className="w-5 h-5 text-teal-400" />
            Working Hours & Buffer Controls
          </h2>

          <div className="space-y-3">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Work Day Start (HH:MM)
              </label>
              <input
                type="time"
                value={workStart}
                onChange={(e) => setWorkStart(e.target.value)}
                className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Work Day End (HH:MM)
              </label>
              <input
                type="time"
                value={workEnd}
                onChange={(e) => setWorkEnd(e.target.value)}
                className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>

            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-400 space-y-1">
              <p>
                <strong>Buffer Between Tasks:</strong> 5 minutes (enforced by OR-Tools)
              </p>
              <p>
                <strong>Timezone:</strong> UTC
              </p>
            </div>
          </div>
        </div>

        {/* Integration Status (Zero Secret Exposure) */}
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Cpu className="w-5 h-5 text-teal-400" />
            AI & Calendar Provider Status
          </h2>

          <div className="space-y-3 text-xs">
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between">
              <div>
                <span className="font-semibold text-slate-200">LLM Provider</span>
                <p className="text-slate-400 font-mono text-[11px]">
                  Model: {integrations?.llm_model || 'gemini-2.5-flash'}
                </p>
              </div>
              <span className="px-2.5 py-1 rounded font-bold uppercase bg-slate-800 text-slate-300 border border-slate-700">
                {integrations?.llm_provider || 'mock'}
              </span>
            </div>

            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between">
              <div>
                <span className="font-semibold text-slate-200">Calendar Integration</span>
                <p className="text-slate-400 font-mono text-[11px]">Simulated Local Verified Adapter</p>
              </div>
              <span className="px-2.5 py-1 rounded font-bold uppercase bg-slate-800 text-slate-300 border border-slate-700">
                {integrations?.calendar_provider || 'simulated'}
              </span>
            </div>

            <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300">
              <p className="font-semibold mb-1">Safety & Confidentiality Contract:</p>
              <p className="text-[11px] leading-relaxed text-amber-300/80">
                API credentials are never sent to the browser. The system defaults to deterministic mock
                responses and verified local calendar simulation when cloud API keys are omitted.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Utility Scoring Mathematical Weights */}
      <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Sliders className="w-5 h-5 text-teal-400" />
            Multi-Factor Mathematical Utility Weights
          </h2>
          <span
            className={`text-xs font-mono font-bold px-2 py-0.5 rounded ${
              Math.abs(weightSum - 1.0) < 0.05
                ? 'bg-emerald-500/20 text-emerald-300'
                : 'bg-rose-500/20 text-rose-300'
            }`}
          >
            Sum: {weightSum.toFixed(2)} / 1.00
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {Object.entries(weights).map(([k, v]) => (
            <div key={k} className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
              <div className="flex justify-between items-center text-xs">
                <span className="capitalize font-semibold text-slate-300">{k}</span>
                <span className="font-mono text-teal-400 font-bold">{v.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0.0"
                max="1.0"
                step="0.05"
                value={v}
                onChange={(e) => handleWeightChange(k as keyof typeof weights, parseFloat(e.target.value))}
                className="w-full accent-teal-400 bg-slate-800"
              />
            </div>
          ))}
        </div>

        <div className="flex justify-end pt-4">
          <button
            onClick={handleSaveSettings}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-teal-500 hover:bg-teal-400 text-slate-950 font-bold text-sm shadow-lg transition-all"
          >
            <Save className="w-4 h-4" />
            Save Preferences
          </button>
        </div>
      </div>
    </div>
  );
};
