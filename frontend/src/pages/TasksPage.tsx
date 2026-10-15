import React, { useEffect, useState } from 'react';
import {
  CheckSquare,
  Plus,
  Search,
  Filter,
  Trash2,
  CheckCircle,
  Clock,
  AlertCircle,
  Tag,
} from 'lucide-react';
import { api } from '../services/api';
import { Task, TaskStatus } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { format, parseISO } from 'date-fns';

export const TasksPage: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [search, setSearch] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);

  // Form State
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [duration, setDuration] = useState(30);
  const [priority, setPriority] = useState(3);
  const [mandatory, setMandatory] = useState(false);
  const [deadline, setDeadline] = useState('');

  useEffect(() => {
    loadTasks();
  }, []);

  async function loadTasks() {
    try {
      setLoading(true);
      const data = await api.listTasks();
      setTasks(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateTask(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim()) return;

    try {
      let deadlineIso: string | undefined = undefined;
      if (deadline) {
        deadlineIso = new Date(deadline).toISOString();
      }

      await api.createTask({
        title,
        description,
        estimated_duration_minutes: duration,
        priority,
        mandatory,
        deadline: deadlineIso,
      });

      setIsModalOpen(false);
      setTitle('');
      setDescription('');
      setDuration(30);
      setPriority(3);
      setMandatory(false);
      setDeadline('');
      loadTasks();
    } catch (err: any) {
      alert(err.message || 'Failed to create task');
    }
  }

  async function handleToggleStatus(task: Task) {
    const newStatus: TaskStatus = task.status === 'COMPLETED' ? 'PENDING' : 'COMPLETED';
    try {
      await api.updateTask(task.id, { status: newStatus });
      loadTasks();
    } catch (err: any) {
      alert(err.message || 'Failed to update task');
    }
  }

  async function handleDeleteTask(id: string) {
    if (!confirm('Are you sure you want to delete this task?')) return;
    try {
      await api.deleteTask(id);
      loadTasks();
    } catch (err: any) {
      alert(err.message || 'Failed to delete task');
    }
  }

  const filteredTasks = tasks.filter((t) => {
    const matchesSearch =
      t.title.toLowerCase().includes(search.toLowerCase()) ||
      (t.description && t.description.toLowerCase().includes(search.toLowerCase()));
    const matchesFilter = filterStatus === 'ALL' || t.status === filterStatus;
    return matchesSearch && matchesFilter;
  });

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-white flex items-center gap-3">
            <CheckSquare className="w-8 h-8 text-teal-400" />
            Task Portfolio & Dependency Management
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Create, inspect, and prioritize tasks with deterministic utility scoring and deadline tracking.
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-teal-500 hover:bg-teal-400 text-slate-950 font-bold text-sm shadow-lg transition-all"
        >
          <Plus className="w-4 h-4" />
          Create Task
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 flex flex-col sm:flex-row items-center gap-4">
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search tasks by title or description..."
            className="w-full pl-10 pr-4 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Filter className="w-4 h-4 text-slate-500" />
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
          >
            <option value="ALL">All Statuses</option>
            <option value="PENDING">Pending</option>
            <option value="SCHEDULED">Scheduled</option>
            <option value="COMPLETED">Completed</option>
            <option value="FAILED">Failed</option>
          </select>
        </div>
      </div>

      {/* Task List */}
      <div className="space-y-3">
        {loading ? (
          <div className="py-12 text-center text-slate-500 text-sm">Loading tasks...</div>
        ) : filteredTasks.length === 0 ? (
          <div className="py-12 text-center text-slate-500 text-sm p-6 rounded-2xl bg-slate-900 border border-slate-800">
            No tasks found matching your filter criteria.
          </div>
        ) : (
          filteredTasks.map((t) => (
            <div
              key={t.id}
              className={`p-4 rounded-xl border transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${
                t.status === 'COMPLETED'
                  ? 'bg-slate-900/40 border-slate-800/60 opacity-60'
                  : 'bg-slate-900 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex items-start gap-3.5">
                <button
                  onClick={() => handleToggleStatus(t)}
                  className={`mt-0.5 w-5 h-5 rounded-md border flex items-center justify-center transition-all ${
                    t.status === 'COMPLETED'
                      ? 'bg-emerald-500 border-emerald-500 text-slate-950'
                      : 'border-slate-600 hover:border-teal-400 text-transparent'
                  }`}
                >
                  <CheckCircle className="w-3.5 h-3.5 stroke-[3]" />
                </button>

                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <h3
                      className={`text-sm font-semibold ${
                        t.status === 'COMPLETED' ? 'line-through text-slate-400' : 'text-white'
                      }`}
                    >
                      {t.title}
                    </h3>
                    {t.mandatory && (
                      <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-300">
                        Mandatory
                      </span>
                    )}
                    <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                      P{t.priority}
                    </span>
                  </div>

                  {t.description && <p className="text-xs text-slate-400 mt-1">{t.description}</p>}

                  <div className="flex flex-wrap items-center gap-4 mt-2 text-xs text-slate-400">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5 text-slate-500" />
                      {t.estimated_duration_minutes} min
                    </span>
                    {t.deadline && (
                      <span className="text-amber-400 flex items-center gap-1">
                        <AlertCircle className="w-3.5 h-3.5" />
                        Due: {format(parseISO(t.deadline), 'MMM d, HH:mm')}
                      </span>
                    )}
                    <span className="text-teal-400">
                      Utility Score: {t.utility_score.toFixed(2)}
                    </span>
                    {t.dependencies.length > 0 && (
                      <span className="text-purple-400 flex items-center gap-1">
                        <Tag className="w-3.5 h-3.5" />
                        Blocks on: {t.dependencies.length} task(s)
                      </span>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between sm:justify-end gap-3 shrink-0">
                <StatusBadge status={t.status} />
                <button
                  onClick={() => handleDeleteTask(t.id)}
                  className="p-1.5 text-slate-500 hover:text-rose-400 rounded-lg hover:bg-slate-800 transition-all"
                  title="Delete Task"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Create Task Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
          <form
            onSubmit={handleCreateTask}
            className="max-w-md w-full bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4 shadow-2xl"
          >
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <Plus className="w-5 h-5 text-teal-400" />
              Create Actionable Task
            </h3>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Title *</label>
              <input
                type="text"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Write System Benchmark Report"
                className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Description</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Specific instructions or acceptance criteria"
                rows={2}
                className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Duration (minutes)</label>
                <input
                  type="number"
                  min={5}
                  max={480}
                  value={duration}
                  onChange={(e) => setDuration(Number(e.target.value))}
                  className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Priority (1 to 5)</label>
                <select
                  value={priority}
                  onChange={(e) => setPriority(Number(e.target.value))}
                  className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                >
                  <option value={1}>1 - Low</option>
                  <option value={2}>2 - Medium-Low</option>
                  <option value={3}>3 - Medium</option>
                  <option value={4}>4 - High</option>
                  <option value={5}>5 - Critical / Urgent</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Deadline (optional)</label>
              <input
                type="datetime-local"
                value={deadline}
                onChange={(e) => setDeadline(e.target.value)}
                className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>

            <div className="flex items-center gap-2 pt-1">
              <input
                type="checkbox"
                id="mandatoryCheck"
                checked={mandatory}
                onChange={(e) => setMandatory(e.target.checked)}
                className="w-4 h-4 rounded text-teal-500 focus:ring-teal-400 bg-slate-950 border-slate-800"
              />
              <label htmlFor="mandatoryCheck" className="text-xs text-slate-300">
                Mark as Mandatory (Hard constraint requirement)
              </label>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setIsModalOpen(false)}
                className="px-4 py-2 rounded-xl text-slate-400 hover:text-white text-sm"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 rounded-xl bg-teal-500 hover:bg-teal-400 text-slate-950 font-bold text-sm transition-all"
              >
                Save Task
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
