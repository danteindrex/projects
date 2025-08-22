'use client';

import React, { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api';
import { 
  TicketIcon,
  UserGroupIcon,
  ChatBubbleLeftRightIcon,
  ExclamationCircleIcon,
  CheckCircleIcon,
  ClockIcon,
  FaceSmileIcon
} from '@heroicons/react/24/outline';

interface ZendeskAnalyticsProps {
  integrationId: number;
  integrationName: string;
}

export default function ZendeskAnalytics({ integrationId, integrationName }: ZendeskAnalyticsProps) {
  const [tickets, setTickets] = useState<any[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  const [organizations, setOrganizations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadZendeskData();
  }, [integrationId]);

  const loadZendeskData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [ticketsResponse, usersResponse, organizationsResponse] = await Promise.allSettled([
        apiClient.getZendeskTickets(integrationId),
        apiClient.getZendeskUsers(integrationId),
        apiClient.getZendeskOrganizations(integrationId)
      ]);

      if (ticketsResponse.status === 'fulfilled') {
        if (!ticketsResponse.value.data) {
          throw new Error('Zendesk tickets data not available');
        }
        setTickets(ticketsResponse.value.data);
      } else {
        throw new Error('Failed to load Zendesk tickets');
      }

      if (usersResponse.status === 'fulfilled') {
        if (!usersResponse.value.data) {
          throw new Error('Zendesk users data not available');
        }
        setUsers(usersResponse.value.data);
      } else {
        throw new Error('Failed to load Zendesk users');
      }

      if (organizationsResponse.status === 'fulfilled') {
        if (!organizationsResponse.value.data) {
          throw new Error('Zendesk organizations data not available');
        }
        setOrganizations(organizationsResponse.value.data);
      } else {
        throw new Error('Failed to load Zendesk organizations');
      }
    } catch (err) {
      setError('Error loading Zendesk analytics');
      console.error('Zendesk analytics error:', err);
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

  const openTickets = tickets.filter(ticket => ticket.status === 'open' || ticket.status === 'pending');
  const solvedTickets = tickets.filter(ticket => ticket.status === 'solved' || ticket.status === 'closed');
  const urgentTickets = tickets.filter(ticket => ticket.priority === 'urgent' || ticket.priority === 'high');
  const agents = users.filter(user => user.role === 'agent' || user.role === 'admin');

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-neutral-50 rounded-lg p-4 border border-neutral-200">
          <div className="flex items-center space-x-2">
            <TicketIcon className="h-5 w-5 text-neutral-600" />
            <div>
              <p className="text-sm font-medium text-neutral-700">Total Tickets</p>
              <p className="text-xl font-bold text-neutral-900">{tickets.length}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-neutral-50 rounded-lg p-4 border border-neutral-200">
          <div className="flex items-center space-x-2">
            <ClockIcon className="h-5 w-5 text-neutral-600" />
            <div>
              <p className="text-sm font-medium text-neutral-700">Open Tickets</p>
              <p className="text-xl font-bold text-neutral-900">{openTickets.length}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-neutral-50 rounded-lg p-4 border border-neutral-200">
          <div className="flex items-center space-x-2">
            <CheckCircleIcon className="h-5 w-5 text-neutral-600" />
            <div>
              <p className="text-sm font-medium text-neutral-700">Solved</p>
              <p className="text-xl font-bold text-neutral-900">{solvedTickets.length}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-neutral-50 rounded-lg p-4 border border-neutral-200">
          <div className="flex items-center space-x-2">
            <ExclamationCircleIcon className="h-5 w-5 text-neutral-600" />
            <div>
              <p className="text-sm font-medium text-neutral-700">Urgent</p>
              <p className="text-xl font-bold text-neutral-900">{urgentTickets.length}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Tickets */}
      <div>
        <h3 className="text-lg font-medium text-neutral-900 mb-4 flex items-center space-x-2">
          <ChatBubbleLeftRightIcon className="h-5 w-5" />
          <span>Recent Tickets</span>
        </h3>
        {tickets.length > 0 ? (
          <div className="space-y-3">
            {tickets
              .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
              .slice(0, 8)
              .map((ticket) => (
                <div key={ticket.id} className="bg-white border border-neutral-200 rounded-lg p-4 hover:shadow-sm transition-shadow">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <span className="text-sm font-mono text-neutral-500">#{ticket.id}</span>
                        <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${
                          ticket.status === 'open' ? 'bg-green-100 text-green-800' :
                          ticket.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                          ticket.status === 'solved' ? 'bg-blue-100 text-blue-800' :
                          'bg-neutral-100 text-neutral-800'
                        }`}>
                          {ticket.status}
                        </span>
                        {ticket.priority && (
                          <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${
                            ticket.priority === 'urgent' ? 'bg-red-100 text-red-800' :
                            ticket.priority === 'high' ? 'bg-orange-100 text-orange-800' :
                            'bg-neutral-100 text-neutral-800'
                          }`}>
                            {ticket.priority}
                          </span>
                        )}
                      </div>
                      <h4 className="font-medium text-neutral-900 mb-1">{ticket.subject}</h4>
                      <div className="flex items-center space-x-4 text-sm text-neutral-600">
                        {ticket.requester && (
                          <span>Requester: {ticket.requester.name}</span>
                        )}
                        {ticket.assignee && (
                          <span>Assigned to: {ticket.assignee.name}</span>
                        )}
                        <span>{new Date(ticket.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))
            }
          </div>
        ) : (
          <p className="text-sm text-neutral-600">No tickets found</p>
        )}
      </div>

      {/* Agent Performance & Organizations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Agents */}
        <div className="bg-white border border-neutral-200 rounded-lg p-4">
          <h4 className="font-medium text-neutral-900 mb-3 flex items-center space-x-2">
            <UserGroupIcon className="h-5 w-5" />
            <span>Support Agents</span>
          </h4>
          <div className="space-y-2">
            {agents.slice(0, 5).map((agent) => {
              const agentTickets = tickets.filter(ticket => ticket.assignee_id === agent.id);
              return (
                <div key={agent.id} className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 rounded-full bg-green-500"></div>
                    <span className="text-sm text-neutral-700">{agent.name}</span>
                    {agent.role === 'admin' && (
                      <span className="inline-flex px-1 py-0.5 rounded text-xs font-medium bg-primary-100 text-primary-800">
                        Admin
                      </span>
                    )}
                  </div>
                  <span className="text-sm text-neutral-500">{agentTickets.length} tickets</span>
                </div>
              );
            })}
            {agents.length > 5 && (
              <p className="text-xs text-neutral-500 mt-2">
                +{agents.length - 5} more agents
              </p>
            )}
          </div>
        </div>

        {/* Organizations */}
        <div className="bg-white border border-neutral-200 rounded-lg p-4">
          <h4 className="font-medium text-neutral-900 mb-3 flex items-center space-x-2">
            <FaceSmileIcon className="h-5 w-5" />
            <span>Top Organizations</span>
          </h4>
          <div className="space-y-2">
            {organizations.slice(0, 5).map((org) => {
              const orgTickets = tickets.filter(ticket => ticket.organization_id === org.id);
              return (
                <div key={org.id} className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 rounded-full bg-blue-500"></div>
                    <span className="text-sm text-neutral-700">{org.name}</span>
                  </div>
                  <span className="text-sm text-neutral-500">{orgTickets.length} tickets</span>
                </div>
              );
            })}
            {organizations.length > 5 && (
              <p className="text-xs text-neutral-500 mt-2">
                +{organizations.length - 5} more organizations
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}