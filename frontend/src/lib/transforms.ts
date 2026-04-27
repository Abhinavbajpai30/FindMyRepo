import { RepoData } from '@/components/RepoCard';

export interface ApiRepository {
  name: string;
  full_name: string;
  description: string | null;
  url: string;
  language: string | null;
  languages: string[];
  topics: string[];
  stars: number;
  forks: number;
  open_issues: number;
  updated_at: string | null;
}

export interface ApiRepositoryDetail extends ApiRepository {
  readme: string | null;
}

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

export const transformRepository = (repo: ApiRepository): RepoData => {
  const owner = repo.full_name.split('/')[0] || '';
  const updatedAt = new Date(repo.updated_at || '');
  const now = new Date();
  const daysSinceUpdate = Math.floor((now.getTime() - updatedAt.getTime()) / (1000 * 60 * 60 * 24));

  let charging: 'active' | 'medium' | 'inactive' = 'medium';
  if (daysSinceUpdate <= 7) {
    charging = 'active';
  } else if (daysSinceUpdate > 180) {
    charging = 'inactive';
  }

  return {
    name: repo.name,
    description: repo.description || 'No description available',
    languages: repo.languages.length > 0 ? repo.languages : (repo.language ? [repo.language] : ['Other']),
    stars: repo.stars,
    lastActivity: formatLastActivity(repo.updated_at || ''),
    issues: repo.open_issues,
    charging,
    url: repo.url,
    owner,
  };
};
