import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '@/components/Navbar';
import RepoCard, { RepoData } from '@/components/RepoCard';
import { usePreferences } from '@/contexts/PreferencesContext';
import { Button } from '@/components/ui/button';
import { ArrowRight, Sparkles, TrendingUp, Users } from 'lucide-react';
import ParticleHero from '@/components/ParticleHero';
import AccentLines from '@/components/AccentLines';
import { HeroPromptInput } from '@/components/HeroPromptInput';

// Mock recommended repos - in production, these would come from an API
const mockRecommendedRepos: RepoData[] = [
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
];

const Home = () => {
  const navigate = useNavigate();
  const { preferences, hasCompletedOnboarding } = usePreferences();
  const [query, setQuery] = useState('');
  const [visibleRepos, setVisibleRepos] = useState(5);

  const placeholders = [
    "Find beginner-friendly Python projects with good first issues",
    "Discover trending React repositories for contributors",
    "Search for machine learning projects with documentation needs",
    "Look for JavaScript libraries accepting new contributors",
    "Find open source projects with Hacktoberfest tags",
    "Discover web development repositories for beginners",
    "Search for AI/ML projects with active communities",
    "Find TypeScript projects with good documentation",
  ];

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value);
  };

  const handleSubmit = () => {
    if (query.trim()) {
      navigate('/search', { state: { query } });
    }
  };

  const handleLoadMore = () => {
    setVisibleRepos(prev => Math.min(prev + 5, mockRecommendedRepos.length));
  };

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Background Effects - Extended throughout entire page */}
      <div className="fixed inset-0 bg-gradient-to-br from-background via-background to-primary/5"></div>
      <ParticleHero />
      <AccentLines />
      
      <div className="relative z-10">
        <Navbar />
        
        {/* Hero Section */}
        <section className="flex flex-col justify-start pt-56 pb-8">
          <div className="container-modern">
            <div className="max-w-5xl mx-auto">
              {/* Main heading */}
              <div className="text-center mb-4 animate-fade-in">
                <h1 className="text-3xl sm:text-4xl lg:text-5xl text-white mb-2 leading-tight tracking-tight font-bold">
                  What do you want to discover?
                </h1>
                <p className="text-gray-400 text-lg font-normal">
                  Find repositories that match your passion and interests
                </p>
              </div>
              
              {/* Search Section */}
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
                  
                  {/* Subtle glow effect */}
                  <div className="absolute inset-0 bg-gradient-to-r from-primary/8 via-primary/3 to-primary/8 rounded-3xl blur-2xl -z-10 opacity-0 group-hover:opacity-100 transition-opacity duration-700"></div>
                </div>
              </div>

              {/* CTA Section */}
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
                Personalized Repositories
              </h2>
              <p className="text-muted-foreground text-lg leading-relaxed code-text">
                Discover repositories tailored to your interests and skill level
              </p>
            </div>

            <div className="grid grid-cols-1 gap-6 mb-12 max-w-4xl mx-auto">
              {mockRecommendedRepos.slice(0, visibleRepos).map((repo, index) => (
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

            {visibleRepos < mockRecommendedRepos.length && (
              <div className="text-center">
                <Button 
                  onClick={handleLoadMore}
                  variant="outline" 
                  className="btn-secondary group relative overflow-hidden"
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-primary/5 to-primary/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                  <span className="relative flex items-center">
                    Load More ({mockRecommendedRepos.length - visibleRepos} remaining)
                    <ArrowRight className="h-4 w-4 ml-2 group-hover:translate-x-1 transition-transform" />
                  </span>
                </Button>
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
};

export default Home;
