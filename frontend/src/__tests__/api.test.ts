import { describe, it, expect, vi, beforeEach } from 'vitest';
import { searchRepos, getAllRepos, getHiddenGems, getRepo } from '../lib/api';

const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

function ok(body: unknown) {
  return Promise.resolve({
    ok: true,
    status: 200,
    json: () => Promise.resolve(body),
  } as Response);
}

function fail(status: number) {
  return Promise.resolve({ ok: false, status, json: () => Promise.resolve({}) } as Response);
}

beforeEach(() => {
  mockFetch.mockReset();
});

describe('searchRepos', () => {
  it('POSTs to /search with correct body and returns results', async () => {
    const repos = [{ name: 'pytorch' }];
    mockFetch.mockResolvedValueOnce(ok({ success: true, results: repos }));

    const result = await searchRepos('deep learning');

    expect(mockFetch).toHaveBeenCalledOnce();
    const [url, opts] = mockFetch.mock.calls[0];
    expect(url).toContain('/search');
    expect(opts.method).toBe('POST');
    expect(JSON.parse(opts.body)).toMatchObject({ query: 'deep learning' });
    expect(result).toEqual(repos);
  });

  it('throws on non-200', async () => {
    mockFetch.mockResolvedValueOnce(fail(503));
    await expect(searchRepos('python')).rejects.toThrow('503');
  });

  it('returns empty array when results is missing', async () => {
    mockFetch.mockResolvedValueOnce(ok({ success: true }));
    const result = await searchRepos('python');
    expect(result).toEqual([]);
  });
});

describe('getAllRepos', () => {
  it('GETs /allrepos with correct query params', async () => {
    mockFetch.mockResolvedValueOnce(ok({ success: true, data: [], pagination: {} }));
    await getAllRepos({ page: 2, sort_by: 'stars', sort_order: 'desc' });

    const url = mockFetch.mock.calls[0][0] as string;
    expect(url).toContain('/allrepos');
    expect(url).toContain('page=2');
    expect(url).toContain('sort_by=stars');
    expect(url).toContain('sort_order=desc');
  });

  it('throws on non-200', async () => {
    mockFetch.mockResolvedValueOnce(fail(400));
    await expect(getAllRepos()).rejects.toThrow('400');
  });
});

describe('getHiddenGems', () => {
  it('GETs /hiddengem', async () => {
    mockFetch.mockResolvedValueOnce(ok({ success: true, data: [], pagination: {} }));
    await getHiddenGems({ page: 1 });

    const url = mockFetch.mock.calls[0][0] as string;
    expect(url).toContain('/hiddengem');
    expect(url).toContain('page=1');
  });
});

describe('getRepo', () => {
  it('GETs /repo/{owner}/{name}', async () => {
    const repo = { name: 'react', full_name: 'facebook/react' };
    mockFetch.mockResolvedValueOnce(ok(repo));

    const result = await getRepo('facebook', 'react');
    const url = mockFetch.mock.calls[0][0] as string;
    expect(url).toContain('/repo/facebook/react');
    expect(result).toMatchObject({ name: 'react' });
  });

  it('throws "Repository not found" on 404', async () => {
    mockFetch.mockResolvedValueOnce(fail(404));
    await expect(getRepo('nobody', 'nothing')).rejects.toThrow('Repository not found');
  });

  it('throws generic error on other non-200', async () => {
    mockFetch.mockResolvedValueOnce(fail(500));
    await expect(getRepo('a', 'b')).rejects.toThrow('500');
  });
});
