import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { DashboardPage } from './pages/DashboardPage';
import { PlannerPage } from './pages/PlannerPage';
import { CalendarPage } from './pages/CalendarPage';
import { TasksPage } from './pages/TasksPage';
import { HistoryPage } from './pages/HistoryPage';
import { SettingsPage } from './pages/SettingsPage';
import { EvaluationPage } from './pages/EvaluationPage';
import { api } from './services/api';
import { IntegrationStatus } from './types';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [integrations, setIntegrations] = useState<IntegrationStatus | null>(null);

  useEffect(() => {
    api.getIntegrations().then(setIntegrations).catch(console.error);
  }, []);

  return (
    <div className="min-h-screen bg-[#0b1120] text-slate-100 flex flex-col">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isMockLLM={integrations?.is_mock_llm ?? true}
        demoMode={integrations?.demo_mode ?? true}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'dashboard' && (
          <DashboardPage onNavigateToPlanner={() => setActiveTab('planner')} />
        )}
        {activeTab === 'planner' && <PlannerPage />}
        {activeTab === 'calendar' && <CalendarPage />}
        {activeTab === 'tasks' && <TasksPage />}
        {activeTab === 'history' && <HistoryPage />}
        {activeTab === 'evaluation' && <EvaluationPage />}
        {activeTab === 'settings' && <SettingsPage />}
      </main>

      <footer className="border-t border-slate-800/80 py-6 text-center text-xs text-slate-500">
        <p>AURA — Adaptive Utility-Aware AI Assistant for Real-Time Task Planning and Execution</p>
      </footer>
    </div>
  );
};
