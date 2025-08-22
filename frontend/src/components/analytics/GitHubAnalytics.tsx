'use client';

import React, { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api';
import { 
  FolderIcon, 
  CodeBracketIcon,
  ExclamationCircleIcon,
  ChartBarIcon,
  EyeIcon,
  StarIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';

interface GitHubAnalyticsProps {
  integrationId: number;
  integrationName: string;
}

export default function GitHubAnalytics({ integrationId, integrationName }: GitHubAnalyticsProps) {
  const [repositories, setRepositories] = useState<any[]>([]);
  const [recentPRs, setRecentPRs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadGitHubData();
  }, [integrationId]);

  const loadGitHubData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [reposResponse, issuesResponse] = await Promise.allSettled([
        apiClient.getGitHubRepositories(integrationId),
        apiClient.getGitHubIssues(integrationId)
      ]);

      if (reposResponse.status === 'fulfilled') {
        if (!reposResponse.value.data) {
          throw new Error('GitHub repositories data not available');
        }
        setRepositories(reposResponse.value.data.slice(0, 10));
        
        // Get recent PRs from issues data (GitHub API returns PRs as issues)
        if (issuesResponse.status === 'fulfilled') {
          if (!issuesResponse.value.data) {
            throw new Error('GitHub issues data not available');
          }
          const prs = issuesResponse.value.data.filter((issue: any) => issue.pull_request).slice(0, 5);
          setRecentPRs(prs);
        } else {
          throw new Error('Failed to load GitHub issues');
        }
      } else {
        throw new Error('Failed to load GitHub repositories');
      }
    } catch (err) {
      setError('Error loading GitHub analytics');
      console.error('GitHub analytics error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="animate-pulse">
          <div className="h-4 bg-neutral-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-2">
            <div className="h-8 bg-neutral-200 rounded"></div>
            <div className="h-8 bg-neutral-200 rounded"></div>
            <div className="h-8 bg-neutral-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <ExclamationCircleIcon className="mx-auto h-8 w-8 text-neutral-400 mb-2" />
        <p className="text-sm text-neutral-600">{error}</p>
      </div>
    );
  }

  const totalStars = repositories.reduce((sum, repo) => sum + repo.stargazers_count, 0);
  const totalForks = repositories.reduce((sum, repo) => sum + repo.forks_count, 0);

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-neutral-50 rounded-lg p-4 border border-neutral-200">
          <div className="flex items-center space-x-2">
            <FolderIcon className="h-5 w-5 text-neutral-600" />
            <div>
              <p className="text-sm font-medium text-neutral-700">Repositories</p>
              <p className="text-xl font-bold text-neutral-900">{repositories.length}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-neutral-50 rounded-lg p-4 border border-neutral-200">
          <div className="flex items-center space-x-2">
            <ArrowPathIcon className="h-5 w-5 text-neutral-600" />
            <div>
              <p className="text-sm font-medium text-neutral-700">Recent PRs</p>
              <p className="text-xl font-bold text-neutral-900">{recentPRs.length}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-neutral-50 rounded-lg p-4 border border-neutral-200">
          <div className="flex items-center space-x-2">
            <StarIcon className="h-5 w-5 text-neutral-600" />
            <div>
              <p className="text-sm font-medium text-neutral-700">Total Stars</p>
              <p className="text-xl font-bold text-neutral-900">{totalStars.toLocaleString()}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-neutral-50 rounded-lg p-4 border border-neutral-200">
          <div className="flex items-center space-x-2">
            <CodeBracketIcon className="h-5 w-5 text-neutral-600" />
            <div>
              <p className="text-sm font-medium text-neutral-700">Total Forks</p>
              <p className="text-xl font-bold text-neutral-900">{totalForks.toLocaleString()}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Pull Requests */}
      <div>
        <h3 className="text-lg font-medium text-neutral-900 mb-4 flex items-center space-x-2">
          <ArrowPathIcon className="h-5 w-5" />
          <span>Recent Pull Requests</span>
        </h3>
        {recentPRs.length > 0 ? (
          <div className="space-y-3">
            {recentPRs.map((pr) => (
              <div key={pr.id} className="bg-white border border-neutral-200 rounded-lg p-4 hover:shadow-sm transition-shadow">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h4 className="font-medium text-neutral-900 mb-1">{pr.title}</h4>
                    <div className="flex items-center space-x-4 text-sm text-neutral-600">
                      <span>#{pr.number}</span>
                      <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${
                        pr.state === 'open' ? 'bg-green-100 text-green-800' : 'bg-neutral-100 text-neutral-800'
                      }`}>
                        {pr.state}
                      </span>
                      <span>{new Date(pr.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2 text-sm text-neutral-500">
                    <span>{pr.user?.login}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-neutral-600">No recent pull requests found</p>
        )}
      </div>

      {/* Top Repositories */}
      <div>
        <h3 className="text-lg font-medium text-neutral-900 mb-4 flex items-center space-x-2">
          <ChartBarIcon className="h-5 w-5" />
          <span>Top Repositories</span>
        </h3>
        {repositories.length > 0 ? (
          <div className="space-y-3">
            {repositories
              .sort((a, b) => b.stargazers_count - a.stargazers_count)
              .slice(0, 5)
              .map((repo) => (
                <div key={repo.id} className="bg-white border border-neutral-200 rounded-lg p-4 hover:shadow-sm transition-shadow">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <h4 className="font-medium text-neutral-900 mb-1">{repo.name}</h4>
                      {repo.description && (
                        <p className="text-sm text-neutral-600 mb-2">{repo.description}</p>
                      )}
                      <div className="flex items-center space-x-4 text-sm text-neutral-500">
                        {repo.language && (
                          <span className="flex items-center space-x-1">
                            <div className="w-2 h-2 rounded-full bg-neutral-400"></div>
                            <span>{repo.language}</span>
                          </span>
                        )}
                        <span className="flex items-center space-x-1">
                          <StarIcon className="h-3 w-3" />
                          <span>{repo.stargazers_count}</span>
                        </span>
                        <span className="flex items-center space-x-1">
                          <CodeBracketIcon className="h-3 w-3" />
                          <span>{repo.forks_count}</span>
                        </span>
                        {repo.visibility && (
                          <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${
                            repo.visibility === 'public' ? 'bg-green-100 text-green-800' : 'bg-neutral-100 text-neutral-800'
                          }`}>
                            {repo.visibility}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))
            }
          </div>
        ) : (
          <p className="text-sm text-neutral-600">No repositories found</p>
        )}
      </div>
    </div>
  );
}