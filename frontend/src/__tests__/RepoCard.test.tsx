import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import RepoCard, { RepoData } from '../components/RepoCard';
import { BookmarksProvider } from '../contexts/BookmarksContext';

const makeRepo = (overrides: Partial<RepoData> = {}): RepoData => ({
  name: 'react',
  description: 'A JS library for building UIs',
  languages: ['JavaScript', 'TypeScript'],
  stars: 220000,
  lastActivity: '2025-04-01T08:00:00Z',
  issues: 1200,
  charging: 'active',
  url: 'https://github.com/facebook/react',
  owner: 'facebook',
  ...overrides,
});

const renderCard = (repo: RepoData) =>
  render(
    <BookmarksProvider>
      <RepoCard repo={repo} />
    </BookmarksProvider>
  );

describe('RepoCard', () => {
  beforeEach(() => {
    vi.stubGlobal('open', vi.fn());
  });

  it('renders repo name derived from url', () => {
    renderCard(makeRepo());
    expect(screen.getByText('facebook/react')).toBeInTheDocument();
  });

  it('renders description', () => {
    renderCard(makeRepo());
    expect(screen.getByText('A JS library for building UIs')).toBeInTheDocument();
  });

  it('renders star count', () => {
    renderCard(makeRepo({ stars: 5000 }));
    expect(screen.getByText('5,000 stars')).toBeInTheDocument();
  });

  it('renders language badges', () => {
    renderCard(makeRepo({ languages: ['Python', 'Go'] }));
    expect(screen.getByText('Python')).toBeInTheDocument();
    expect(screen.getByText('Go')).toBeInTheDocument();
  });

  it('shows +N badge when more than 3 languages', () => {
    renderCard(makeRepo({ languages: ['Python', 'Go', 'Rust', 'TypeScript'] }));
    expect(screen.getByText('+1')).toBeInTheDocument();
  });

  it('opens GitHub URL on card click', () => {
    renderCard(makeRepo());
    fireEvent.click(screen.getByRole('article'));
    expect(window.open).toHaveBeenCalledWith('https://github.com/facebook/react', '_blank');
  });

  it('clicking bookmark button saves repo', () => {
    renderCard(makeRepo());
    const btn = screen.getByTitle('Save repo');
    fireEvent.click(btn);
    expect(screen.getByTitle('Remove bookmark')).toBeInTheDocument();
  });

  it('clicking bookmark again removes repo', () => {
    renderCard(makeRepo());
    const btn = screen.getByTitle('Save repo');
    fireEvent.click(btn);
    fireEvent.click(screen.getByTitle('Remove bookmark'));
    expect(screen.getByTitle('Save repo')).toBeInTheDocument();
  });

  it('card click does not propagate when bookmark is clicked', () => {
    renderCard(makeRepo());
    fireEvent.click(screen.getByTitle('Save repo'));
    expect(window.open).not.toHaveBeenCalled();
  });
});
