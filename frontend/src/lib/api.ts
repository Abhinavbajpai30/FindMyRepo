import { ApiRepository, ApiRepositoryDetail } from './transforms';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

interface SearchResponse {
  success: boolean;
  results: ApiRepository[];
}

interface PaginationInfo {
  current_page: number;
  per_page: number;
  total_items: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
  next_page: number | null;
  previous_page: number | null;
  sort_by: string;
  sort_order: string;
}

export interface PaginatedResponse {
  success: boolean;
  data: ApiRepository[];
  pagination: PaginationInfo;
  filters_applied?: Record<string, unknown>;
}

export interface RepoListParams {
  page?: number;
  limit?: number;
  sort_by?: string;
  sort_order?: string;
  languages?: string;
  topics?: string;
  min_stars?: number;
  max_stars?: number;
  min_forks?: number;
  max_forks?: number;
  has_issues?: boolean;
  has_wiki?: boolean;
  name_contains?: string;
  description_contains?: string;
  is_hacktoberfest?: boolean;
  is_gsoc?: boolean;
  is_underrated?: boolean;
}

export async function searchRepos(query: string): Promise<ApiRepository[]> {
  const res = await fetch(`${API_BASE_URL}/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query: query.trim() }),
  });
  if (!res.ok) throw new Error(`Search failed: ${res.status}`);
  const data: SearchResponse = await res.json();
  return data.results ?? [];
}

export async function getAllRepos(params: RepoListParams = {}): Promise<PaginatedResponse> {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') query.append(k, String(v));
  });
  const res = await fetch(`${API_BASE_URL}/allrepos?${query}`);
  if (!res.ok) throw new Error(`Failed to fetch repos: ${res.status}`);
  return res.json();
}

export async function getHiddenGems(params: Pick<RepoListParams, 'page' | 'limit' | 'sort_by' | 'sort_order'> = {}): Promise<PaginatedResponse> {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined) query.append(k, String(v));
  });
  const res = await fetch(`${API_BASE_URL}/hiddengem?${query}`);
  if (!res.ok) throw new Error(`Failed to fetch hidden gems: ${res.status}`);
  return res.json();
}

export async function getRepo(owner: string, name: string): Promise<ApiRepositoryDetail> {
  const res = await fetch(`${API_BASE_URL}/repo/${encodeURIComponent(owner)}/${encodeURIComponent(name)}`);
  if (res.status === 404) throw new Error('Repository not found');
  if (!res.ok) throw new Error(`Failed to fetch repo: ${res.status}`);
  return res.json();
}
