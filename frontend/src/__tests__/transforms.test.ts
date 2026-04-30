import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { transformRepository, ApiRepository } from '../lib/transforms';

const makeRepo = (overrides: Partial<ApiRepository> = {}): ApiRepository => ({
  name: 'react',
  full_name: 'facebook/react',
  description: 'A JS library',
  url: 'https://github.com/facebook/react',
  language: 'JavaScript',
  languages: ['JavaScript', 'TypeScript'],
  topics: ['frontend', 'ui'],
  stars: 220000,
  forks: 45000,
  open_issues: 1200,
  updated_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(), // 3 days ago
  ...overrides,
});

describe('transformRepository', () => {
  it('maps full_name to owner', () => {
    const result = transformRepository(makeRepo());
    expect(result.owner).toBe('facebook');
  });

  it('uses description or falls back to placeholder', () => {
    expect(transformRepository(makeRepo({ description: null })).description).toBe('No description available');
    expect(transformRepository(makeRepo({ description: 'Real desc' })).description).toBe('Real desc');
  });

  it('uses languages array when non-empty', () => {
    const result = transformRepository(makeRepo({ languages: ['Python', 'Go'] }));
    expect(result.languages).toEqual(['Python', 'Go']);
  });

  it('falls back to language string when languages is empty', () => {
    const result = transformRepository(makeRepo({ languages: [], language: 'Python' }));
    expect(result.languages).toEqual(['Python']);
  });

  it('falls back to Other when both languages and language are absent', () => {
    const result = transformRepository(makeRepo({ languages: [], language: null }));
    expect(result.languages).toEqual(['Other']);
  });

  it('marks active for repos updated within 7 days', () => {
    const recent = new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString();
    expect(transformRepository(makeRepo({ updated_at: recent })).charging).toBe('active');
  });

  it('marks inactive for repos not updated in over 180 days', () => {
    const old = new Date(Date.now() - 200 * 24 * 60 * 60 * 1000).toISOString();
    expect(transformRepository(makeRepo({ updated_at: old })).charging).toBe('inactive');
  });

  it('marks medium for repos updated between 7 and 180 days ago', () => {
    const mid = new Date(Date.now() - 60 * 24 * 60 * 60 * 1000).toISOString();
    expect(transformRepository(makeRepo({ updated_at: mid })).charging).toBe('medium');
  });

  it('maps stars, open_issues, url correctly', () => {
    const result = transformRepository(makeRepo({ stars: 5000, open_issues: 42, url: 'https://github.com/a/b' }));
    expect(result.stars).toBe(5000);
    expect(result.issues).toBe(42);
    expect(result.url).toBe('https://github.com/a/b');
  });
});
