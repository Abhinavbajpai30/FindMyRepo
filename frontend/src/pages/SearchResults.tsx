import { useLocation, useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import Navbar from '@/components/Navbar';
import RepoCard, { RepoData } from '@/components/RepoCard';
import { ArrowLeft, Search } from 'lucide-react';
import TetrisLoading from '@/components/ui/tetris-loader';

// API Configuration from environment variables
const SEARCH_API_URL = import.meta.env.VITE_SEARCH_API_URL || 'http://localhost:8000/search';

// Combined repository data from all pages for search
const allRepositories: RepoData[] = [
  // From Home page
  {
    name: 'first-contributions',
    description: 'Help beginners make their first open source contribution. This repository is perfect for newcomers to open source.',
    languages: ['JavaScript', 'HTML', 'CSS'],
    stars: 42000,
    lastActivity: '2 days ago',
    issues: 12,
    charging: 'active',
    url: 'https://github.com/firstcontributions/first-contributions',
    owner: 'firstcontributions',
  },
  {
    name: 'awesome-for-beginners',
    description: 'A list of awesome beginners-friendly projects. Curated list of projects that welcome new contributors.',
    languages: ['Markdown', 'JavaScript'],
    stars: 38000,
    lastActivity: '2 months ago',
    issues: 73,
    charging: 'medium',
    url: 'https://github.com/MunGell/awesome-for-beginners',
    owner: 'MunGell',
  },
  {
    name: 'scikit-learn',
    description: 'Machine learning in Python. Simple and efficient tools for predictive data analysis.',
    languages: ['Python', 'Cython', 'C++'],
    stars: 59000,
    lastActivity: '1 day ago',
    issues: 89,
    charging: 'active',
    url: 'https://github.com/scikit-learn/scikit-learn',
    owner: 'scikit-learn',
  },
  {
    name: 'react',
    description: 'A declarative, efficient, and flexible JavaScript library for building user interfaces.',
    languages: ['JavaScript', 'TypeScript', 'HTML'],
    stars: 220000,
    lastActivity: '3 hours ago',
    issues: 1247,
    charging: 'active',
    url: 'https://github.com/facebook/react',
    owner: 'facebook',
  },
  {
    name: 'tensorflow',
    description: 'An Open Source Machine Learning Framework for Everyone.',
    languages: ['Python', 'C++', 'JavaScript'],
    stars: 180000,
    lastActivity: '5 hours ago',
    issues: 892,
    charging: 'active',
    url: 'https://github.com/tensorflow/tensorflow',
    owner: 'tensorflow',
  },
  {
    name: 'vue',
    description: 'This is the repo for Vue 3. Vue 3 is the latest version of Vue.js.',
    languages: ['TypeScript', 'JavaScript', 'CSS'],
    stars: 41000,
    lastActivity: '1 day ago',
    issues: 456,
    charging: 'active',
    url: 'https://github.com/vuejs/vue',
    owner: 'vuejs',
  },
  {
    name: 'django',
    description: 'The Web framework for perfectionists with deadlines.',
    languages: ['Python', 'HTML', 'CSS'],
    stars: 75000,
    lastActivity: '2 days ago',
    issues: 234,
    charging: 'active',
    url: 'https://github.com/django/django',
    owner: 'django',
  },
  {
    name: 'express',
    description: 'Fast, unopinionated, minimalist web framework for node.',
    languages: ['JavaScript', 'HTML', 'CSS'],
    stars: 63000,
    lastActivity: '1 week ago',
    issues: 189,
    charging: 'medium',
    url: 'https://github.com/expressjs/express',
    owner: 'expressjs',
  },
  {
    name: 'pytorch',
    description: 'Tensors and Dynamic neural networks in Python with strong GPU acceleration.',
    languages: ['Python', 'C++', 'CUDA'],
    stars: 75000,
    lastActivity: '4 hours ago',
    issues: 567,
    charging: 'active',
    url: 'https://github.com/pytorch/pytorch',
    owner: 'pytorch',
  },
  {
    name: 'next.js',
    description: 'The React Framework for Production.',
    languages: ['TypeScript', 'JavaScript', 'CSS'],
    stars: 120000,
    lastActivity: '6 hours ago',
    issues: 789,
    charging: 'active',
    url: 'https://github.com/vercel/next.js',
    owner: 'vercel',
  },
  {
    name: 'fastapi',
    description: 'FastAPI framework, high performance, easy to learn, fast to code, ready for production.',
    languages: ['Python', 'JavaScript', 'HTML'],
    stars: 68000,
    lastActivity: '1 day ago',
    issues: 123,
    charging: 'active',
    url: 'https://github.com/tiangolo/fastapi',
    owner: 'tiangolo',
  },
  // From All Repos page
  {
    name: 'public-apis',
    description: 'A collective list of free APIs for use in software and web development',
    languages: ['Python'],
    stars: 280000,
    lastActivity: '1 day ago',
    issues: 156,
    charging: 'active',
    owner: 'public-apis',
    url: 'https://github.com/public-apis/public-apis',
  },
  {
    name: 'freeCodeCamp',
    description: "freeCodeCamp.org's open-source codebase and curriculum",
    languages: ['JavaScript', 'CSS'],
    stars: 390000,
    lastActivity: '5 hours ago',
    issues: 234,
    charging: 'active',
    url: 'https://github.com/freeCodeCamp/freeCodeCamp',
  },
  // From Hacktoberfest page
  {
    name: 'open-sauced',
    description: '🍕 This is a project to identify your next open source contribution',
    languages: ['TypeScript', 'JavaScript'],
    stars: 1200,
    lastActivity: '3 days ago',
    issues: 45,
    charging: 'active',
    owner: 'open-sauced',
    url: 'https://github.com/open-sauced/open-sauced',
  },
  {
    name: 'appwrite',
    description: 'Build like a team of hundreds_',
    languages: ['TypeScript', 'PHP', 'Dart'],
    stars: 38000,
    lastActivity: '1 day ago',
    issues: 234,
    charging: 'active',
    owner: 'appwrite',
    url: 'https://github.com/appwrite/appwrite',
  },
  {
    name: 'supabase',
    description: 'The open source Firebase alternative',
    languages: ['TypeScript', 'Go', 'Rust'],
    stars: 62000,
    lastActivity: '4 hours ago',
    issues: 567,
    charging: 'active',
    owner: 'supabase',
    url: 'https://github.com/supabase/supabase',
  },
  {
    name: 'novu',
    description: 'The open-source notification infrastructure',
    languages: ['TypeScript', 'JavaScript'],
    stars: 25000,
    lastActivity: '2 days ago',
    issues: 123,
    charging: 'active',
    owner: 'novuhq',
    url: 'https://github.com/novuhq/novu',
  },
  {
    name: 'n8n',
    description: 'Free and open source fair-code licensed workflow automation tool',
    languages: ['TypeScript', 'JavaScript'],
    stars: 42000,
    lastActivity: '6 hours ago',
    issues: 189,
    charging: 'active',
    owner: 'n8n-io',
    url: 'https://github.com/n8n-io/n8n',
  },
  {
    name: 'strapi',
    description: 'The open source headless CMS',
    languages: ['JavaScript', 'TypeScript'],
    stars: 60000,
    lastActivity: '1 day ago',
    issues: 456,
    charging: 'active',
    owner: 'strapijs',
    url: 'https://github.com/strapijs/strapi',
  },
  {
    name: 'directus',
    description: 'The Modern Data Stack 🐰 — Directus wraps any SQL database with a real-time GraphQL+REST API',
    languages: ['TypeScript', 'Vue', 'JavaScript'],
    stars: 25000,
    lastActivity: '3 days ago',
    issues: 234,
    charging: 'active',
    owner: 'directus',
    url: 'https://github.com/directus/directus',
  },
];

// Search function to find related repositories from external API
const searchRepositories = async (query: string): Promise<RepoData[]> => {
  if (!query.trim()) return [];
  
  try {
    // Make API call to external search service
    const response = await fetch(SEARCH_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query: query.trim() })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    
    // Transform API response to our RepoData format
    if (data.success && data.results && Array.isArray(data.results)) {
      return data.results.map((repo: any) => ({
        name: repo.name || 'Unknown',
        description: repo.description || 'No description available',
        languages: Array.isArray(repo.languages) && repo.languages.length > 0 ? repo.languages : 
                  repo.language ? [repo.language] : 
                  repo.topics && repo.topics.length > 0 ? [repo.topics[0]] : ['JavaScript'],
        stars: parseInt(repo.stars || '0') || 0,
        lastActivity: repo.updated_at || 'Unknown',
        issues: parseInt(repo.open_issues || '0') || 0,
        charging: repo.open_issues > 0 ? 'active' : 'medium',
        url: repo.url || '#',
        owner: repo.full_name ? repo.full_name.split('/')[0] : 'Unknown'
      }));
    }
    
    // Fallback to local search if API doesn't return expected format
    return fallbackLocalSearch(query);
    
  } catch (error) {
    console.error('Error fetching from external search API:', error);
    // Fallback to local search if API is unavailable
    return fallbackLocalSearch(query);
  }
};

