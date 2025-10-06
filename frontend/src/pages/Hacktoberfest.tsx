import { useState, useMemo } from 'react';
import Navbar from '@/components/Navbar';
import RepoCard, { RepoData } from '@/components/RepoCard';
import { GitPullRequest } from 'lucide-react';

const hacktoberfestRepos: RepoData[] = [
  {
    name: 'first-contributions',
    description: 'Help beginners make their first open source contribution',
    languages: ['JavaScript', 'HTML'],
    stars: 42000,
    lastActivity: '2 days ago',
    issues: 8,
    charging: 'active',
    owner: 'firstcontributions',
    url: 'https://github.com/firstcontributions/first-contributions',
  },
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
  {
    name: 'awesome-for-beginners',
    description: 'A list of awesome beginners-friendly projects',
    languages: ['Markdown'],
    stars: 38000,
    lastActivity: '1 week ago',
    issues: 73,
    charging: 'active',
    owner: 'MunGell',
    url: 'https://github.com/MunGell/awesome-for-beginners',
  },
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

const Hacktoberfest = () => {
  const [selectedLanguages, setSelectedLanguages] = useState<string[]>(['JavaScript', 'TypeScript', 'Python', 'Rust', 'Go']);
  const [starRange, setStarRange] = useState<string>('all');
  const [selectedActivities, setSelectedActivities] = useState<string[]>(['active', 'medium']);
  const [sortBy, setSortBy] = useState<string>('stars');

  // Filter and sort repositories
  const filteredRepos = useMemo(() => {
    let filtered = hacktoberfestRepos.filter(repo => {
      // Language filter
      const hasSelectedLanguage = repo.languages.some(lang => selectedLanguages.includes(lang));
      
      // Star range filter
      let matchesStarRange = true;
      if (starRange === 'less-1k') {
        matchesStarRange = repo.stars < 1000;
      } else if (starRange === '1k-10k') {
        matchesStarRange = repo.stars >= 1000 && repo.stars < 10000;
      } else if (starRange === '10k+') {
        matchesStarRange = repo.stars >= 10000;
      }
      
      // Activity filter
      const matchesActivity = selectedActivities.includes(repo.charging);
      
      return hasSelectedLanguage && matchesStarRange && matchesActivity;
    });

    // Sort repositories
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'stars':
          return b.stars - a.stars;
        case 'recent':
          const activityOrder = { active: 3, medium: 2, inactive: 1 };
          return activityOrder[b.charging] - activityOrder[a.charging];
        case 'issues':
          return b.issues - a.issues;
        case 'name':
          return a.name.localeCompare(b.name);
        default:
          return 0;
      }
    });

    return filtered;
  }, [selectedLanguages, starRange, selectedActivities, sortBy]);

  const handleLanguageChange = (language: string, checked: boolean) => {
    if (checked) {
      setSelectedLanguages(prev => [...prev, language]);
    } else {
      setSelectedLanguages(prev => prev.filter(lang => lang !== language));
    }
  };

  const handleActivityChange = (activity: string, checked: boolean) => {
    if (checked) {
      setSelectedActivities(prev => [...prev, activity]);
    } else {
      setSelectedActivities(prev => prev.filter(act => act !== activity));
    }
  };

  const clearFilters = () => {
    setSelectedLanguages(['JavaScript', 'TypeScript', 'Python', 'Rust', 'Go']);
    setStarRange('all');
    setSelectedActivities(['active', 'medium']);
    setSortBy('stars');
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      
      <div className="container mx-auto max-w-7xl px-4 pb-12">
        {/* Header */}
        <div className="text-center mb-16 mt-12">
          <h1 className="text-4xl font-bold text-foreground mb-4">Hacktoberfest</h1>
          <p className="text-muted-foreground text-lg">
            Repositories participating in Hacktoberfest
          </p>
        </div>

        {/* Main Content - 30-70 Split */}
        <div className="grid grid-cols-1 lg:grid-cols-10 gap-8">
          {/* Filters Section - 30% */}
          <div className="lg:col-span-3">
            <div className="bg-card border border-border rounded-xl p-6 sticky top-24">
              <h3 className="text-lg font-semibold text-foreground mb-4">Filters</h3>
              
              {/* Language Filter */}
              <div className="mb-6">
                <h4 className="text-sm font-medium text-foreground mb-3">Languages</h4>
                <div className="space-y-2">
                  {['JavaScript', 'HTML', 'Python', 'CSS', 'Markdown', 'TypeScript'].map((lang) => (
                    <label key={lang} className="flex items-center space-x-2 cursor-pointer">
                      <input type="checkbox" className="rounded border-border" defaultChecked />
                      <span className="text-sm text-muted-foreground">{lang}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Stars Filter */}
              <div className="mb-6">
                <h4 className="text-sm font-medium text-foreground mb-3">Star Count</h4>
                <div className="space-y-2">
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input type="radio" name="stars" className="border-border" defaultChecked />
                    <span className="text-sm text-muted-foreground">All</span>
                  </label>
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input type="radio" name="stars" className="border-border" />
                    <span className="text-sm text-muted-foreground">Less than 50K</span>
                  </label>
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input type="radio" name="stars" className="border-border" />
                    <span className="text-sm text-muted-foreground">50K - 200K</span>
                  </label>
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input type="radio" name="stars" className="border-border" />
                    <span className="text-sm text-muted-foreground">200K+</span>
                  </label>
                </div>
              </div>

              {/* Activity Filter */}
              <div className="mb-6">
                <h4 className="text-sm font-medium text-foreground mb-3">Activity</h4>
                <div className="space-y-2">
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input type="checkbox" className="rounded border-border" defaultChecked />
                    <span className="text-sm text-muted-foreground">Active (recent commits)</span>
                  </label>
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input type="checkbox" className="rounded border-border" />
                    <span className="text-sm text-muted-foreground">Medium activity</span>
                  </label>
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input type="checkbox" className="rounded border-border" />
                    <span className="text-sm text-muted-foreground">Low activity</span>
                  </label>
                </div>
              </div>

              {/* Clear Filters Button */}
              <button className="w-full px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors">
                Clear Filters
              </button>
            </div>
          </div>

          {/* Repositories Section - 70% */}
          <div className="lg:col-span-7">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-foreground">
                {filteredRepos.length} repositories found
              </h2>
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">Sort by:</span>
                <select 
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="bg-background border border-border rounded-lg px-3 py-1 text-sm"
                  aria-label="Sort repositories"
                >
                  <option value="stars">Most Stars</option>
                  <option value="recent">Recently Updated</option>
                  <option value="issues">Most Issues</option>
                  <option value="name">Name</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-6 mb-12 max-w-4xl mx-auto">
              {filteredRepos.map((repo, index) => (
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
          </div>
        </div>
      </div>
    </div>
  );
};

export default Hacktoberfest;
