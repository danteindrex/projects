'use client';

import React, { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api';
import { 
  FolderIcon,
  RectangleStackIcon,
  UserGroupIcon,
  ExclamationCircleIcon,
  CheckCircleIcon,
  ClockIcon,
  FlagIcon
} from '@heroicons/react/24/outline';

interface AsanaAnalyticsProps {
  integrationId: number;
  integrationName: string;
}

export default function AsanaAnalytics({ integrationId, integrationName }: AsanaAnalyticsProps) {
  const [projects, setProjects] = useState<any[]>([]);
  const [tasks, setTasks] = useState<any[]>([]);
  const [teams, setTeams] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadAsanaData();
  }, [integrationId]);

  const loadAsanaData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [projectsResponse, tasksResponse, teamsResponse] = await Promise.allSettled([
        apiClient.getAsanaProjects(integrationId),
        apiClient.getAsanaTasks(integrationId),
        apiClient.getAsanaTeams(integrationId)
      ]);

      if (projectsResponse.status === 'fulfilled') {
        if (!projectsResponse.value.data) {
          throw new Error('Asana projects data not available');
        }
        setProjects(projectsResponse.value.data);
      } else {
        throw new Error('Failed to load Asana projects');
      }

      if (tasksResponse.status === 'fulfilled') {
        if (!tasksResponse.value.data) {
          throw new Error('Asana tasks data not available');
        }
        setTasks(tasksResponse.value.data);
      } else {
        throw new Error('Failed to load Asana tasks');
      }

      if (teamsResponse.status === 'fulfilled') {
        if (!teamsResponse.value.data) {
          throw new Error('Asana teams data not available');
        }
        setTeams(teamsResponse.value.data);
      } else {
        throw new Error('Failed to load Asana teams');
      }
    } catch (err) {
      setError('Error loading Asana analytics');
      console.error('Asana analytics error:', err);
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

  const activeTasks = tasks.filter(task => !task.completed);
  const completedTasks = tasks.filter(task => task.completed);
  const overdueTasks = tasks.filter(task => task.due_on && new Date(task.due_on) < new Date() && !task.completed);
  const activeProjects = projects.filter(project => project.archived === false);

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-neutral-50 rounded-lg p-4 border border-neutral-200">
          <div className="flex items-center space-x-2">
            <FolderIcon className="h-5 w-5 text-neutral-600" />
            <div>
              <p className="text-sm font-medium text-neutral-700">Active Projects</p>
              <p className="text-xl font-bold text-neutral-900">{activeProjects.length}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-neutral-50 rounded-lg p-4 border border-neutral-200">
          <div className="flex items-center space-x-2">
            <ClockIcon className="h-5 w-5 text-neutral-600" />
            <div>
              <p className="text-sm font-medium text-neutral-700">Active Tasks</p>
              <p className="text-xl font-bold text-neutral-900">{activeTasks.length}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-neutral-50 rounded-lg p-4 border border-neutral-200">
          <div className="flex items-center space-x-2">
            <CheckCircleIcon className="h-5 w-5 text-neutral-600" />
            <div>
              <p className="text-sm font-medium text-neutral-700">Completed</p>
              <p className="text-xl font-bold text-neutral-900">{completedTasks.length}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-neutral-50 rounded-lg p-4 border border-neutral-200">
          <div className="flex items-center space-x-2">
            <FlagIcon className="h-5 w-5 text-neutral-600" />
            <div>
              <p className="text-sm font-medium text-neutral-700">Overdue</p>
              <p className="text-xl font-bold text-neutral-900">{overdueTasks.length}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Tasks */}
      <div>
        <h3 className="text-lg font-medium text-neutral-900 mb-4 flex items-center space-x-2">
          <RectangleStackIcon className="h-5 w-5" />
          <span>Recent Tasks</span>
        </h3>
        {tasks.length > 0 ? (
          <div className="space-y-3">
            {tasks
              .sort((a, b) => new Date(b.modified_at).getTime() - new Date(a.modified_at).getTime())
              .slice(0, 8)
              .map((task) => {
                const taskProject = projects.find(project => project.gid === task.projects?.[0]?.gid);
                return (
                  <div key={task.gid} className="bg-white border border-neutral-200 rounded-lg p-4 hover:shadow-sm transition-shadow">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${
                            task.completed ? 'bg-green-100 text-green-800' : 'bg-neutral-100 text-neutral-800'
                          }`}>
                            {task.completed ? 'Completed' : 'Active'}
                          </span>
                          {task.due_on && (
                            <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${
                              task.completed ? 'bg-green-100 text-green-800' :
                              new Date(task.due_on) < new Date() ? 'bg-red-100 text-red-800' :
                              'bg-yellow-100 text-yellow-800'
                            }`}>
                              Due: {new Date(task.due_on).toLocaleDateString()}
                            </span>
                          )}
                        </div>
                        <h4 className="font-medium text-neutral-900 mb-1">{task.name}</h4>
                        <div className="flex items-center space-x-4 text-sm text-neutral-600">
                          {taskProject && (
                            <span>Project: {taskProject.name}</span>
                          )}
                          {task.assignee && (
                            <span>Assigned to: {task.assignee.name}</span>
                          )}
                          <span>Updated: {new Date(task.modified_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })
            }
          </div>
        ) : (
          <p className="text-sm text-neutral-600">No tasks found</p>
        )}
      </div>

      {/* Active Projects */}
      <div>
        <h3 className="text-lg font-medium text-neutral-900 mb-4 flex items-center space-x-2">
          <FolderIcon className="h-5 w-5" />
          <span>Active Projects</span>
        </h3>
        {activeProjects.length > 0 ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {activeProjects.slice(0, 6).map((project) => {
              const projectTasks = tasks.filter(task => 
                task.projects && task.projects.some(p => p.gid === project.gid)
              );
              const projectActiveTasks = projectTasks.filter(task => !task.completed);
              const projectTeam = teams.find(team => team.gid === project.team?.gid);
              
              return (
                <div key={project.gid} className="bg-white border border-neutral-200 rounded-lg p-4 hover:shadow-sm transition-shadow">
                  <div className="flex items-start space-x-3">
                    <div className="w-6 h-6 bg-primary-100 rounded flex items-center justify-center">
                      <span className="text-xs font-bold text-primary-600">
                        {project.name?.slice(0, 2)}
                      </span>
                    </div>
                    <div className="flex-1">
                      <h4 className="font-medium text-neutral-900 mb-1">{project.name}</h4>
                      {project.notes && (
                        <p className="text-sm text-neutral-500 mb-2 truncate">{project.notes}</p>
                      )}
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-neutral-600">
                          {projectActiveTasks.length} active tasks
                        </span>
                        <span className="text-neutral-500">
                          {projectTasks.length} total
                        </span>
                      </div>
                      {projectTeam && (
                        <div className="mt-2">
                          <span className="text-xs text-neutral-500">Team: {projectTeam.name}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-sm text-neutral-600">No active projects found</p>
        )}
      </div>
    </div>
  );
}