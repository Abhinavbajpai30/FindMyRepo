import { useLocation, useNavigate, useSearchParams } from 'react-router-dom';
import { useState, useEffect, useRef, useCallback } from 'react';
import Navbar from '@/components/Navbar';
import RepoCard, { RepoData } from '@/components/RepoCard';
import { ArrowLeft, Search, Share2, Check } from 'lucide-react';
import TetrisLoading from '@/components/ui/tetris-loader';

const SEARCH_API_URL = import.meta.env.VITE_SEARCH_API_URL || 'http://localhost:8000/search';
const PAGE_SIZE = 20;

const searchRepositories = async (query: string): Promise<RepoData[]> => {
  const response = await fetch(SEARCH_API_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query: query.trim(), limit: 60 }),
  });

  if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

  const data = await response.json();

  if (data.success && Array.isArray(data.results)) {
    return data.results.map((repo: any) => ({
      name: repo.name || 'Unknown',
      description: repo.description || 'No description available',
      languages: Array.isArray(repo.languages) && repo.languages.length > 0
        ? repo.languages
        : repo.language ? [repo.language] : ['Other'],
      stars: parseInt(repo.stars || '0') || 0,
      lastActivity: repo.updated_at || 'Unknown',
      issues: parseInt(repo.open_issues || '0') || 0,
      charging: repo.open_issues > 0 ? 'active' : 'medium',
      url: repo.url || '#',
      owner: repo.full_name ? repo.full_name.split('/')[0] : 'Unknown',
    }));
  }

  return [];
};

