'use client';

import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/Button';
import { apiClient, IntegrationTemplate } from '@/lib/api';
import { INTEGRATION_TYPES, IntegrationType, INTEGRATION_CATEGORIES } from '@/lib/integrationTypes';
import { 
  PuzzlePieceIcon, 
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ArrowRightIcon,
  ArrowLeftIcon
} from '@heroicons/react/24/outline';

const integrationSchema = z.object({
  name: z.string().min(2, 'Integration name must be at least 2 characters'),
  description: z.string().optional(),
  integration_type: z.enum(INTEGRATION_TYPES),
  base_url: z.string().url('Please enter a valid URL').optional(),
  api_key: z.string().min(1, 'API key is required'),
  username: z.string().optional(),
  password: z.string().optional(),
  api_token: z.string().optional(),
  access_key: z.string().optional(),
  secret_key: z.string().optional(),
  client_id: z.string().optional(),
  client_secret: z.string().optional(),
  tenant_id: z.string().optional(),
  subscription_id: z.string().optional(),
  region: z.string().optional(),
  refresh_token: z.string().optional(),
  config: z.record(z.any()).optional(),
  monitoring_preferences: z.array(z.string()).optional(),
});

type IntegrationFormData = z.infer<typeof integrationSchema>;

const integrationTemplates: IntegrationTemplate[] = [
  // Project Management
  {
    id: 'jira',
    name: 'Jira',
    description: 'Track issues, projects, and team performance',
    icon: '🎯',
    fields: ['base_url', 'api_key', 'username'],
    config: {
      category: 'project_management',
      monitoring: ['issue_count', 'project_status', 'sprint_progress'],
      endpoints: {
        issues: '/rest/api/2/issue',
        projects: '/rest/api/2/project',
        users: '/rest/api/2/user'
      }
    }
  },
  {
    id: 'asana',
    name: 'Asana',
    description: 'Monitor tasks, projects, and team productivity',
    icon: '📋',
    fields: ['api_key'],
    config: {
      category: 'project_management',
      monitoring: ['task_completion', 'project_timeline', 'team_workload'],
      endpoints: {
        tasks: '/api/1.0/tasks',
        projects: '/api/1.0/projects'
      }
    }
  },
  {
    id: 'trello',
    name: 'Trello',
    description: 'Track boards, cards, and workflow progress',
    icon: '📊',
    fields: ['api_key', 'api_token'],
    config: {
      category: 'project_management',
      monitoring: ['board_activity', 'card_movement', 'due_dates'],
      endpoints: {
        boards: '/1/members/me/boards',
        cards: '/1/boards/{id}/cards'
      }
    }
  },
  
  // Customer Support
  {
    id: 'zendesk',
    name: 'Zendesk',
    description: 'Monitor tickets, customer satisfaction, and support metrics',
    icon: '🎫',
    fields: ['base_url', 'api_key', 'username'],
    config: {
      category: 'customer_support',
      monitoring: ['ticket_volume', 'response_time', 'satisfaction_score'],
      endpoints: {
        tickets: '/api/v2/tickets',
        users: '/api/v2/users',
        organizations: '/api/v2/organizations'
      }
    }
  },
  {
    id: 'freshdesk',
    name: 'Freshdesk',
    description: 'Track support tickets and team performance',
    icon: '🆘',
    fields: ['base_url', 'api_key'],
    config: {
      category: 'customer_support',
      monitoring: ['ticket_status', 'agent_performance', 'sla_compliance'],
      endpoints: {
        tickets: '/api/v2/tickets',
        agents: '/api/v2/agents'
      }
    }
  },
  
  // CRM Systems
  {
    id: 'salesforce',
    name: 'Salesforce',
    description: 'Monitor sales pipeline, leads, and revenue metrics',
    icon: '☁️',
    fields: ['base_url', 'api_key', 'username', 'password'],
    config: {
      category: 'crm',
      monitoring: ['pipeline_health', 'lead_conversion', 'revenue_forecast'],
      endpoints: {
        leads: '/services/data/v52.0/sobjects/Lead',
        contacts: '/services/data/v52.0/sobjects/Contact',
        opportunities: '/services/data/v52.0/sobjects/Opportunity'
      }
    }
  },
  {
    id: 'hubspot',
    name: 'HubSpot',
    description: 'Track contacts, deals, and marketing campaigns',
    icon: '🔶',
    fields: ['api_key'],
    config: {
      category: 'crm',
      monitoring: ['deal_stage', 'contact_engagement', 'campaign_performance'],
      endpoints: {
        contacts: '/crm/v3/objects/contacts',
        deals: '/crm/v3/objects/deals'
      }
    }
  },
  
  // Development Tools
  {
    id: 'github',
    name: 'GitHub',
    description: 'Monitor repositories, issues, and development metrics',
    icon: '🐙',
    fields: ['api_key'],
    config: {
      category: 'development',
      monitoring: ['commit_frequency', 'pull_request_status', 'issue_resolution'],
      endpoints: {
        repos: '/user/repos',
        issues: '/repos/{owner}/{repo}/issues',
        pull_requests: '/repos/{owner}/{repo}/pulls'
      }
    }
  },
  {
    id: 'gitlab',
    name: 'GitLab',
    description: 'Track projects, pipelines, and code quality',
    icon: '🦊',
    fields: ['base_url', 'api_key'],
    config: {
      category: 'development',
      monitoring: ['pipeline_success', 'merge_requests', 'code_coverage'],
      endpoints: {
        projects: '/api/v4/projects',
        pipelines: '/api/v4/projects/{id}/pipelines'
      }
    }
  },
  
  // Communication
  {
    id: 'slack',
    name: 'Slack',
    description: 'Monitor team communication and activity',
    icon: '💬',
    fields: ['api_key'],
    config: {
      category: 'communication',
      monitoring: ['message_volume', 'active_users', 'response_time'],
      endpoints: {
        conversations: '/api/conversations.list',
        users: '/api/users.list'
      }
    }
  },
  
  // Cloud Platforms
  {
    id: 'aws',
    name: 'AWS',
    description: 'Monitor cloud resources, costs, and performance',
    icon: '☁️',
    fields: ['access_key', 'secret_key', 'region'],
    config: {
      category: 'cloud_platform',
      monitoring: ['resource_utilization', 'cost_tracking', 'service_health'],
      endpoints: {
        ec2: 'ec2.{region}.amazonaws.com',
        cloudwatch: 'monitoring.{region}.amazonaws.com'
      }
    }
  },
  {
    id: 'azure',
    name: 'Azure',
    description: 'Track Azure resources and service metrics',
    icon: '🔷',
    fields: ['subscription_id', 'client_id', 'client_secret', 'tenant_id'],
    config: {
      category: 'cloud_platform',
      monitoring: ['vm_performance', 'storage_usage', 'cost_analysis'],
      endpoints: {
        resources: 'management.azure.com',
        monitor: 'monitor.azure.com'
      }
    }
  },
  
  // Analytics
  {
    id: 'google_analytics',
    name: 'Google Analytics',
    description: 'Monitor website traffic and user behavior',
    icon: '📈',
    fields: ['client_id', 'client_secret', 'refresh_token'],
    config: {
      category: 'analytics',
      monitoring: ['page_views', 'user_sessions', 'conversion_rate'],
      endpoints: {
        reports: 'analyticsreporting.googleapis.com/v4/reports:batchGet'
      }
    }
  },
  
  // Custom Integration
  {
    id: 'custom',
    name: 'Custom System',
    description: 'Connect to any custom API or system you want to monitor',
    icon: '🔧',
    fields: ['base_url', 'api_key'],
    config: {
      category: 'custom',
      monitoring: ['custom_metrics', 'system_health', 'data_quality'],
      endpoints: {}
    }
  }
];

