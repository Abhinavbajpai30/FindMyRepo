import React, { useState, useEffect, useCallback } from 'react';
import Navbar from '@/components/Navbar';
import RepoCard, { RepoData } from '@/components/RepoCard';
import TetrisLoading from '@/components/ui/tetris-loader';

// API Types
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
  filters_applied?: Record<string, any>;
  error?: string;
}

// Filter parameters interface
interface FilterParams {
  language?: string;
  languages?: string;
  topics?: string;
  min_stars?: number;
  max_stars?: number;
  min_forks?: number;
  max_forks?: number;
  license?: string;
  has_issues?: boolean;
  has_wiki?: boolean;
  is_underrated?: boolean;
  is_gsoc?: boolean;
  is_hacktoberfest?: boolean;
  has_good_first_issues?: boolean;
  name_contains?: string;
  description_contains?: string;
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
const ALL_REPOS_ENDPOINT = import.meta.env.VITE_ALL_REPOS_ENDPOINT || '/allrepos';

// Fetch repositories from backend with filters
const fetchRepositories = async (
  page: number = 1,
  limit: number = 20,
  sortBy: string = 'stars',
  sortOrder: string = 'desc',
  filters: FilterParams = {}
): Promise<PaginatedResponse> => {
  const params = new URLSearchParams({
    page: page.toString(),
    limit: limit.toString(),
    sort_by: sortBy,
    sort_order: sortOrder
  });

  // Add filter parameters
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      if (Array.isArray(value)) {
        params.append(key, value.join(','));
      } else {
        params.append(key, value.toString());
      }
    }
  });
  
  const response = await fetch(`${API_BASE_URL}${ALL_REPOS_ENDPOINT}?${params}`);
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  return await response.json();
};

