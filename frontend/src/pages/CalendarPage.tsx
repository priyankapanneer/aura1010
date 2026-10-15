import React, { useEffect, useState } from 'react';
import { Calendar as CalendarIcon, Clock, Plus, Trash2, ShieldAlert } from 'lucide-react';
import { api } from '../services/api';
import { CalendarEvent, Plan } from '../types';
import { format, parseISO, addHours, startOfDay, addDays } from 'date-fns';

export const CalendarPage: React.FC = () => {
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [latestPlan, setLatestPlan] = useState<Plan | null>(null);
  const [viewMode, setViewMode] = useState<'day' | 'week'>('day');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newStart, setNewStart] = useState('10:00');
  const [newEnd, setNewEnd] = useState('11:00');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadCalendarData();
  }, []);

  async function loadCalendarData() {
    try {
      setLoading(true);
      const [eList, pList] = await Promise.all([api.listEvents(), api.listPlans()]);
      setEvents(eList);
      if (pList.length > 0) setLatestPlan(pList[0]);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateEvent() {
    if (!newTitle.trim()) return;
    try {
      const now = new Date();
      const [sh, sm] = newStart.split(':').map(Number);
      const [eh, em] = newEnd.split(':').map(Number);

      const sDt = new Date(now.getFullYear(), now.getMonth(), now.getDate(), sh, sm);
      const eDt = new Date(now.getFullYear(), now.getMonth(), now.getDate(), eh, em);

      await api.createEvent({
        title: newTitle,
        start_time: sDt.toISOString(),
        end_time: eDt.toISOString(),
        is_fixed: true,
      });

      setIsModalOpen(false);
      setNewTitle('');
      loadCalendarData();
    } catch (err: any) {
      alert(err.message || 'Failed to create event');
    }
  }

  async function handleDeleteEvent(id: string) {
    if (!confirm('Delete this calendar event?')) return;
    try {
      await api.deleteEvent(id);
      loadCalendarData();
    } catch (err: any) {
      alert(err.message || 'Failed to delete event');
    }
  }

  // Hours array for day timetable: 08:00 to 19:00
  const hours = Array.from({ length: 12 }, (_, i) => i + 8);

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-white flex items-center gap-3">
            <CalendarIcon className="w-8 h-8 text-teal-400" />
            Interactive Calendar & Schedule Inspector
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Visual day and week schedules clearly differentiating fixed commitments from dynamically placed task slots.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="inline-flex rounded-xl bg-slate-900 border border-slate-800 p-1">
            <button
              onClick={() => setViewMode('day')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                viewMode === 'day' ? 'bg-teal-500 text-slate-950' : 'text-slate-400 hover:text-white'
              }`}
            >
              Day View
            </button>
            <button
              onClick={() => setViewMode('week')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                viewMode === 'week' ? 'bg-teal-500 text-slate-950' : 'text-slate-400 hover:text-white'
              }`}
            >
              Week View
            </button>
          </div>

          <button
            onClick={() => setIsModalOpen(true)}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-teal-500 hover:bg-teal-400 text-slate-950 font-bold text-xs shadow-md transition-all"
          >
            <Plus className="w-4 h-4" />
            Add Meeting
          </button>
        </div>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap items-center gap-6 p-4 rounded-xl bg-slate-900 border border-slate-800 text-xs">
        <div className="flex items-center gap-2">
          <span className="w-3.5 h-3.5 rounded bg-purple-500 border border-purple-400"></span>
          <span className="text-slate-300 font-medium">Fixed Calendar Meeting (Hard constraint)</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3.5 h-3.5 rounded bg-teal-500 border border-teal-400"></span>
          <span className="text-slate-300 font-medium">Auto-Scheduled Task Slot (AURA Optimized)</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3.5 h-3.5 rounded bg-slate-800 border border-slate-700"></span>
          <span className="text-slate-400 font-medium">Available Working Buffer</span>
        </div>
      </div>

      {/* Timetable View */}
      <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800">
        <div className="space-y-4">
          {hours.map((hour) => {
            const timeLabel = `${hour.toString().padStart(2, '0')}:00`;

            // Filter events in this hour
            const matchingEvents = events.filter((e) => {
              const h = new Date(e.start_time).getHours();
              return h === hour;
            });

            // Filter scheduled tasks in this hour
            const matchingTasks =
              latestPlan?.items?.filter((it) => {
                if (!it.is_scheduled || !it.scheduled_start) return false;
                const h = new Date(it.scheduled_start).getHours();
                return h === hour;
              }) || [];

            return (
              <div key={hour} className="flex gap-4 items-start group">
                {/* Time Label */}
                <div className="w-16 font-mono text-xs font-semibold text-slate-500 pt-2 shrink-0 text-right">
                  {timeLabel}
                </div>

                {/* Timeline Lane */}
                <div className="flex-1 min-h-[64px] rounded-xl bg-slate-950/60 border border-slate-800/80 p-2.5 space-y-2">
                  {matchingEvents.map((ev) => (
                    <div
                      key={ev.id}
                      className="p-3 rounded-lg bg-purple-950/30 border border-purple-500/40 flex items-center justify-between"
                    >
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-purple-500/20 text-purple-300 uppercase">
                            Fixed
                          </span>
                          <span className="text-sm font-semibold text-white">{ev.title}</span>
                        </div>
                        <p className="text-xs text-purple-300/80 mt-0.5">
                          {format(parseISO(ev.start_time), 'HH:mm')} - {format(parseISO(ev.end_time), 'HH:mm')}
                        </p>
                      </div>
                      <button
                        onClick={() => handleDeleteEvent(ev.id)}
                        className="text-slate-500 hover:text-rose-400 p-1"
                        title="Delete event"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}

                  {matchingTasks.map((it) => (
                    <div
                      key={it.id}
                      className="p-3 rounded-lg bg-teal-950/30 border border-teal-500/40 flex items-center justify-between"
                    >
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-teal-500/20 text-teal-300 uppercase">
                            Planned Task
                          </span>
                          <span className="text-sm font-semibold text-white">{it.task_title || it.task_id}</span>
                        </div>
                        <p className="text-xs text-teal-300/80 mt-0.5">
                          {format(parseISO(it.scheduled_start!), 'HH:mm')} -{' '}
                          {format(parseISO(it.scheduled_end!), 'HH:mm')} • Utility: {it.utility_score.toFixed(2)}
                        </p>
                      </div>
                    </div>
                  ))}

                  {matchingEvents.length === 0 && matchingTasks.length === 0 && (
                    <div className="text-xs text-slate-700 py-1 px-2 italic">Open time window</div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Add Event Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
          <div className="max-w-md w-full bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <Plus className="w-5 h-5 text-teal-400" />
              Add Fixed Calendar Event
            </h3>
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Title</label>
                <input
                  type="text"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="e.g. Executive Strategy Review"
                  className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Start Time (HH:MM)</label>
                  <input
                    type="time"
                    value={newStart}
                    onChange={(e) => setNewStart(e.target.value)}
                    className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">End Time (HH:MM)</label>
                  <input
                    type="time"
                    value={newEnd}
                    onChange={(e) => setNewEnd(e.target.value)}
                    className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setIsModalOpen(false)}
                className="px-4 py-2 rounded-xl text-slate-400 hover:text-white text-sm"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateEvent}
                className="px-4 py-2 rounded-xl bg-teal-500 hover:bg-teal-400 text-slate-950 font-bold text-sm transition-all"
              >
                Create Event
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
