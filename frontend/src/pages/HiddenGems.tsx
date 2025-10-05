import React, { useState, useEffect } from 'react';
import Navbar from '@/components/Navbar';
import RepoCard, { RepoData } from '@/components/RepoCard';
import TetrisLoading from '@/components/ui/tetris-loader';

// API Types (same as AllRepos)
interface Repository {
  name: string;
  full_name: string;
  description: string;
  url: string;
  homepage: string;
  language: string;
  languages: string[];
  topics: string[];
  stars: number;
  forks: number;
  open_issues: number;
  license: string;
  has_issues: boolean;
  has_wiki: boolean;
  created_at: string;
  updated_at: string;
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

interface PaginatedResponse {
  success: boolean;
  data: Repository[];
  pagination: PaginationInfo;
  error?: string;
}

// Helper function to transform API repository to RepoData
const transformRepository = (repo: Repository): RepoData => {
  // Extract owner from full_name
  const owner = repo.full_name.split('/')[0] || '';
  
  // Determine charging status based on activity
  let charging: 'active' | 'medium' | 'inactive' = 'medium';
  const updatedAt = new Date(repo.updated_at);
  const now = new Date();
  const daysSinceUpdate = Math.floor((now.getTime() - updatedAt.getTime()) / (1000 * 60 * 60 * 24));
  
  if (daysSinceUpdate <= 7) {
    charging = 'active';
  } else if (daysSinceUpdate > 180) {
    charging = 'inactive';
  }
  
  // Format last activity
  const formatLastActivity = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInMs = now.getTime() - date.getTime();
    const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24));
    
    if (diffInDays === 0) {
      const diffInHours = Math.floor(diffInMs / (1000 * 60 * 60));
      if (diffInHours === 0) {
        const diffInMinutes = Math.floor(diffInMs / (1000 * 60));
        return `${diffInMinutes} minutes ago`;
      }
      return `${diffInHours} hours ago`;
    } else if (diffInDays === 1) {
      return '1 day ago';
    } else if (diffInDays < 7) {
      return `${diffInDays} days ago`;
    } else if (diffInDays < 30) {
      const weeks = Math.floor(diffInDays / 7);
      return `${weeks} week${weeks > 1 ? 's' : ''} ago`;
    } else if (diffInDays < 365) {
      const months = Math.floor(diffInDays / 30);
      return `${months} month${months > 1 ? 's' : ''} ago`;
    } else {
      const years = Math.floor(diffInDays / 365);
      return `${years} year${years > 1 ? 's' : ''} ago`;
    }
  };
  
  return {
    name: repo.name,
    description: repo.description || 'No description available',
    languages: repo.languages.length > 0 ? repo.languages : (repo.language ? [repo.language] : ['Other']),
    stars: repo.stars,
    lastActivity: formatLastActivity(repo.updated_at),
    issues: repo.open_issues,
    charging,
    url: repo.url,
    owner
  };
};

// API Base URL from environment variables
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const HIDDEN_GEMS_ENDPOINT = import.meta.env.VITE_HIDDEN_GEMS_ENDPOINT || '/hiddengem';

// Fetch hidden gems from backend
const fetchHiddenGems = async (
  page: number = 1,
  limit: number = 20,
  sortBy: string = 'stars',
  sortOrder: string = 'desc'
): Promise<PaginatedResponse> => {
  const params = new URLSearchParams({
    page: page.toString(),
    limit: limit.toString(),
    sort_by: sortBy,
    sort_order: sortOrder
  });
  
  const response = await fetch(`${API_BASE_URL}${HIDDEN_GEMS_ENDPOINT}?${params}`);
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  return await response.json();
};