const AllRepos = () => {
  // State for repositories and pagination
  const [repositories, setRepositories] = useState<RepoData[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [totalItems, setTotalItems] = useState<number>(0);
  const [sortBy, setSortBy] = useState<string>('stars');
  const [sortOrder, setSortOrder] = useState<string>('desc');
  const [filtersApplied, setFiltersApplied] = useState<Record<string, any> | null>(null);
  
  // Backend filter states
  const [filters, setFilters] = useState<FilterParams>({});
  
  // UI filter states (mapped to backend filters)
  const [selectedLanguages, setSelectedLanguages] = useState<string[]>([]);
  const [selectedTopics, setSelectedTopics] = useState<string[]>([]);
  const [selectedPrograms, setSelectedPrograms] = useState<string[]>([]);
  const [minStars, setMinStars] = useState<number | undefined>();
  const [maxStars, setMaxStars] = useState<number | undefined>();
  const [minForks, setMinForks] = useState<number | undefined>();
  const [maxForks, setMaxForks] = useState<number | undefined>();
  const [hasIssues, setHasIssues] = useState<boolean | undefined>();
  const [hasWiki, setHasWiki] = useState<boolean | undefined>();
  const [nameContains, setNameContains] = useState<string>('');
  const [descriptionContains, setDescriptionContains] = useState<string>('');
  const [debouncedNameContains, setDebouncedNameContains] = useState<string>('');
  const [debouncedDescriptionContains, setDebouncedDescriptionContains] = useState<string>('');
  
  const itemsPerPage = 20;

  // Debounce text search inputs
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedNameContains(nameContains);
    }, 500);
    return () => clearTimeout(timer);
  }, [nameContains]);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedDescriptionContains(descriptionContains);
    }, 500);
    return () => clearTimeout(timer);
  }, [descriptionContains]);

  // Build backend filters from UI state
  const buildBackendFilters = (): FilterParams => {
    const backendFilters: FilterParams = {};
    
    // Languages filter
    if (selectedLanguages.length > 0) {
      backendFilters.languages = selectedLanguages.join(',');
    }
    
    // Topics filter
    if (selectedTopics.length > 0) {
      backendFilters.topics = selectedTopics.join(',');
    }
    
    // Program filters
    if (selectedPrograms.includes('Hacktoberfest')) {
      backendFilters.is_hacktoberfest = true;
    }
    if (selectedPrograms.includes('GSOC')) {
      backendFilters.is_gsoc = true;
    }
    
    // Star range filters
    if (minStars !== undefined) {
      backendFilters.min_stars = minStars;
    }
    if (maxStars !== undefined) {
      backendFilters.max_stars = maxStars;
    }
    
    // Fork range filters
    if (minForks !== undefined) {
      backendFilters.min_forks = minForks;
    }
    if (maxForks !== undefined) {
      backendFilters.max_forks = maxForks;
    }
    
    // Boolean filters
    if (hasIssues !== undefined) {
      backendFilters.has_issues = hasIssues;
    }
    if (hasWiki !== undefined) {
      backendFilters.has_wiki = hasWiki;
    }
    
    // Text search filters (using debounced values)
    if (debouncedNameContains.trim()) {
      backendFilters.name_contains = debouncedNameContains.trim();
    }
    if (debouncedDescriptionContains.trim()) {
      backendFilters.description_contains = debouncedDescriptionContains.trim();
    }
    
    return backendFilters;
  };

  // Update filters when UI state changes
  useEffect(() => {
    const newFilters = buildBackendFilters();
    setFilters(newFilters);
  }, [selectedLanguages, selectedTopics, selectedPrograms, minStars, maxStars, minForks, maxForks, hasIssues, hasWiki, debouncedNameContains, debouncedDescriptionContains]);

  // Filter handler functions
  const handleLanguageChange = (language: string, checked: boolean) => {
    if (checked) {
      setSelectedLanguages(prev => [...prev, language]);
    } else {
      setSelectedLanguages(prev => prev.filter(lang => lang !== language));
    }
  };

  const handleTopicChange = (topic: string, checked: boolean) => {
    if (checked) {
      setSelectedTopics(prev => [...prev, topic]);
    } else {
      setSelectedTopics(prev => prev.filter(t => t !== topic));
    }
  };

  const handleProgramChange = (program: string, checked: boolean) => {
    if (checked) {
      setSelectedPrograms(prev => [...prev, program]);
    } else {
      setSelectedPrograms(prev => prev.filter(prog => prog !== program));
    }
  };

  const clearFilters = () => {
    setSelectedLanguages([]);
    setSelectedTopics([]);
    setSelectedPrograms([]);
    setMinStars(undefined);
    setMaxStars(undefined);
    setMinForks(undefined);
    setMaxForks(undefined);
    setHasIssues(undefined);
    setHasWiki(undefined);
    setNameContains('');
    setDescriptionContains('');
  };

  // Fetch repositories from backend
  const loadRepositories = async (page: number, sort: string, order: string, currentFilters: FilterParams = {}) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetchRepositories(page, itemsPerPage, sort, order, currentFilters);
      
      if (response.success) {
        const transformedRepos = response.data.map(transformRepository);
        setRepositories(transformedRepos);
        setCurrentPage(response.pagination.current_page);
        setTotalPages(response.pagination.total_pages);
        setTotalItems(response.pagination.total_items);
        setFiltersApplied(response.filters_applied || null);
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
    loadRepositories(currentPage, sortBy, sortOrder, filters);
  }, [currentPage, sortBy, sortOrder, filters]);

  // Reset to first page when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [selectedLanguages, selectedTopics, selectedPrograms, minStars, maxStars, minForks, maxForks, hasIssues, hasWiki, debouncedNameContains, debouncedDescriptionContains]);

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
        <div className="text-center mb-8 mt-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">All Repositories</h1>
          <p className="text-muted-foreground">
            Explore all available repositories across different categories
          </p>
        </div>

        {/* Main Content - 30-70 Split */}
        <div className="grid grid-cols-1 lg:grid-cols-10 gap-8">
          {/* Filters Section - 30% */}
          <div className="lg:col-span-3">
            <div className="bg-card border border-border rounded-xl p-6 sticky top-20 max-h-[calc(100vh-6rem)] overflow-y-auto scrollbar-hide hover:scrollbar-show transition-all duration-300">
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-foreground">Filters</h3>
                  <button 
                    onClick={clearFilters}
                    className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                  >
                    Clear All
                  </button>
                </div>
                
                {/* Star Range Filter */}
                <div>
                  <h4 className="text-sm font-medium text-foreground mb-3">By Stars</h4>
                  <div className="space-y-3">
                    <div>
                      <label className="text-xs text-muted-foreground">Minimum Stars</label>
                      <input 
                        type="number" 
                        min="0"
                        className="w-full mt-1 px-3 py-2 text-sm bg-card border border-border rounded-lg focus:outline-none focus:ring-1 focus:ring-primary"
                        placeholder="e.g. 100"
                        value={minStars || ''}
                        onChange={(e) => {
                          const value = e.target.value;
                          setMinStars(value && !isNaN(parseInt(value)) && parseInt(value) >= 0 ? parseInt(value) : undefined);
                        }}
                      />
                    </div>
                    <div>
                      <label className="text-xs text-muted-foreground">Maximum Stars</label>
                      <input 
                        type="number" 
                        min="0"
                        className="w-full mt-1 px-3 py-2 text-sm bg-card border border-border rounded-lg focus:outline-none focus:ring-1 focus:ring-primary"
                        placeholder="e.g. 10000"
                        value={maxStars || ''}
                        onChange={(e) => {
                          const value = e.target.value;
                          setMaxStars(value && !isNaN(parseInt(value)) && parseInt(value) >= 0 ? parseInt(value) : undefined);
                        }}
                      />
                    </div>
                  </div>
                </div>

                {/* Programming Language Filter */}
                <div>
                  <h4 className="text-sm font-medium text-foreground mb-3">By Programming Language</h4>
                  <div className="grid grid-cols-2 gap-2">
                    {['Python', 'JavaScript', 'TypeScript', 'Java', 'C++', 'Go', 'Rust', 'HTML', 'CSS', 'PHP', 'Ruby', 'Swift', 'Kotlin', 'Dart', 'C#', 'Scala'].map((lang) => (
                      <label key={lang} className="flex items-center space-x-2 cursor-pointer p-2 rounded-lg hover:bg-secondary/50 transition-colors">
                        <input 
                          type="checkbox" 
                          className="rounded border-border" 
                          checked={selectedLanguages.includes(lang)}
                          onChange={(e) => handleLanguageChange(lang, e.target.checked)}
                        />
                        <span className="text-sm text-muted-foreground">{lang}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Programs Filter */}
                <div>
                  <h4 className="text-sm font-medium text-foreground mb-3">By Programs</h4>
                  <div className="space-y-2">
                    {['Hacktoberfest', 'GSOC'].map((program) => (
                      <label key={program} className="flex items-center space-x-2 cursor-pointer p-2 rounded-lg hover:bg-secondary/50 transition-colors">
                        <input 
                          type="checkbox" 
                          className="rounded border-border" 
                          checked={selectedPrograms.includes(program)}
                          onChange={(e) => handleProgramChange(program, e.target.checked)}
                        />
                        <span className="text-sm text-muted-foreground">{program}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Topics Filter */}
                <div>
                  <h4 className="text-sm font-medium text-foreground mb-3">By Topics</h4>
                  <div className="grid grid-cols-2 gap-2">
                    {['machine-learning', 'web-development', 'mobile-app', 'api', 'framework', 'library', 'tool', 'game', 'blockchain', 'ai', 'data-science', 'devops', 'security', 'testing', 'documentation'].map((topic) => (
                      <label key={topic} className="flex items-center space-x-2 cursor-pointer p-2 rounded-lg hover:bg-secondary/50 transition-colors">
                        <input 
                          type="checkbox" 
                          className="rounded border-border" 
                          checked={selectedTopics.includes(topic)}
                          onChange={(e) => handleTopicChange(topic, e.target.checked)}
                        />
                        <span className="text-sm text-muted-foreground">{topic}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Repository Features Filter */}
                <div>
                  <h4 className="text-sm font-medium text-foreground mb-3">By Repository Features</h4>
                  <div className="space-y-2">
                    <label className="flex items-center space-x-2 cursor-pointer p-2 rounded-lg hover:bg-secondary/50 transition-colors">
                      <input 
                        type="checkbox" 
                        className="rounded border-border" 
                        checked={hasIssues === true}
                        onChange={(e) => setHasIssues(e.target.checked ? true : undefined)}
                      />
                      <span className="text-sm text-muted-foreground">Has Issues Enabled</span>
                    </label>
                    <label className="flex items-center space-x-2 cursor-pointer p-2 rounded-lg hover:bg-secondary/50 transition-colors">
                      <input 
                        type="checkbox" 
                        className="rounded border-border" 
                        checked={hasWiki === true}
                        onChange={(e) => setHasWiki(e.target.checked ? true : undefined)}
                      />
                      <span className="text-sm text-muted-foreground">Has Wiki Enabled</span>
                    </label>
                  </div>
                </div>

                {/* Text Search Filters */}
                <div>
                  <h4 className="text-sm font-medium text-foreground mb-3">Text Search</h4>
                  <div className="space-y-3">
                    <div>
                      <label className="text-xs text-muted-foreground">Repository Name Contains</label>
                      <input 
                        type="text" 
                        className="w-full mt-1 px-3 py-2 text-sm bg-card border border-border rounded-lg focus:outline-none focus:ring-1 focus:ring-primary"
                        placeholder="e.g. react, vue, angular"
                        value={nameContains}
                        onChange={(e) => setNameContains(e.target.value)}
                      />
                    </div>
                    <div>
                      <label className="text-xs text-muted-foreground">Description Contains</label>
                      <input 
                        type="text" 
                        className="w-full mt-1 px-3 py-2 text-sm bg-card border border-border rounded-lg focus:outline-none focus:ring-1 focus:ring-primary"
                        placeholder="e.g. machine learning, web framework"
                        value={descriptionContains}
                        onChange={(e) => setDescriptionContains(e.target.value)}
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Repositories Section - 70% */}
          <div className="lg:col-span-7">
            {/* Controls */}
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-4">
                <h2 className="text-xl font-semibold text-foreground">
                  {loading ? 'Loading...' : `${totalItems} repositories found`}
                </h2>
                {filtersApplied && Object.keys(filtersApplied).length > 0 && (
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-muted-foreground">Filters applied:</span>
                    <div className="flex flex-wrap gap-1">
                      {Object.entries(filtersApplied).map(([key, value]) => (
                        <span 
                          key={key}
                          className="px-2 py-1 text-xs bg-primary/10 text-primary rounded-md border border-primary/20"
                        >
                          {key}: {Array.isArray(value) ? value.join(', ') : String(value)}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
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
              <div className="mt-3 flex gap-2">
                <button 
                  onClick={() => loadRepositories(currentPage, sortBy, sortOrder, filters)}
                  className="text-sm text-red-600 hover:text-red-800 underline"
                >
                  Try again
                </button>
                <button 
                  onClick={() => {
                    setError(null);
                    clearFilters();
                  }}
                  className="text-sm text-red-600 hover:text-red-800 underline"
                >
                  Clear filters and retry
                </button>
              </div>
            </div>
          )}

          {/* Loading State */}
          {loading && !error && (
            <div className="flex flex-col items-center justify-center h-[calc(100vh-200px)]">
              <TetrisLoading size="lg" />
              <p className="text-muted-foreground text-sm mt-4">Loading repositories...</p>
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
                      onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                      disabled={currentPage === 1 || loading}
                      className="px-3 py-2 text-sm font-medium text-muted-foreground bg-card border border-border rounded-lg hover:bg-secondary disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      Previous
                    </button>
                    
                    <div className="flex items-center gap-1">
                      {/* Always show first page */}
                      <button
                        onClick={() => setCurrentPage(1)}
                        className={`px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                          currentPage === 1
                            ? 'bg-primary text-primary-foreground'
                            : 'text-muted-foreground bg-card border border-border hover:bg-secondary'
                        }`}
                      >
                        1
                      </button>
                      
                      {/* Show ellipsis if current page is far from start */}
                      {currentPage > 4 && (
                        <>
                          <span className="px-2 text-muted-foreground">...</span>
                        </>
                      )}
                      
                      {/* Show pages around current page */}
                      {Array.from({ length: Math.min(5, totalPages - 2) }, (_, i) => {
                        let pageNum;
                        if (currentPage <= 3) {
                          pageNum = i + 2;
                        } else if (currentPage >= totalPages - 2) {
                          pageNum = totalPages - 4 + i;
                        } else {
                          pageNum = currentPage - 2 + i;
                        }
                        
                        // Don't show page 1 or last page here (already shown separately)
                        if (pageNum <= 1 || pageNum >= totalPages) return null;
                        
                        return (
                          <button
                            key={pageNum}
                            onClick={() => setCurrentPage(pageNum)}
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
                      
                      {/* Show ellipsis if current page is far from end */}
                      {currentPage < totalPages - 3 && totalPages > 6 && (
                        <>
                          <span className="px-2 text-muted-foreground">...</span>
                        </>
                      )}
                      
                      {/* Always show last page (if more than 1 page) */}
                      {totalPages > 1 && (
                        <button
                          onClick={() => setCurrentPage(totalPages)}
                          className={`px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                            currentPage === totalPages
                              ? 'bg-primary text-primary-foreground'
                              : 'text-muted-foreground bg-card border border-border hover:bg-secondary'
                          }`}
                        >
                          {totalPages}
                        </button>
                      )}
                    </div>
                    
                    <button
                      onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
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
                <p className="text-muted-foreground">No repositories found matching your filters.</p>
                <button 
                  onClick={clearFilters}
                  className="mt-2 text-sm text-primary hover:text-primary/80 underline"
                >
                  Clear filters to see all repositories
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AllRepos;