import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { StatusBadge } from '../StatusBadge';

describe('StatusBadge Component', () => {
  it('renders completed status badge correctly', () => {
    render(<StatusBadge status="COMPLETED" />);
    expect(screen.getByText('COMPLETED')).toBeInTheDocument();
  });

  it('renders proposed status badge correctly', () => {
    render(<StatusBadge status="PROPOSED" />);
    expect(screen.getByText('PROPOSED')).toBeInTheDocument();
  });

  it('renders failed status badge correctly', () => {
    render(<StatusBadge status="FAILED" />);
    expect(screen.getByText('FAILED')).toBeInTheDocument();
  });
});
