import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { Navbar } from '../Navbar';

describe('Navbar Component', () => {
  it('renders navigation links and logo', () => {
    const setActiveTab = vi.fn();
    render(
      <Navbar
        activeTab="dashboard"
        setActiveTab={setActiveTab}
        isMockLLM={true}
        demoMode={true}
      />
    );

    expect(screen.getByText('AURA')).toBeInTheDocument();
    expect(screen.getAllByText('Dashboard')[0]).toBeInTheDocument();
    expect(screen.getAllByText('AI Planner')[0]).toBeInTheDocument();
    expect(screen.getByText('Demo Mode')).toBeInTheDocument();
    expect(screen.getByText('Simulated AI')).toBeInTheDocument();
  });

  it('triggers setActiveTab callback when navigation item is clicked', () => {
    const setActiveTab = vi.fn();
    render(
      <Navbar
        activeTab="dashboard"
        setActiveTab={setActiveTab}
        isMockLLM={false}
        demoMode={false}
      />
    );

    const plannerBtns = screen.getAllByRole('button', { name: /AI Planner/i });
    expect(plannerBtns.length).toBeGreaterThan(0);
    fireEvent.click(plannerBtns[0]);
    expect(setActiveTab).toHaveBeenCalledWith('planner');
  });
});