// Fallback local search function
const fallbackLocalSearch = (query: string): RepoData[] => {
  const searchTerm = query.toLowerCase();
  
  return allRepositories.filter(repo => {
    // Search in name, description, languages, and owner
    const searchableText = [
      repo.name,
      repo.description,
      repo.owner,
      ...repo.languages
    ].join(' ').toLowerCase();
    
    return searchableText.includes(searchTerm);
  }).sort((a, b) => {
    // Sort by relevance (exact matches first, then by stars)
    const aExactMatch = a.name.toLowerCase().includes(searchTerm) || 
                       a.owner?.toLowerCase().includes(searchTerm);
    const bExactMatch = b.name.toLowerCase().includes(searchTerm) || 
                       b.owner?.toLowerCase().includes(searchTerm);
    
    if (aExactMatch && !bExactMatch) return -1;
    if (!aExactMatch && bExactMatch) return 1;
    
    return b.stars - a.stars; // Sort by stars as secondary criteria
  });
};

const SearchResults = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const query = location.state?.query || '';

  const [searchResults, setSearchResults] = useState<RepoData[]>([]);
  const [currentQuery, setCurrentQuery] = useState(query);
  const [isLoading, setIsLoading] = useState(false);


  useEffect(() => {
    if (query) {
      setIsLoading(true);
      
      // Search without artificial delay
      searchRepositories(query)
        .then((results) => {
          setSearchResults(results);
          setIsLoading(false);
        })
        .catch((error) => {
          console.error('Search error:', error);
          setSearchResults([]);
          setIsLoading(false);
        });
    } else {
      setSearchResults([]);
    }
  }, [query]);

  const handleSearch = async () => {
    if (currentQuery.trim()) {
      setIsLoading(true);
      
      try {
        // Search without artificial delay
        const results = await searchRepositories(currentQuery);
        setSearchResults(results);
        setIsLoading(false);
        
        // Update URL state
        navigate('/search', { state: { query: currentQuery } });
        
      } catch (error) {
        console.error('Search error:', error);
        setSearchResults([]);
        setIsLoading(false);
      }
    }
  };

  return (
    <div className="min-h-screen bg-background relative overflow-auto">
      <Navbar />
      
      {/* Background Effects */}
      <div className="fixed inset-0 -z-10">
        {/* Gradient Background */}
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-background to-primary/3"></div>
        
        {/* Floating Geometric Shapes */}
        <div className="absolute top-20 left-10 w-32 h-32 bg-primary/10 rounded-full blur-3xl animate-float"></div>
        <div className="absolute top-40 right-20 w-24 h-24 bg-primary/8 rounded-full blur-2xl animate-float" style={{ animationDelay: '2s' }}></div>
        <div className="absolute bottom-40 left-1/4 w-40 h-40 bg-primary/6 rounded-full blur-3xl animate-float" style={{ animationDelay: '4s' }}></div>
        
        {/* Accent Lines */}
        <div className="absolute top-32 left-0 w-32 h-px bg-gradient-to-r from-transparent via-primary/30 to-transparent animate-draw-x"></div>
        <div className="absolute top-48 right-0 w-px h-24 bg-gradient-to-b from-transparent via-primary/20 to-transparent animate-draw-y" style={{ animationDelay: '1s' }}></div>
        <div className="absolute bottom-32 left-1/3 w-24 h-px bg-gradient-to-r from-transparent via-primary/25 to-transparent animate-draw-x" style={{ animationDelay: '3s' }}></div>
      </div>
      
      <div className="container mx-auto max-w-7xl px-4 pb-12 relative z-10">
        {/* Go Back Button */}
        <div className="mb-6" style={{ marginTop: '80px' }}>
          <button
            onClick={() => navigate(-1)}
            className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors duration-200 group"
          >
            <ArrowLeft className="w-5 h-5 group-hover:-translate-x-1 transition-transform duration-200" />
            <span className="text-sm font-medium">Go Back</span>
          </button>
        </div>
        {/* Search Bar Section */}
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
            {/* Subtle glow effect */}
            <div className="absolute inset-0 bg-gradient-to-r from-primary/8 via-primary/3 to-primary/8 rounded-xl blur-2xl -z-10 opacity-0 group-hover:opacity-100 transition-opacity duration-700"></div>
          </div>
        </div>

        {/* Results Section */}
        <div className="max-w-4xl mx-auto">
          {isLoading ? (
            /* Loading State with Tetris Animation */
            <div className="flex flex-col items-center gap-6" style={{ marginTop: '120px' }}>
              <div className="flex justify-center">
                <TetrisLoading 
                  size="lg" 
                  speed="normal"
                  showLoadingText={false}
                />
              </div>
              <p className="text-foreground font-medium">Searching repositories...</p>
            </div>
          ) : searchResults.length > 0 ? (
            <>
              {/* Results Header */}
              <div className="text-center mb-8">
                <h2 className="text-2xl font-bold text-foreground mb-2">
                  Search Results
                </h2>
            <p className="text-muted-foreground">
                  Found {searchResults.length} repositories matching "{currentQuery}"
            </p>
          </div>
              
              <div className="grid grid-cols-1 gap-6 mb-12">
                {searchResults.map((repo, index) => (
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
            </>
          ) : query ? (
            <div className="text-center py-12">
              <div className="text-muted-foreground text-lg mb-4">
                No repositories found matching "{query}"
              </div>
              <p className="text-sm text-muted-foreground">
                Try searching for different keywords or check your spelling
              </p>
            </div>
          ) : (
            <div className="text-center py-12">
              <div className="text-muted-foreground text-lg mb-4">
                Start searching for repositories
              </div>
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