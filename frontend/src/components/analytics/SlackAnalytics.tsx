'use client';

import React, { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api';
import { 
  ChatBubbleLeftRightIcon,
  UsersIcon,
  HashtagIcon,
  ExclamationCircleIcon,
  LockClosedIcon,
  GlobeAltIcon
} from '@heroicons/react/24/outline';

interface SlackAnalyticsProps {
  integrationId: number;
  integrationName: string;
}

export default function SlackAnalytics({ integrationId, integrationName }: SlackAnalyticsProps) {
  const [channels, setChannels] = useState<any[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadSlackData();
  }, [integrationId]);

  const loadSlackData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [channelsResponse, usersResponse] = await Promise.allSettled([
        apiClient.getSlackChannels(integrationId),
        apiClient.getSlackUsers(integrationId)
      ]);

      if (channelsResponse.status === 'fulfilled') {
        if (!channelsResponse.value.data) {
          throw new Error('Slack channels data not available');
        }
        setChannels(channelsResponse.value.data);
      } else {
        throw new Error('Failed to load Slack channels');
      }

      if (usersResponse.status === 'fulfilled') {
        if (!usersResponse.value.data) {
          throw new Error('Slack users data not available');
        }
        setUsers(usersResponse.value.data);
      } else {
        throw new Error('Failed to load Slack users');
      }
    } catch (err) {
      setError('Error loading Slack analytics');
      console.error('Slack analytics error:', err);
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

  const publicChannels = channels.filter(channel => !channel.is_private);
  const privateChannels = channels.filter(channel => channel.is_private);
  const activeUsers = users.filter(user => !user.deleted && !user.is_bot);
  const botUsers = users.filter(user => user.is_bot);

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-neutral-50 rounded-lg p-4 border border-neutral-200">
          <div className="flex items-center space-x-2">
            <HashtagIcon className="h-5 w-5 text-neutral-600" />
            <div>
              <p className="text-sm font-medium text-neutral-700">Total Channels</p>
              <p className="text-xl font-bold text-neutral-900">{channels.length}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-neutral-50 rounded-lg p-4 border border-neutral-200">
          <div className="flex items-center space-x-2">
            <UsersIcon className="h-5 w-5 text-neutral-600" />
            <div>
              <p className="text-sm font-medium text-neutral-700">Active Users</p>
              <p className="text-xl font-bold text-neutral-900">{activeUsers.length}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-neutral-50 rounded-lg p-4 border border-neutral-200">
          <div className="flex items-center space-x-2">
            <GlobeAltIcon className="h-5 w-5 text-neutral-600" />
            <div>
              <p className="text-sm font-medium text-neutral-700">Public Channels</p>
              <p className="text-xl font-bold text-neutral-900">{publicChannels.length}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-neutral-50 rounded-lg p-4 border border-neutral-200">
          <div className="flex items-center space-x-2">
            <LockClosedIcon className="h-5 w-5 text-neutral-600" />
            <div>
              <p className="text-sm font-medium text-neutral-700">Private Channels</p>
              <p className="text-xl font-bold text-neutral-900">{privateChannels.length}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Channel Overview */}
      <div>
        <h3 className="text-lg font-medium text-neutral-900 mb-4 flex items-center space-x-2">
          <HashtagIcon className="h-5 w-5" />
          <span>Recent Channels</span>
        </h3>
        {channels.length > 0 ? (
          <div className="space-y-3">
            {channels
              .filter(channel => !channel.is_archived)
              .slice(0, 8)
              .map((channel) => (
                <div key={channel.id} className="bg-white border border-neutral-200 rounded-lg p-4 hover:shadow-sm transition-shadow">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="flex-shrink-0">
                        {channel.is_private ? (
                          <LockClosedIcon className="h-4 w-4 text-neutral-500" />
                        ) : (
                          <HashtagIcon className="h-4 w-4 text-neutral-500" />
                        )}
                      </div>
                      <div className="flex-1">
                        <h4 className="font-medium text-neutral-900">
                          {channel.is_private ? '' : '#'}{channel.name}
                        </h4>
                        {channel.purpose?.value && (
                          <p className="text-sm text-neutral-600 mt-1">{channel.purpose.value}</p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center space-x-2 text-sm text-neutral-500">
                      <UsersIcon className="h-4 w-4" />
                      <span>{channel.num_members} members</span>
                    </div>
                  </div>
                </div>
              ))
            }
          </div>
        ) : (
          <p className="text-sm text-neutral-600">No channels found</p>
        )}
      </div>

      {/* User Overview */}
      <div>
        <h3 className="text-lg font-medium text-neutral-900 mb-4 flex items-center space-x-2">
          <UsersIcon className="h-5 w-5" />
          <span>User Statistics</span>
        </h3>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Active Users */}
          <div className="bg-white border border-neutral-200 rounded-lg p-4">
            <h4 className="font-medium text-neutral-900 mb-3">Active Users</h4>
            <div className="space-y-2">
              {activeUsers.slice(0, 5).map((user) => (
                <div key={user.id} className="flex items-center space-x-2">
                  <div className="w-2 h-2 rounded-full bg-green-500"></div>
                  <span className="text-sm text-neutral-700">{user.real_name || user.name}</span>
                  {user.is_admin && (
                    <span className="inline-flex px-1 py-0.5 rounded text-xs font-medium bg-primary-100 text-primary-800">
                      Admin
                    </span>
                  )}
                </div>
              ))}
              {activeUsers.length > 5 && (
                <p className="text-xs text-neutral-500 mt-2">
                  +{activeUsers.length - 5} more active users
                </p>
              )}
            </div>
          </div>

          {/* Bot Users */}
          <div className="bg-white border border-neutral-200 rounded-lg p-4">
            <h4 className="font-medium text-neutral-900 mb-3">Bots & Integrations</h4>
            <div className="space-y-2">
              {botUsers.slice(0, 5).map((bot) => (
                <div key={bot.id} className="flex items-center space-x-2">
                  <div className="w-2 h-2 rounded-full bg-blue-500"></div>
                  <span className="text-sm text-neutral-700">{bot.real_name || bot.name}</span>
                  <span className="inline-flex px-1 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                    Bot
                  </span>
                </div>
              ))}
              {botUsers.length > 5 && (
                <p className="text-xs text-neutral-500 mt-2">
                  +{botUsers.length - 5} more bots
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}