const HiddenGems = () => {
  // State for repositories and pagination
  const [repositories, setRepositories] = useState<RepoData[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [totalItems, setTotalItems] = useState<number>(0);
  const [sortBy, setSortBy] = useState<string>('stars');
  const [sortOrder, setSortOrder] = useState<string>('desc');
  
  const itemsPerPage = 20;

  // Fetch repositories from backend
  const loadRepositories = async (page: number, sort: string, order: string) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetchHiddenGems(page, itemsPerPage, sort, order);
      
      if (response.success) {
        const transformedRepos = response.data.map(transformRepository);
        setRepositories(transformedRepos);
        setCurrentPage(response.pagination.current_page);
        setTotalPages(response.pagination.total_pages);
        setTotalItems(response.pagination.total_items);
      } else {
        setError(response.error || 'Failed to fetch repositories');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  // Load repositories on component mount and when parameters change
  useEffect(() => {
    loadRepositories(currentPage, sortBy, sortOrder);
  }, [currentPage, sortBy, sortOrder]);

  // Handle sort change
  const handleSortChange = (newSortBy: string) => {
    setSortBy(newSortBy);
    setCurrentPage(1); // Reset to first page when sorting changes
  };

  // Handle page change
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      
      <div className="container mx-auto max-w-7xl px-4 pb-12">
        {/* Header */}
        <div className="text-center mb-16 mt-12">
          <h1 className="text-4xl font-bold text-foreground mb-4">Hidden Gems</h1>
          <p className="text-muted-foreground text-lg">
            Discover quality projects with fewer than 1,000 stars
          </p>
        </div>

        {/* Main Content - Full Width */}
        <div className="max-w-6xl mx-auto">
          {/* Controls */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-4">
              <h2 className="text-xl font-semibold text-foreground">
                {loading ? 'Loading...' : `${totalItems} repositories found`}
              </h2>
            </div>
            
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">Sort by:</span>
              <select 
                value={`${sortBy}-${sortOrder}`}
                onChange={(e) => {
                  const [sort, order] = e.target.value.split('-');
                  setSortBy(sort);
                  setSortOrder(order);
                }}
                className="bg-card border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                aria-label="Sort repositories"
                disabled={loading}
              >
                <option value="stars-desc">Most Stars</option>
                <option value="stars-asc">Least Stars</option>
                <option value="updated_at-desc">Recently Updated</option>
                <option value="updated_at-asc">Oldest Updated</option>
                <option value="forks-desc">Most Forks</option>
                <option value="forks-asc">Least Forks</option>
                <option value="open_issues-desc">Most Issues</option>
                <option value="open_issues-asc">Least Issues</option>
                <option value="name-asc">Name A-Z</option>
                <option value="name-desc">Name Z-A</option>
                <option value="created_at-desc">Newest Created</option>
                <option value="created_at-asc">Oldest Created</option>
              </select>
            </div>
          </div>

          {/* Error State */}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg mb-6">
              <p className="font-medium">Error loading repositories</p>
              <p className="text-sm">{error}</p>
              <button 
                onClick={() => loadRepositories(currentPage, sortBy, sortOrder)}
                className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
              >
                Try again
              </button>
            </div>
          )}

          {/* Loading State */}
          {loading && !error && (
            <div className="flex flex-col items-center justify-center h-[calc(100vh-200px)]">
              <TetrisLoading size="lg" />
              <p className="text-muted-foreground text-sm mt-4">Loading hidden gems...</p>
            </div>
          )}

          {/* Repositories Grid */}
          {!loading && !error && (
            <>
              <div className="grid grid-cols-1 gap-6 mb-8">
                {repositories.map((repo, index) => (
                  <div 
                    key={repo.name} 
                    className={`transform transition-all duration-300 hover:scale-[1.02] hover:-translate-y-0.5 animate-slide-up cursor-pointer ${
                      index === 1 ? 'animate-delay-150ms' : '' 
                    } ${index === 2 ? 'animate-delay-300ms' : ''}`}
                  >
                    <RepoCard 
                      repo={repo} 
                      isHighlight={false}
                    />
                  </div>
                ))}
              </div>

              {/* Pagination Controls */}
              {totalPages > 1 && (
                <div className="flex items-center justify-center gap-2 mb-8">
                  <button
                    onClick={() => handlePageChange(currentPage - 1)}
                    disabled={currentPage === 1 || loading}
                    className="px-3 py-2 text-sm font-medium text-muted-foreground bg-card border border-border rounded-lg hover:bg-secondary disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    Previous
                  </button>
                  
                  <div className="flex items-center gap-1">
                    {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                      let pageNum;
                      if (totalPages <= 5) {
                        pageNum = i + 1;
                      } else if (currentPage <= 3) {
                        pageNum = i + 1;
                      } else if (currentPage >= totalPages - 2) {
                        pageNum = totalPages - 4 + i;
                      } else {
                        pageNum = currentPage - 2 + i;
                      }
                      
                      return (
                        <button
                          key={pageNum}
                          onClick={() => handlePageChange(pageNum)}
                          className={`px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                            currentPage === pageNum
                              ? 'bg-primary text-primary-foreground'
                              : 'text-muted-foreground bg-card border border-border hover:bg-secondary'
                          }`}
                        >
                          {pageNum}
                        </button>
                      );
                    })}
                  </div>
                  
                  <button
                    onClick={() => handlePageChange(currentPage + 1)}
                    disabled={currentPage === totalPages || loading}
                    className="px-3 py-2 text-sm font-medium text-muted-foreground bg-card border border-border rounded-lg hover:bg-secondary disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    Next
                  </button>
                </div>
              )}

              {/* Pagination Info */}
              <div className="text-center text-sm text-muted-foreground mb-4">
                Showing {((currentPage - 1) * itemsPerPage) + 1} to {Math.min(currentPage * itemsPerPage, totalItems)} of {totalItems} repositories
              </div>
            </>
          )}

          {/* Empty State */}
          {!loading && !error && repositories.length === 0 && (
            <div className="text-center py-12">
              <p className="text-muted-foreground">No repositories found.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default HiddenGems;