const SearchResults = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const initialQuery = location.state?.query || searchParams.get('q') || '';

  const [allResults, setAllResults] = useState<RepoData[]>([]);
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE);
  const [currentQuery, setCurrentQuery] = useState(initialQuery);
  const [submittedQuery, setSubmittedQuery] = useState(initialQuery);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const sentinelRef = useRef<HTMLDivElement | null>(null);
  const observerRef = useRef<IntersectionObserver | null>(null);

  const runSearch = useCallback(async (q: string) => {
    setIsLoading(true);
    setError(null);
    setAllResults([]);
    setVisibleCount(PAGE_SIZE);
    try {
      const results = await searchRepositories(q);
      setAllResults(results);
    } catch (err) {
      setError('Search failed. Please check that the backend is running and try again.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Run search on initial load if there's a query
  useEffect(() => {
    if (initialQuery) {
      setSearchParams({ q: initialQuery }, { replace: true });
      runSearch(initialQuery);
    }
  }, []);

  // Set up IntersectionObserver to load more results on scroll
  useEffect(() => {
    if (observerRef.current) observerRef.current.disconnect();

    if (!sentinelRef.current || visibleCount >= allResults.length) return;

    observerRef.current = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          setVisibleCount(prev => Math.min(prev + PAGE_SIZE, allResults.length));
        }
      },
      { rootMargin: '200px' }
    );

    observerRef.current.observe(sentinelRef.current);
    return () => observerRef.current?.disconnect();
  }, [visibleCount, allResults.length]);

  const handleSearch = async () => {
    if (!currentQuery.trim()) return;
    setSubmittedQuery(currentQuery);
    setSearchParams({ q: currentQuery }, { replace: true });
    await runSearch(currentQuery);
  };

  const handleShare = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // clipboard unavailable
    }
  };

  const visibleResults = allResults.slice(0, visibleCount);
  const hasMore = visibleCount < allResults.length;

  const statusText = () => {
    if (allResults.length === 0) return null;
    if (hasMore) return `Showing ${visibleCount} of ${allResults.length} results for "${submittedQuery}"`;
    return `Showing all ${allResults.length} results for "${submittedQuery}"`;
  };

  return (
    <div className="min-h-screen bg-background relative overflow-auto">
      <Navbar />

      {/* Background Effects */}
      <div className="fixed inset-0 -z-10">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-background to-primary/3"></div>
        <div className="absolute top-20 left-10 w-32 h-32 bg-primary/10 rounded-full blur-3xl animate-float"></div>
        <div className="absolute top-40 right-20 w-24 h-24 bg-primary/8 rounded-full blur-2xl animate-float" style={{ animationDelay: '2s' }}></div>
        <div className="absolute bottom-40 left-1/4 w-40 h-40 bg-primary/6 rounded-full blur-3xl animate-float" style={{ animationDelay: '4s' }}></div>
        <div className="absolute top-32 left-0 w-32 h-px bg-gradient-to-r from-transparent via-primary/30 to-transparent animate-draw-x"></div>
        <div className="absolute top-48 right-0 w-px h-24 bg-gradient-to-b from-transparent via-primary/20 to-transparent animate-draw-y" style={{ animationDelay: '1s' }}></div>
        <div className="absolute bottom-32 left-1/3 w-24 h-px bg-gradient-to-r from-transparent via-primary/25 to-transparent animate-draw-x" style={{ animationDelay: '3s' }}></div>
      </div>

      <div className="container mx-auto max-w-7xl px-4 pb-12 relative z-10">
        {/* Go Back */}
        <div className="mb-6" style={{ marginTop: '80px' }}>
          <button
            onClick={() => navigate(-1)}
            className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors duration-200 group"
          >
            <ArrowLeft className="w-5 h-5 group-hover:-translate-x-1 transition-transform duration-200" />
            <span className="text-sm font-medium">Go Back</span>
          </button>
        </div>

        {/* Search Bar */}
        <div className="max-w-4xl mx-auto mt-8 mb-8">
          <div className="relative group">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-5 h-5 transition-colors group-focus-within:text-primary" />
              <input
                type="text"
                value={currentQuery}
                onChange={(e) => setCurrentQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="Search repositories..."
                className="w-full pl-10 pr-4 py-3 bg-card/60 backdrop-blur-md border border-border rounded-xl text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 hover:border-primary/30 transition-all duration-300 shadow-lg hover:shadow-xl"
              />
            </div>
            <div className="absolute inset-0 bg-gradient-to-r from-primary/8 via-primary/3 to-primary/8 rounded-xl blur-2xl -z-10 opacity-0 group-hover:opacity-100 transition-opacity duration-700"></div>
          </div>
        </div>

        {/* Results */}
        <div className="max-w-4xl mx-auto">
          {isLoading ? (
            <div className="flex flex-col items-center gap-6" style={{ marginTop: '120px' }}>
              <TetrisLoading size="lg" speed="normal" showLoadingText={false} />
              <p className="text-foreground font-medium">Searching repositories...</p>
            </div>
          ) : error ? (
            <div className="text-center py-12 space-y-3">
              <p className="text-muted-foreground text-lg">{error}</p>
              <button
                onClick={() => runSearch(submittedQuery)}
                className="text-sm text-primary hover:underline"
              >
                Try again
              </button>
            </div>
          ) : visibleResults.length > 0 ? (
            <>
              {/* Header */}
              <div className="text-center mb-8">
                <h2 className="text-2xl font-bold text-foreground mb-2">Search Results</h2>
                <p className="text-muted-foreground mb-4">{statusText()}</p>
                <button
                  onClick={handleShare}
                  className="inline-flex items-center gap-2 px-3 py-1.5 text-sm text-muted-foreground border border-border rounded-lg hover:bg-secondary transition-colors"
                >
                  {copied ? <Check className="w-4 h-4 text-green-500" /> : <Share2 className="w-4 h-4" />}
                  {copied ? 'Link copied!' : 'Share search'}
                </button>
              </div>

              <div className="grid grid-cols-1 gap-6 mb-8">
                {visibleResults.map((repo, index) => (
                  <div
                    key={`${repo.url}-${index}`}
                    className="transform transition-all duration-300 hover:scale-[1.02] hover:-translate-y-0.5 animate-slide-up"
                  >
                    <RepoCard repo={repo} isHighlight={false} />
                  </div>
                ))}
              </div>

              {/* Sentinel for infinite scroll */}
              {hasMore && (
                <div ref={sentinelRef} className="flex justify-center py-6">
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                    Loading more results...
                  </div>
                </div>
              )}

              {!hasMore && allResults.length > PAGE_SIZE && (
                <p className="text-center text-sm text-muted-foreground py-6">
                  All {allResults.length} results loaded
                </p>
              )}
            </>
          ) : submittedQuery && !isLoading ? (
            <div className="text-center py-12">
              <div className="text-muted-foreground text-lg mb-4">
                No repositories found matching "{submittedQuery}"
              </div>
              <p className="text-sm text-muted-foreground">
                Try searching with different keywords
              </p>
            </div>
          ) : (
            <div className="text-center py-12">
              <div className="text-muted-foreground text-lg mb-4">Start searching for repositories</div>
              <p className="text-sm text-muted-foreground">
                Enter a search term to find repositories that match your interests
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SearchResults;
