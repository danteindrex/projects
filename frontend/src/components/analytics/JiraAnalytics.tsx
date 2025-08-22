'use client';

import React, { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api';
import { 
  RectangleStackIcon,
  BugAntIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ClockIcon,
  FolderIcon
} from '@heroicons/react/24/outline';

interface JiraAnalyticsProps {
  integrationId: number;
  integrationName: string;
}

export default function JiraAnalytics({ integrationId, integrationName }: JiraAnalyticsProps) {
  const [projects, setProjects] = useState<any[]>([]);
  const [issues, setIssues] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadJiraData();
  }, [integrationId]);

  const loadJiraData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [projectsResponse, issuesResponse] = await Promise.allSettled([
        apiClient.getJiraProjects(integrationId),
        apiClient.getJiraIssues(integrationId)
      ]);

      if (projectsResponse.status === 'fulfilled') {
        if (!projectsResponse.value.data) {
          throw new Error('Jira projects data not available');
        }
        setProjects(projectsResponse.value.data);
      } else {
        throw new Error('Failed to load Jira projects');
      }

      if (issuesResponse.status === 'fulfilled') {
        if (!issuesResponse.value.data?.issues) {
          throw new Error('Jira issues data not available');
        }
        setIssues(issuesResponse.value.data.issues);
      } else {
        throw new Error('Failed to load Jira issues');
      }
    } catch (err) {
      setError('Error loading Jira analytics');
      console.error('Jira analytics error:', err);
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

  const openIssues = issues.filter(issue => issue.fields?.status?.name !== 'Done' && issue.fields?.status?.name !== 'Closed');
  const closedIssues = issues.filter(issue => issue.fields?.status?.name === 'Done' || issue.fields?.status?.name === 'Closed');
  const bugs = issues.filter(issue => issue.fields?.issuetype?.name?.toLowerCase().includes('bug'));

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-neutral-50 rounded-lg p-4 border border-neutral-200">
          <div className="flex items-center space-x-2">
            <FolderIcon className="h-5 w-5 text-neutral-600" />
            <div>
              <p className="text-sm font-medium text-neutral-700">Projects</p>
              <p className="text-xl font-bold text-neutral-900">{projects.length}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-neutral-50 rounded-lg p-4 border border-neutral-200">
          <div className="flex items-center space-x-2">
            <ClockIcon className="h-5 w-5 text-neutral-600" />
            <div>
              <p className="text-sm font-medium text-neutral-700">Open Issues</p>
              <p className="text-xl font-bold text-neutral-900">{openIssues.length}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-neutral-50 rounded-lg p-4 border border-neutral-200">
          <div className="flex items-center space-x-2">
            <CheckCircleIcon className="h-5 w-5 text-neutral-600" />
            <div>
              <p className="text-sm font-medium text-neutral-700">Completed</p>
              <p className="text-xl font-bold text-neutral-900">{closedIssues.length}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-neutral-50 rounded-lg p-4 border border-neutral-200">
          <div className="flex items-center space-x-2">
            <BugAntIcon className="h-5 w-5 text-neutral-600" />
            <div>
              <p className="text-sm font-medium text-neutral-700">Bugs</p>
              <p className="text-xl font-bold text-neutral-900">{bugs.length}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Issues */}
      <div>
        <h3 className="text-lg font-medium text-neutral-900 mb-4 flex items-center space-x-2">
          <RectangleStackIcon className="h-5 w-5" />
          <span>Recent Issues</span>
        </h3>
        {issues.length > 0 ? (
          <div className="space-y-3">
            {issues
              .sort((a, b) => new Date(b.fields?.created).getTime() - new Date(a.fields?.created).getTime())
              .slice(0, 8)
              .map((issue) => (
                <div key={issue.id} className="bg-white border border-neutral-200 rounded-lg p-4 hover:shadow-sm transition-shadow">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <span className="text-sm font-mono text-neutral-500">{issue.key}</span>
                        <span className="inline-flex px-2 py-1 rounded-full text-xs font-medium bg-neutral-100 text-neutral-800">
                          {issue.fields?.status?.name}
                        </span>
                        {issue.fields?.issuetype?.name && (
                          <span className="inline-flex px-2 py-1 rounded-full text-xs font-medium bg-neutral-100 text-neutral-800">
                            {issue.fields.issuetype.name}
                          </span>
                        )}
                      </div>
                      <h4 className="font-medium text-neutral-900 mb-1">{issue.fields?.summary}</h4>
                      <div className="flex items-center space-x-4 text-sm text-neutral-600">
                        {issue.fields?.assignee && (
                          <span>Assigned to: {issue.fields.assignee.displayName}</span>
                        )}
                        {issue.fields?.priority && (
                          <span>Priority: {issue.fields.priority.name}</span>
                        )}
                        <span>{new Date(issue.fields?.created).toLocaleDateString()}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))
            }
          </div>
        ) : (
          <p className="text-sm text-neutral-600">No issues found</p>
        )}
      </div>

      {/* Projects Overview */}
      <div>
        <h3 className="text-lg font-medium text-neutral-900 mb-4 flex items-center space-x-2">
          <FolderIcon className="h-5 w-5" />
          <span>Projects</span>
        </h3>
        {projects.length > 0 ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {projects.slice(0, 6).map((project) => {
              const projectIssues = issues.filter(issue => issue.fields?.project?.key === project.key);
              const projectOpenIssues = projectIssues.filter(issue => 
                issue.fields?.status?.name !== 'Done' && issue.fields?.status?.name !== 'Closed'
              );
              
              return (
                <div key={project.id} className="bg-white border border-neutral-200 rounded-lg p-4 hover:shadow-sm transition-shadow">
                  <div className="flex items-start space-x-3">
                    {project.avatarUrls?.['24x24'] ? (
                      <img 
                        src={project.avatarUrls['24x24']} 
                        alt={project.name}
                        className="w-6 h-6 rounded"
                      />
                    ) : (
                      <div className="w-6 h-6 bg-primary-100 rounded flex items-center justify-center">
                        <span className="text-xs font-bold text-primary-600">
                          {project.key?.slice(0, 2)}
                        </span>
                      </div>
                    )}
                    <div className="flex-1">
                      <h4 className="font-medium text-neutral-900 mb-1">{project.name}</h4>
                      <p className="text-sm text-neutral-500 mb-2">{project.key}</p>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-neutral-600">
                          {projectOpenIssues.length} open issues
                        </span>
                        <span className="text-neutral-500">
                          {projectIssues.length} total
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-sm text-neutral-600">No projects found</p>
        )}
      </div>
    </div>
  );
}