interface IntegrationWizardProps {
  onComplete: (data: IntegrationFormData) => void;
  onCancel: () => void;
}

export default function IntegrationWizard({ onComplete, onCancel }: IntegrationWizardProps) {
  const [currentStep, setCurrentStep] = useState(1);
  const [selectedTemplate, setSelectedTemplate] = useState<IntegrationTemplate | null>(null);
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isValid },
  } = useForm<IntegrationFormData>({
    resolver: zodResolver(integrationSchema),
    mode: 'onChange',
  });

  const watchedType = watch('integration_type');

  const handleTemplateSelect = (template: IntegrationTemplate) => {
    setSelectedTemplate(template);
    setValue('integration_type', template.id as any);
    setValue('config', template.config);
    setCurrentStep(2);
  };

  const handleTestConnection = async (data: IntegrationFormData) => {
    setIsTesting(true);
    setTestResult(null);
    setError(null);
    
    try {
      // Prepare credentials object
      const credentials: Record<string, string> = {};
      
      // Build credentials object based on available fields
      if (data.api_key) credentials.api_key = data.api_key;
      if (data.username) credentials.username = data.username;
      if (data.password) credentials.password = data.password;
      if (data.api_token) credentials.api_token = data.api_token;
      if (data.access_key) credentials.access_key = data.access_key;
      if (data.secret_key) credentials.secret_key = data.secret_key;
      if (data.client_id) credentials.client_id = data.client_id;
      if (data.client_secret) credentials.client_secret = data.client_secret;
      if (data.tenant_id) credentials.tenant_id = data.tenant_id;
      if (data.subscription_id) credentials.subscription_id = data.subscription_id;
      if (data.region) credentials.region = data.region;
      if (data.refresh_token) credentials.refresh_token = data.refresh_token;

      console.log('Creating integration with data:', {
        name: data.name,
        description: data.description,
        integration_type: data.integration_type,
        base_url: data.base_url,
        credentials: Object.keys(credentials),
        config: selectedTemplate?.config
      });

      // First create the integration
      const integration = await apiClient.createIntegration({
        name: data.name,
        description: data.description,
        integration_type: data.integration_type,
        base_url: data.base_url || selectedTemplate?.config.endpoints?.base_url || `https://${data.integration_type}.api.com`,
        credentials,
        config: {
          ...selectedTemplate?.config,
          monitoring_preferences: data.monitoring_preferences || selectedTemplate?.config.monitoring
        }
      });

      // Then test the connection
      const testResult = await apiClient.testIntegration(integration.id);
      
      setTestResult({
        success: testResult.success || true,
        message: testResult.message || 'Connection successful! Integration is ready to use.'
      });
      
      if (testResult.success !== false) {
        setCurrentStep(4);
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'An error occurred while testing the connection.';
      console.error('Integration test failed:', error);
      setError(errorMessage);
      setTestResult({
        success: false,
        message: errorMessage
      });
    } finally {
      setIsTesting(false);
    }
  };

  const handleFormSubmit = async (data: IntegrationFormData) => {
    setError(null);
    
    try {
      if (currentStep === 2) {
        // Validate required fields before proceeding
        if (!data.name?.trim()) {
          setError('Integration name is required');
          return;
        }
        if (!data.api_key?.trim()) {
          setError('API key is required');
          return;
        }
        setCurrentStep(3);
      } else if (currentStep === 3) {
        await handleTestConnection(data);
      } else if (currentStep === 4) {
        setIsSubmitting(true);
        await onComplete(data);
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'An unexpected error occurred';
      console.error('Form submission error:', error);
      setError(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  const goBack = () => {
    if (currentStep > 1) {
      setError(null);
      setTestResult(null);
      setCurrentStep(currentStep - 1);
    }
  };
  
  const handleCancel = () => {
    setError(null);
    setTestResult(null);
    onCancel();
  };

  const renderStep1 = () => {
    const categories = {
      custom: { name: 'Custom Systems', icon: '🔧', color: 'orange' },
      project_management: { name: 'Project Management', icon: '📋', color: 'blue' },
      customer_support: { name: 'Customer Support', icon: '🎫', color: 'green' },
      crm: { name: 'CRM & Sales', icon: '📈', color: 'purple' },
      development: { name: 'Development', icon: '🐙', color: 'gray' },
      communication: { name: 'Communication', icon: '💬', color: 'yellow' },
      cloud_platform: { name: 'Cloud Platforms', icon: '☁️', color: 'indigo' },
      analytics: { name: 'Analytics', icon: '📉', color: 'pink' }
    };

    return (
      <div className="space-y-6">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-neutral-900">Choose System to Monitor</h2>
          <p className="text-neutral-600 mt-2">Connect your business systems for AI-powered monitoring and insights</p>
        </div>
        
        {/* Custom System - Always show at top */}
        <div className="space-y-3">
          <div className="flex items-center space-x-2">
            <span className="text-lg">🔧</span>
            <h3 className="font-medium text-neutral-800">Custom Systems</h3>
            <span className="bg-green-100 text-green-800 text-xs font-medium px-2 py-1 rounded-full">Popular</span>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            <button
              onClick={() => handleTemplateSelect(integrationTemplates.find(t => t.id === 'custom')!)}
              className="p-6 border-2 border-green-200 bg-green-50 rounded-xl hover:border-green-300 hover:shadow-lg transition-all duration-300 text-left group relative overflow-hidden hover:bg-green-100/50"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <span className="text-xl">🔧</span>
                  <h4 className="font-semibold text-neutral-900 group-hover:text-green-700">Custom System</h4>
                </div>
              </div>
              <p className="text-sm text-neutral-600 mb-3">Connect to any custom API or system you want to monitor</p>
              
              {/* Endpoint Requirements */}
              <div className="mb-3">
                <p className="text-xs font-semibold text-neutral-600 mb-2">📡 API Endpoints:</p>
                <div className="bg-neutral-50 rounded-md p-2 text-xs text-neutral-700">
                  <span className="text-neutral-500">Custom API endpoint required</span>
                </div>
              </div>
              
              {/* Monitoring Capabilities */}
              <div className="mb-3">
                <p className="text-xs font-semibold text-neutral-600 mb-2">📊 Monitors:</p>
                <div className="flex flex-wrap gap-1">
                  <span className="inline-flex px-2 py-1 text-xs rounded-full bg-green-100 text-green-700 font-medium">custom metrics</span>
                  <span className="inline-flex px-2 py-1 text-xs rounded-full bg-green-100 text-green-700 font-medium">system health</span>
                  <span className="inline-flex px-2 py-1 text-xs rounded-full bg-neutral-100 text-neutral-600">+1 more</span>
                </div>
              </div>
            </button>
          </div>
        </div>
        
        {Object.entries(categories).map(([categoryKey, category]) => {
          if (categoryKey === 'custom') return null; // Skip custom since we showed it above
          const categoryTemplates = integrationTemplates.filter(t => t.config.category === categoryKey);
          console.log(`Category: ${categoryKey}, Templates: ${categoryTemplates.length}`, categoryTemplates.map(t => t.name));
          if (categoryTemplates.length === 0) return null;
          
          return (
            <div key={categoryKey} className="space-y-3">
              <div className="flex items-center space-x-2">
                <span className="text-lg">{category.icon}</span>
                <h3 className="font-medium text-neutral-800">{category.name}</h3>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {categoryTemplates.map((template) => (
                  <button
                    key={template.id}
                    onClick={() => handleTemplateSelect(template)}
                    className="p-6 border border-neutral-200 rounded-xl hover:border-green-300 hover:shadow-lg transition-all duration-300 text-left group relative overflow-hidden bg-white hover:bg-green-50/30"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <span className="text-xl">{template.icon}</span>
                        <h4 className="font-semibold text-neutral-900 group-hover:text-green-700">{template.name}</h4>
                      </div>
                    </div>
                    <p className="text-sm text-neutral-600 mb-3">{template.description}</p>
                    
                    {/* Endpoint Requirements */}
                    <div className="mb-3">
                      <p className="text-xs font-semibold text-neutral-600 mb-2">📡 API Endpoints:</p>
                      <div className="bg-neutral-50 rounded-md p-2 text-xs text-neutral-700">
                        {Object.entries(template.config.endpoints || {}).length > 0 ? (
                          Object.entries(template.config.endpoints).map(([key, endpoint]) => (
                            <div key={key} className="font-mono">
                              <span className="text-green-600">{key}:</span> {endpoint as string}
                            </div>
                          ))
                        ) : (
                          <span className="text-neutral-500">Custom API endpoint required</span>
                        )}
                      </div>
                    </div>
                    
                    {/* Monitoring Capabilities */}
                    <div className="mb-3">
                      <p className="text-xs font-semibold text-neutral-600 mb-2">📊 Monitors:</p>
                      <div className="flex flex-wrap gap-1">
                        {template.config.monitoring?.slice(0, 2).map((metric, idx) => (
                          <span key={idx} className="inline-flex px-2 py-1 text-xs rounded-full bg-green-100 text-green-700 font-medium">
                            {metric.replace('_', ' ')}
                          </span>
                        ))}
                        {template.config.monitoring?.length > 2 && (
                          <span className="inline-flex px-2 py-1 text-xs rounded-full bg-neutral-100 text-neutral-600">
                            +{template.config.monitoring.length - 2} more
                          </span>
                        )}
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  const renderStep2 = () => (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-neutral-900">Configure {selectedTemplate?.name}</h2>
        <p className="text-neutral-600 mt-2">Enter your connection details</p>
      </div>
      
      <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-neutral-700 mb-2">
            Integration Name
          </label>
          <input
            {...register('name')}
            type="text"
            id="name"
            className={`w-full px-4 py-3 border rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors ${
              errors.name ? 'border-red-300' : 'border-neutral-300'
            }`}
            placeholder="e.g., Production Jira"
          />
          {errors.name && (
            <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
          )}
        </div>

        <div>
          <label htmlFor="description" className="block text-sm font-medium text-neutral-700 mb-2">
            Description (Optional)
          </label>
          <textarea
            {...register('description')}
            id="description"
            rows={3}
            className="w-full px-4 py-3 border border-neutral-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
            placeholder="Describe what this integration is for..."
          />
        </div>

        {selectedTemplate?.fields.includes('base_url') && (
          <div>
            <label htmlFor="base_url" className="block text-sm font-medium text-neutral-700 mb-2">
              Base URL
            </label>
            <input
              {...register('base_url')}
              type="url"
              id="base_url"
              className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 ${
                errors.base_url ? 'border-red-300' : 'border-neutral-300'
              }`}
              placeholder="https://your-domain.com"
            />
            {errors.base_url && (
              <p className="mt-1 text-sm text-red-600">{errors.base_url.message}</p>
            )}
          </div>
        )}

        <div>
          <label htmlFor="api_key" className="block text-sm font-medium text-neutral-700 mb-2">
            API Key / Token
            <span className="text-xs text-neutral-500 ml-2">🔑 Authentication required</span>
          </label>
          <input
            {...register('api_key')}
            type="password"
            id="api_key"
            className={`w-full px-4 py-3 border rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors ${
              errors.api_key ? 'border-red-300' : 'border-neutral-300'
            }`}
            placeholder="Enter your API key or token"
          />
          {errors.api_key && (
            <p className="mt-1 text-sm text-red-600">{errors.api_key.message}</p>
          )}
          <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-xs text-blue-800">
              <strong>🔍 Where to find this:</strong>
              {selectedTemplate?.id === 'jira' && ' Go to Jira → Settings → System → Personal Access Tokens'}
              {selectedTemplate?.id === 'github' && ' Go to GitHub → Settings → Developer settings → Personal access tokens'}
              {selectedTemplate?.id === 'salesforce' && ' Go to Salesforce → Setup → Apps → App Manager → Connected Apps'}
              {selectedTemplate?.id === 'zendesk' && ' Go to Zendesk → Admin → Channels → API → Token Access'}
              {selectedTemplate?.id === 'custom' && ' Check your API documentation for authentication details'}
              {!['jira', 'github', 'salesforce', 'zendesk', 'custom'].includes(selectedTemplate?.id || '') && ' Check your platform\'s API documentation for authentication details'}
            </p>
          </div>
        </div>

        {selectedTemplate?.fields.includes('username') && (
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-neutral-700 mb-2">
              Username / Email
            </label>
            <input
              {...register('username')}
              type="text"
              id="username"
              className="w-full px-4 py-3 border border-neutral-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
              placeholder="Enter your username or email"
            />
          </div>
        )}

        {selectedTemplate?.fields.includes('password') && (
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-neutral-700 mb-2">
              Password
            </label>
            <input
              {...register('password')}
              type="password"
              id="password"
              className="w-full px-4 py-3 border border-neutral-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
              placeholder="Enter your password"
            />
          </div>
        )}

        {/* Additional fields for different integration types */}
        {selectedTemplate?.fields.includes('api_token') && (
          <div>
            <label htmlFor="api_token" className="block text-sm font-medium text-neutral-700 mb-2">
              API Token
            </label>
            <input
              {...register('api_token')}
              type="password"
              id="api_token"
              className="w-full px-4 py-3 border border-neutral-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
              placeholder="Enter your API token"
            />
          </div>
        )}

        {selectedTemplate?.fields.includes('access_key') && (
          <div>
            <label htmlFor="access_key" className="block text-sm font-medium text-neutral-700 mb-2">
              Access Key ID
            </label>
            <input
              {...register('access_key')}
              type="password"
              id="access_key"
              className="w-full px-4 py-3 border border-neutral-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
              placeholder="Enter your access key ID"
            />
          </div>
        )}

        {selectedTemplate?.fields.includes('secret_key') && (
          <div>
            <label htmlFor="secret_key" className="block text-sm font-medium text-neutral-700 mb-2">
              Secret Access Key
            </label>
            <input
              {...register('secret_key')}
              type="password"
              id="secret_key"
              className="w-full px-4 py-3 border border-neutral-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
              placeholder="Enter your secret access key"
            />
          </div>
        )}

        {selectedTemplate?.fields.includes('client_id') && (
          <div>
            <label htmlFor="client_id" className="block text-sm font-medium text-neutral-700 mb-2">
              Client ID
            </label>
            <input
              {...register('client_id')}
              type="text"
              id="client_id"
              className="w-full px-4 py-3 border border-neutral-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
              placeholder="Enter your client ID"
            />
          </div>
        )}

        {selectedTemplate?.fields.includes('client_secret') && (
          <div>
            <label htmlFor="client_secret" className="block text-sm font-medium text-neutral-700 mb-2">
              Client Secret
            </label>
            <input
              {...register('client_secret')}
              type="password"
              id="client_secret"
              className="w-full px-4 py-3 border border-neutral-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
              placeholder="Enter your client secret"
            />
          </div>
        )}

        {selectedTemplate?.fields.includes('tenant_id') && (
          <div>
            <label htmlFor="tenant_id" className="block text-sm font-medium text-neutral-700 mb-2">
              Tenant ID
            </label>
            <input
              {...register('tenant_id')}
              type="text"
              id="tenant_id"
              className="w-full px-4 py-3 border border-neutral-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
              placeholder="Enter your tenant ID"
            />
          </div>
        )}

        {selectedTemplate?.fields.includes('subscription_id') && (
          <div>
            <label htmlFor="subscription_id" className="block text-sm font-medium text-neutral-700 mb-2">
              Subscription ID
            </label>
            <input
              {...register('subscription_id')}
              type="text"
              id="subscription_id"
              className="w-full px-4 py-3 border border-neutral-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
              placeholder="Enter your subscription ID"
            />
          </div>
        )}

        {selectedTemplate?.fields.includes('region') && (
          <div>
            <label htmlFor="region" className="block text-sm font-medium text-neutral-700 mb-2">
              Region
            </label>
            <input
              {...register('region')}
              type="text"
              id="region"
              className="w-full px-4 py-3 border border-neutral-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
              placeholder="e.g., us-east-1"
            />
          </div>
        )}

        {selectedTemplate?.fields.includes('refresh_token') && (
          <div>
            <label htmlFor="refresh_token" className="block text-sm font-medium text-neutral-700 mb-2">
              Refresh Token
            </label>
            <input
              {...register('refresh_token')}
              type="password"
              id="refresh_token"
              className="w-full px-4 py-3 border border-neutral-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
              placeholder="Enter your refresh token"
            />
          </div>
        )}

        {/* Monitoring Preferences */}
        {selectedTemplate && selectedTemplate.config.monitoring && (
          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-3">
              What would you like to monitor? (Optional)
            </label>
            <div className="grid grid-cols-2 gap-2">
              {selectedTemplate.config.monitoring.map((metric, idx) => (
                <label key={idx} className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    value={metric}
                    {...register('monitoring_preferences')}
                    className="rounded border-neutral-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span className="text-sm text-neutral-700 capitalize">
                    {metric.replace(/_/g, ' ')}
                  </span>
                </label>
              ))}
            </div>
            <p className="text-xs text-neutral-500 mt-2">
              You can customize monitoring preferences later
            </p>
          </div>
        )}

        <div className="flex justify-end pt-6">
          <Button
            type="submit"
            disabled={!isValid}
            rightIcon={<ArrowRightIcon className="h-4 w-4" />}
            className="bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded-lg font-medium transition-colors"
          >
            Continue to Test
          </Button>
        </div>
      </form>
    </div>
  );

  const renderStep3 = () => (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-neutral-900">Test Connection</h2>
        <p className="text-neutral-600 mt-2">Let&apos;s verify your integration works before saving</p>
      </div>
      
      <div className="bg-neutral-50 border border-neutral-200 rounded-lg p-6">
        <div className="flex items-center space-x-3 mb-4">
          <PuzzlePieceIcon className="h-6 w-6 text-primary-600" />
          <h3 className="font-medium text-neutral-900">Connection Details</h3>
        </div>
        
        <div className="space-y-2 text-sm text-neutral-600">
          <p><span className="font-medium">Name:</span> {watch('name')}</p>
          <p><span className="font-medium">Type:</span> {watch('integration_type')}</p>
          <p><span className="font-medium">URL:</span> {watch('base_url')}</p>
        </div>
      </div>
      
      <div className="text-center">
        <Button
          onClick={handleSubmit(handleFormSubmit)}
          loading={isTesting}
          disabled={isTesting}
          className="w-full"
        >
          {isTesting ? 'Testing Connection...' : 'Test Connection'}
        </Button>
      </div>
      
      {testResult && (
        <div className={`p-4 rounded-md border ${
          testResult.success 
            ? 'bg-green-50 border-green-200' 
            : 'bg-red-50 border-red-200'
        }`}>
          <div className="flex items-center space-x-2">
            {testResult.success ? (
              <CheckCircleIcon className="h-5 w-5 text-green-600" />
            ) : (
              <ExclamationTriangleIcon className="h-5 w-5 text-red-600" />
            )}
            <p className={`text-sm font-medium ${
              testResult.success ? 'text-green-800' : 'text-red-800'
            }`}>
              {testResult.message}
            </p>
          </div>
        </div>
      )}
      
      <div className="flex justify-center pt-6">
        {testResult?.success && (
          <Button
            onClick={() => setCurrentStep(4)}
            rightIcon={<ArrowRightIcon className="h-4 w-4" />}
            className="bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded-lg font-medium transition-colors"
          >
            Continue to Finish
          </Button>
        )}
      </div>
    </div>
  );

  const renderStep4 = () => (
    <div className="space-y-6 text-center">
      <div className="mx-auto h-16 w-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
        <CheckCircleIcon className="h-12 w-12 text-green-600" />
      </div>
      
      <h2 className="text-2xl font-bold text-neutral-900">Integration Ready!</h2>
      <p className="text-neutral-600">
        Your {selectedTemplate?.name} integration has been successfully configured and tested.
      </p>
      
      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
        <p className="text-sm text-green-800">
          The integration is now active and ready to use. You can start querying your data through the chat interface.
        </p>
      </div>
      
      <Button
        onClick={handleSubmit(handleFormSubmit)}
        className="w-full"
        size="lg"
      >
        Complete Setup
      </Button>
    </div>
  );

  const renderCurrentStep = () => {
    switch (currentStep) {
      case 1:
        return renderStep1();
      case 2:
        return renderStep2();
      case 3:
        return renderStep3();
      case 4:
        return renderStep4();
      default:
        return renderStep1();
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white shadow-xl rounded-2xl border border-neutral-200">
        {/* Progress bar */}
        <div className="px-6 py-4 border-b border-neutral-200">
          <div className="flex items-center justify-between">
            {[1, 2, 3, 4].map((step) => (
              <div key={step} className="flex items-center">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  step < currentStep
                    ? 'bg-green-500 text-white'
                    : step === currentStep
                    ? 'bg-primary-500 text-white'
                    : 'bg-neutral-200 text-neutral-600'
                }`}>
                  {step < currentStep ? (
                    <CheckCircleIcon className="h-5 w-5" />
                  ) : (
                    step
                  )}
                </div>
                {step < 4 && (
                  <div className={`w-16 h-0.5 mx-2 ${
                    step < currentStep ? 'bg-green-500' : 'bg-neutral-200'
                  }`} />
                )}
              </div>
            ))}
          </div>
        </div>
        
        {/* Step content */}
        <div className="px-8 py-10">
          {renderCurrentStep()}
        </div>
        
        {/* Footer with navigation and close */}
        <div className="px-8 py-6 bg-gray-50 border-t border-neutral-200 flex justify-between items-center">
          <div className="flex space-x-3">
            {currentStep > 1 && (
              <Button
                type="button"
                variant="outline"
                onClick={goBack}
                leftIcon={<ArrowLeftIcon className="h-4 w-4" />}
              >
                Back
              </Button>
            )}
            <Button
              type="button"
              variant="outline"
              onClick={onCancel}
              className="text-neutral-600 hover:text-neutral-800"
            >
              Cancel
            </Button>
          </div>
          
          <div className="text-sm text-neutral-500">
            Step {currentStep} of 4
          </div>
        </div>
      </div>
    </div>
  );
}
