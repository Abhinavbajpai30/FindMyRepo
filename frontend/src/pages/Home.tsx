import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '@/components/Navbar';
import RepoCard, { RepoData } from '@/components/RepoCard';
import { usePreferences } from '@/contexts/PreferencesContext';
import { Button } from '@/components/ui/button';
import { ArrowRight, Sparkles, Loader2 } from 'lucide-react';
import ParticleHero from '@/components/ParticleHero';
import AccentLines from '@/components/AccentLines';
import { HeroPromptInput } from '@/components/HeroPromptInput';

// --- Types ---

// Matches the Python Pydantic model from your backend
interface BackendRepository {
  name: string;
  full_name: string;
  description: string;
  url: string;
  language: string;
  languages: string[];
  stars: number;
  open_issues: number;
  updated_at: string;
  topics: string[];
  owner?: string; // Assuming you might add this to backend, or we extract from full_name
}

// --- Utility Functions ---

const calculateRelativeTime = (dateString: string) => {
  const date = new Date(dateString);
  const now = new Date();
  const diffTime = Math.abs(now.getTime() - date.getTime());
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  
  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 30) return `${diffDays} days ago`;
  if (diffDays < 365) return `${Math.floor(diffDays / 30)} months ago`;
  return `${Math.floor(diffDays / 365)} years ago`;
};

const mapBackendToRepoData = (backendData: BackendRepository): RepoData => {
  // Extract owner from full_name (e.g., "facebook/react" -> "facebook")
  const owner = backendData.full_name.split('/')[0] || 'unknown';
  
  return {
    name: backendData.name,
    description: backendData.description || 'No description provided.',
    languages: backendData.languages.length > 0 ? backendData.languages : [backendData.language],
    stars: backendData.stars,
    lastActivity: calculateRelativeTime(backendData.updated_at),
    issues: backendData.open_issues,
    // Simple logic to determine "charging" status based on activity
    charging: backendData.open_issues > 20 ? 'active' : 'medium', 
    url: backendData.url,
    owner: owner,
  };
};

// --- Component ---

const Home = () => {
  const navigate = useNavigate();
  const { preferences, hasCompletedOnboarding } = usePreferences();
  
  const [query, setQuery] = useState('');
  
  // State for Repos
  const [repos, setRepos] = useState<RepoData[]>([]);
  const [visibleRepos, setVisibleRepos] = useState(5);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const USER_PREFERENCES_API = import.meta.env.VITE_USER_PREFERENCES_API || 'http://localhost:8000/userpreferences';
  const placeholders = [
    "Find beginner-friendly Python projects with good first issues",
    "Discover trending React repositories for contributors",
    "Search for machine learning projects with documentation needs",
    "Look for JavaScript libraries accepting new contributors",
  ];

  // 
  // 1. Check Local Storage -> 2. If Empty, Call API -> 3. Save to State & Local Storage
  useEffect(() => {
    const fetchRecommendations = async () => {
      if (!hasCompletedOnboarding || !preferences) return;

      // 1. Check Local Storage first
      const cachedData = localStorage.getItem('personalizedRepos');
      if (cachedData) {
        console.log("Loading repositories from local cache");
        setRepos(JSON.parse(cachedData));
        return;
      }

      // 2. If no cache, fetch from API
      setIsLoading(true);
      setError(null);

      try {
        // Replace with your actual backend URL

        console.log("Fetching repositories from backend based on preferences:", preferences);
        const response = await fetch(USER_PREFERENCES_API, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          // The context structure matches the backend Pydantic model
          body: JSON.stringify({
            primaryDomains: preferences.primaryDomains, // Mapping context naming to backend naming
            role: preferences.role, // Using skillLevel as role context
            expertise: preferences.expertise,
            preferredLanguages: preferences.preferredLanguages
          }),
        });

        if (!response.ok) {
          throw new Error('Failed to fetch recommendations');
        }

        const data = await response.json();
        
        if (data.success && Array.isArray(data.results)) {
          const formattedRepos = data.results.map(mapBackendToRepoData);
          
          // 3. Save to state and Cache
          setRepos(formattedRepos);
          localStorage.setItem('personalizedRepos', JSON.stringify(formattedRepos));
        } else {
          setError('No results found for your preferences.');
        }

      } catch (err) {
        console.error("Error fetching repos:", err);
        setError('Failed to load recommendations. Please try again later.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchRecommendations();
  }, [hasCompletedOnboarding, preferences]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value);
  };

  const handleSubmit = () => {
    if (query.trim()) {
      navigate('/search', { state: { query } });
    }
  };

  const handleLoadMore = () => {
    setVisibleRepos(prev => Math.min(prev + 5, repos.length));
  };

  return (
    <div className="min-h-screen relative overflow-hidden">
      <div className="fixed inset-0 bg-gradient-to-br from-background via-background to-primary/5"></div>
      <ParticleHero />
      <AccentLines />
      
      <div className="relative z-10">
        <Navbar />
        
        {/* Hero Section */}
        <section className="flex flex-col justify-start pt-56 pb-8">
          <div className="container-modern">
            <div className="max-w-5xl mx-auto">
              <div className="text-center mb-4 animate-fade-in">
                <h1 className="text-3xl sm:text-4xl lg:text-5xl text-white mb-2 leading-tight tracking-tight font-bold">
                  What do you want to discover?
                </h1>
                <p className="text-gray-400 text-lg font-normal">
                  Find repositories that match your passion and interests
                </p>
              </div>
              
              <div className="max-w-4xl mx-auto mb-0 animate-slide-up">
                <div className="relative group">
                  <div className="p-4">
                    <HeroPromptInput
                      value={query}
                      onValueChange={setQuery}
                      onSubmit={handleSubmit}
                      placeholders={placeholders}
                    />
                  </div>
                  <div className="absolute inset-0 bg-gradient-to-r from-primary/8 via-primary/3 to-primary/8 rounded-3xl blur-2xl -z-10 opacity-0 group-hover:opacity-100 transition-opacity duration-700"></div>
                </div>
              </div>

              {!hasCompletedOnboarding && (
                <div className="text-center animate-slide-up">
                  <Button
                    onClick={() => navigate('/onboarding')}
                    className="h-12 px-8 bg-gradient-to-r from-primary to-primary/80 hover:from-primary/90 hover:to-primary/70 text-primary-foreground border-0 rounded-2xl font-medium text-base transition-all duration-300 shadow-lg hover:shadow-primary/25 hover:scale-105 code-text"
                  >
                    <Sparkles className="h-5 w-5 mr-2" />
                    Get Personalized Recommendations
                    <ArrowRight className="h-5 w-5 ml-2 group-hover:translate-x-1 transition-transform" />
                  </Button>
                </div>
              )}
            </div>
          </div>
        </section>

        {/* Featured Section */}
        <section className="pb-16 sm:pb-20 lg:pb-24 relative rounded-t-[64px] border-t border-border/50 mx-6 mt-48" style={{ backgroundColor: '#080D0F', paddingTop: '80px' }}>
          <div className="container-modern relative z-10">
            <div className="text-center mb-16">
              <h2 className="text-3xl sm:text-4xl font-bold text-foreground mb-6 code-text">
                {hasCompletedOnboarding ? 'Personalized For You' : 'Trending Repositories'}
              </h2>
              <p className="text-muted-foreground text-lg leading-relaxed code-text">
                {hasCompletedOnboarding 
                  ? 'AI-curated repositories based on your preferences'
                  : 'Discover repositories tailored to your interests and skill level'}
              </p>
            </div>

            {/* Loading State */}
            {isLoading && (
               <div className="flex flex-col items-center justify-center py-20">
                 <Loader2 className="h-10 w-10 text-primary animate-spin mb-4" />
                 <p className="text-muted-foreground">Curating your feed...</p>
               </div>
            )}

            {/* Error State */}
            {!isLoading && error && (
              <div className="text-center py-10">
                <p className="text-red-400 mb-4">{error}</p>
                <Button onClick={() => window.location.reload()} variant="outline">
                  Try Again
                </Button>
              </div>
            )}

            {/* Empty State (No preferences) */}
            {!isLoading && !error && repos.length === 0 && (
              <div className="text-center py-10">
                 <p className="text-muted-foreground mb-4">Complete onboarding to see personalized results.</p>
                 <Button onClick={() => navigate('/onboarding')}>Start Onboarding</Button>
              </div>
            )}

            {/* Results Grid */}
            {!isLoading && repos.length > 0 && (
              <>
                <div className="grid grid-cols-1 gap-6 mb-12 max-w-4xl mx-auto">
                  {repos.slice(0, visibleRepos).map((repo, index) => (
                    <div 
                      key={repo.name} 
                      className={`transform transition-all duration-300 hover:scale-[1.02] hover:-translate-y-0.5 animate-slide-up cursor-pointer`}
                      style={{ animationDelay: `${index * 100}ms` }}
                    >
                      <RepoCard 
                        repo={repo} 
                        isHighlight={false}
                      />
                    </div>
                  ))}
                </div>

                {visibleRepos < repos.length && (
                  <div className="text-center">
                    <Button 
                      onClick={handleLoadMore}
                      variant="outline" 
                      className="btn-secondary group relative overflow-hidden"
                    >
                      <div className="absolute inset-0 bg-gradient-to-r from-primary/5 to-primary/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                      <span className="relative flex items-center">
                        Load More ({repos.length - visibleRepos} remaining)
                        <ArrowRight className="h-4 w-4 ml-2 group-hover:translate-x-1 transition-transform" />
                      </span>
                    </Button>
                  </div>
                )}
              </>
            )}
          </div>
        </section>
      </div>
    </div>
  );
};

export default Home;