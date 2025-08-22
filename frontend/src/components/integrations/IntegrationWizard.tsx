'use client';

import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/Button';
import { apiClient, IntegrationTemplate, OAuthSupport } from '@/lib/api';
import { INTEGRATION_CATEGORIES } from '@/lib/integrationTypes';
import { 
  PuzzlePieceIcon, 
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ArrowRightIcon,
  ArrowLeftIcon,
  XMarkIcon,
  CloudIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';

const integrationSchema = z.object({
  name: z.string().min(2, 'Integration name must be at least 2 characters'),
  description: z.string().optional(),
  integration_type: z.string().min(1, 'Please select an integration type'),
  base_url: z.string().url('Please enter a valid URL').optional().or(z.literal('')),
  // Dynamic credentials based on template
  credentials: z.record(z.string()).optional(),
});

type IntegrationFormData = z.infer<typeof integrationSchema>;

interface IntegrationWizardProps {
  onComplete: (integration: any) => void;
  onCancel: () => void;
}

export default function IntegrationWizard({ onComplete, onCancel }: IntegrationWizardProps) {
  const [currentStep, setCurrentStep] = useState(1);
  const [templates, setTemplates] = useState<Record<string, IntegrationTemplate>>({});
  const [templatesLoading, setTemplatesLoading] = useState(true);
  const [selectedTemplate, setSelectedTemplate] = useState<IntegrationTemplate | null>(null);
  const [oauthSupport, setOAuthSupport] = useState<Record<string, OAuthSupport>>({});
  const [authMethod, setAuthMethod] = useState<'credentials' | 'oauth'>('credentials');
  const [scopes, setScopes] = useState<string[]>([]);
  const [availableScopes, setAvailableScopes] = useState<string[]>([]);
  const [isTesting, setIsTesting] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
    setValue,
    reset
  } = useForm<IntegrationFormData>({
    resolver: zodResolver(integrationSchema),
    mode: 'onChange',
  });

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      setTemplatesLoading(true);
      setError(null);
      
      const response = await apiClient.getIntegrationTemplates();
      // Handle both possible response formats
      const templateData = response.templates || response;
      
      // Convert to the format expected by the frontend
      const processedTemplates: Record<string, IntegrationTemplate> = {};
      
      Object.entries(templateData).forEach(([key, template]: [string, any]) => {
        const processedTemplate: IntegrationTemplate & { iconComponent?: React.ReactNode } = {
          id: key.toLowerCase(),
          name: template.name,
          description: template.description,
          category: getCategoryFromType(key.toLowerCase()),
          integration_type: key.toLowerCase(),
          icon: key.toLowerCase(),
          iconComponent: getIconForType(key.toLowerCase()),
          config: {
            endpoints: template.endpoints || {},
            required_credentials: template.required_credentials || [],
            optional_credentials: template.optional_credentials || [],
            default_settings: template.default_settings || {},
            capabilities: template.capabilities || [],
          },
          fields: template.required_credentials || [],
          documentation_url: template.documentation,
          setup_instructions: template.setup_instructions || []
        };
        processedTemplates[key.toLowerCase()] = processedTemplate;
      });
      
      setTemplates(processedTemplates);
    } catch (err) {
      console.error('Error fetching templates:', err);
      setError(err instanceof Error ? err.message : 'Failed to load integration templates');
    } finally {
      setTemplatesLoading(false);
    }
  };

  const getCategoryFromType = (type: string): string => {
    // Find which category this type belongs to
    for (const [category, types] of Object.entries(INTEGRATION_CATEGORIES)) {
      if (types.includes(type as any)) {
        return category;
      }
    }
    return 'other';
  };

  const getIconForType = (type: string): React.ReactNode => {
    const logoMap: Record<string, string> = {
      jira: '/integration-logos/jira.svg',
      asana: '/integration-logos/asana.svg', 
      trello: '/integration-logos/trello.svg',
      zendesk: '/integration-logos/zendesk.svg',
      salesforce: '/integration-logos/salesforce.svg',
      github: '/integration-logos/github.svg',
      slack: '/integration-logos/slack.svg',
      hubspot: '/integration-logos/hubspot.svg'
    };

    if (logoMap[type]) {
      return (
        <img 
          src={logoMap[type]} 
          alt={`${type} logo`}
          className="w-16 h-16 object-contain"
        />
      );
    }

    // Fallback to emoji for services without logos
    const emojiMap: Record<string, string> = {
      monday: '📅',
      freshdesk: '🆘',
      gitlab: '🦊',
      aws: '☁️',
      azure: '🔵',
      google_analytics: '📊',
      custom: '⚙️'
    };
    
    return <span className="text-6xl">{emojiMap[type] || '⚙️'}</span>;
  };

  const handleTemplateSelect = async (template: IntegrationTemplate) => {
    setSelectedTemplate(template);
    setValue('integration_type', template.integration_type);
    
    // Fetch OAuth support information
    try {
      const [oauthSupportData, scopesData] = await Promise.allSettled([
        apiClient.getOAuthSupport(template.integration_type),
        apiClient.getOAuthScopes(template.integration_type).catch(() => ({ available_scopes: [], default_scopes: [] }))
      ]);
      
      if (oauthSupportData.status === 'fulfilled') {
        setOAuthSupport(prev => ({
          ...prev,
          [template.integration_type]: oauthSupportData.value
        }));
        
        // Set default auth method based on OAuth support
        if (oauthSupportData.value.supports_oauth) {
          setAuthMethod('oauth');
        } else {
          setAuthMethod('credentials');
        }
      }
      
      if (scopesData.status === 'fulfilled') {
        setAvailableScopes(scopesData.value.available_scopes || []);
        setScopes(scopesData.value.default_scopes || []);
      }
    } catch (err) {
      console.warn('Could not fetch OAuth support:', err);
      setAuthMethod('credentials');
    }
    
    setCurrentStep(2);
  };

  const handleCredentialSubmit = async (data: IntegrationFormData) => {
    if (!selectedTemplate) return;

    setError(null);
    setIsTesting(true);

    try {
      if (authMethod === 'oauth') {
        // Handle OAuth flow
        await handleOAuthFlow(data);
      } else {
        // Handle traditional credential flow
        await handleCredentialFlow(data);
      }
    } catch (err) {
      console.error('Integration creation failed:', err);
      setError(err instanceof Error ? err.message : 'Failed to create integration');
      setTestResult({
        success: false,
        message: err instanceof Error ? err.message : 'Integration setup failed'
      });
    } finally {
      setIsTesting(false);
    }
  };

  const handleCredentialFlow = async (data: IntegrationFormData) => {
    if (!selectedTemplate) return;

    // Build credentials object from form data
    const credentials: Record<string, string> = {};
    selectedTemplate.config.required_credentials.forEach(field => {
      const value = (data as any)[field];
      if (value) {
        credentials[field] = value;
      }
    });

    // Create integration
    const integration = await apiClient.createIntegration({
      name: data.name,
      description: data.description,
      integration_type: data.integration_type,
      base_url: data.base_url || undefined,
      credentials,
      config: selectedTemplate.config.default_settings || {},
    });

    // Test the integration
    const testResponse = await apiClient.testIntegration(integration.id);
    
    setTestResult({
      success: true,
      message: 'Integration created and tested successfully!'
    });
    
    setCurrentStep(3);
    
    // Complete after a short delay to show success
    setTimeout(() => {
      onComplete(integration);
    }, 2000);
  };

  const handleOAuthFlow = async (data: IntegrationFormData) => {
    if (!selectedTemplate) return;

    // Get client credentials from form
    const clientId = (data as any).client_id;
    const clientSecret = (data as any).client_secret;

    if (!clientId || !clientSecret) {
      throw new Error('Client ID and Client Secret are required for OAuth');
    }

    // Store OAuth flow data in session for callback
    const oauthData = {
      integration_type: data.integration_type,
      client_id: clientId,
      client_secret: clientSecret,
      name: data.name,
      description: data.description,
      config: selectedTemplate.config.default_settings || {}
    };

    // Initiate OAuth flow
    const authResponse = await apiClient.initiateOAuth({
      integration_type: data.integration_type,
      client_id: clientId,
      scopes: scopes.length > 0 ? scopes : undefined
    });

    // Store oauth data for callback
    sessionStorage.setItem(`oauth_${authResponse.state}`, JSON.stringify(oauthData));

    // Redirect to OAuth authorization URL
    window.location.href = authResponse.authorization_url;
  };

  const groupTemplatesByCategory = () => {
    const grouped: Record<string, IntegrationTemplate[]> = {};
    Object.values(templates).forEach(template => {
      const category = template.category;
      if (!grouped[category]) {
        grouped[category] = [];
      }
      grouped[category].push(template);
    });
    return grouped;
  };

  const getCategoryDisplayName = (category: string): string => {
    const categoryNames: Record<string, string> = {
      project_management: 'Project Management',
      customer_support: 'Customer Support',
      crm: 'CRM Systems',
      development: 'Development & DevOps',
      communication: 'Communication',
      cloud: 'Cloud Platforms',
      erp: 'ERP Systems',
      marketing: 'Marketing & Analytics',
      ecommerce: 'E-commerce',
      financial: 'Financial',
      hr: 'HR & Recruitment',
      other: 'Other',
      custom: 'Custom'
    };
    return categoryNames[category] || category.charAt(0).toUpperCase() + category.slice(1);
  };

  if (templatesLoading) {
    return (
      <div className="fixed inset-0 backdrop-blur-md flex items-center justify-center z-50">
        <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl mx-4 p-8">
          <div className="animate-pulse">
            <div className="flex items-center mb-6">
              <div className="w-8 h-8 bg-neutral-200 rounded mr-4"></div>
              <div className="h-8 bg-neutral-200 rounded w-64"></div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {[1, 2, 3, 4, 5, 6].map(i => (
                <div key={i} className="h-32 bg-neutral-200 rounded-lg"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error && Object.keys(templates).length === 0) {
    return (
      <div className="fixed inset-0 backdrop-blur-md flex items-center justify-center z-50">
        <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4 p-8 text-center">
          <ExclamationTriangleIcon className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-neutral-900 mb-2">Failed to Load Templates</h2>
          <p className="text-neutral-600 mb-6">{error}</p>
          <div className="flex space-x-3">
            <Button onClick={fetchTemplates} className="flex-1">
              Try Again
            </Button>
            <Button onClick={onCancel} variant="outline" className="flex-1">
              Cancel
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 backdrop-blur-md flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl mx-4 max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="border-b border-neutral-200 p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <PuzzlePieceIcon className="w-8 h-8 text-primary-600" />
              <div>
                <h2 className="text-2xl font-bold text-neutral-900">
                  {currentStep === 1 && 'Choose Integration'}
                  {currentStep === 2 && 'Configure Integration'}
                  {currentStep === 3 && 'Integration Complete'}
                </h2>
                <p className="text-neutral-600">
                  {currentStep === 1 && 'Select the service you want to integrate'}
                  {currentStep === 2 && `Set up your ${selectedTemplate?.name} integration`}
                  {currentStep === 3 && 'Your integration is ready to use'}
                </p>
              </div>
            </div>
            <button
              onClick={onCancel}
              className="text-neutral-400 hover:text-neutral-600"
            >
              <XMarkIcon className="w-6 h-6" />
            </button>
          </div>
          
          {/* Step indicator */}
          <div className="flex items-center justify-center mt-6 space-x-8">
            {[1, 2, 3].map((step) => (
              <div key={step} className="flex items-center">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  step <= currentStep
                    ? 'bg-primary-600 text-white'
                    : 'bg-neutral-200 text-neutral-500'
                }`}>
                  {step < currentStep ? (
                    <CheckCircleIcon className="w-5 h-5" />
                  ) : (
                    step
                  )}
                </div>
                {step < 3 && (
                  <div className={`w-16 h-0.5 ml-2 ${
                    step < currentStep ? 'bg-primary-600' : 'bg-neutral-200'
                  }`} />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
          {/* Step 1: Template Selection */}
          {currentStep === 1 && (
            <div className="space-y-8">
              {/* Custom Integration Highlight */}
              <div className="bg-gradient-to-br from-primary-50 to-teal-50 rounded-xl p-6 border border-primary-200">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="font-semibold text-neutral-900">Custom Integration</h3>
                    <p className="text-sm text-neutral-600">Connect any REST API service</p>
                  </div>
                  <span className="bg-green-100 text-green-800 text-xs font-medium px-2 py-1 rounded-full">
                    Flexible
                  </span>
                </div>
                
                <Button
                  onClick={() => templates.custom && handleTemplateSelect(templates.custom)}
                  className="w-full bg-green-200 hover:bg-green-300 text-black"
                  disabled={!templates.custom}
                >
                  <SparklesIcon className="w-4 h-4 mr-2" />
                  Set Up Custom Integration
                </Button>
              </div>

              {/* Popular Integrations */}
              {Object.entries(groupTemplatesByCategory()).map(([category, categoryTemplates]) => {
                if (category === 'custom') return null;
                
                return (
                  <div key={category} className="space-y-4">
                    <h3 className="text-lg font-semibold text-neutral-900 flex items-center">
                      <CloudIcon className="w-5 h-5 mr-2 text-primary-600" />
                      {getCategoryDisplayName(category)}
                    </h3>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {categoryTemplates.map((template) => (
                        <button
                          key={template.id}
                          onClick={() => handleTemplateSelect(template)}
                          className="p-4 border-2 border-neutral-200 rounded-xl hover:border-primary-300 hover:shadow-lg transition-all duration-200 text-left group"
                        >
                          <div className="flex flex-col items-center justify-center space-y-2">
                            <div className="group-hover:scale-110 transition-transform">
                              {(template as any).iconComponent || template.icon}
                            </div>
                            <p className="text-xs text-neutral-600 text-center line-clamp-2">
                              {template.description}
                            </p>
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Step 2: Configuration */}
          {currentStep === 2 && selectedTemplate && (
            <form onSubmit={handleSubmit(handleCredentialSubmit)} className="space-y-6">
              {error && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <ExclamationTriangleIcon className="w-5 h-5 text-red-600 flex-shrink-0" />
                    <span className="text-red-800 text-sm">{error}</span>
                  </div>
                </div>
              )}

              {/* Selected Template Info */}
              <div className="bg-neutral-50 rounded-lg p-4 flex items-center space-x-3">
                <div className="flex-shrink-0">
                  {(selectedTemplate as any).iconComponent || selectedTemplate.icon}
                </div>
                <div>
                  <h3 className="font-medium text-neutral-900">{selectedTemplate.name}</h3>
                  <p className="text-sm text-neutral-600">{selectedTemplate.description}</p>
                </div>
              </div>

              {/* Basic Information */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label htmlFor="name" className="block text-sm font-medium text-neutral-700 mb-2">
                    Integration Name *
                  </label>
                  <input
                    {...register('name')}
                    type="text"
                    id="name"
                    className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    placeholder={`My ${selectedTemplate.name} Integration`}
                  />
                  {errors.name && (
                    <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
                  )}
                </div>

                <div>
                  <label htmlFor="description" className="block text-sm font-medium text-neutral-700 mb-2">
                    Description
                  </label>
                  <input
                    {...register('description')}
                    type="text"
                    id="description"
                    className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    placeholder={`Integration with ${selectedTemplate.name}`}
                  />
                </div>
              </div>

              {/* Authentication Method Selection */}
              {oauthSupport[selectedTemplate.integration_type]?.supports_oauth && (
                <div>
                  <h4 className="text-lg font-medium text-neutral-900 mb-4">
                    Authentication Method
                  </h4>
                  
                  <div className="grid grid-cols-2 gap-4 mb-6">
                    <button
                      type="button"
                      onClick={() => setAuthMethod('oauth')}
                      className={`p-4 border-2 rounded-lg text-left transition-all ${
                        authMethod === 'oauth'
                          ? 'border-primary-500 bg-primary-50'
                          : 'border-neutral-200 hover:border-neutral-300'
                      }`}
                    >
                      <div className="flex items-center space-x-3">
                        <div className={`w-4 h-4 rounded-full border-2 ${
                          authMethod === 'oauth' ? 'border-primary-500 bg-primary-500' : 'border-neutral-300'
                        }`}>
                          {authMethod === 'oauth' && (
                            <div className="w-2 h-2 bg-white rounded-full mx-auto mt-0.5"></div>
                          )}
                        </div>
                        <div>
                          <h5 className="font-medium">OAuth 2.0</h5>
                          <p className="text-sm text-neutral-600">Secure, recommended</p>
                        </div>
                      </div>
                    </button>
                    
                    <button
                      type="button"
                      onClick={() => setAuthMethod('credentials')}
                      className={`p-4 border-2 rounded-lg text-left transition-all ${
                        authMethod === 'credentials'
                          ? 'border-primary-500 bg-primary-50'
                          : 'border-neutral-200 hover:border-neutral-300'
                      }`}
                    >
                      <div className="flex items-center space-x-3">
                        <div className={`w-4 h-4 rounded-full border-2 ${
                          authMethod === 'credentials' ? 'border-primary-500 bg-primary-500' : 'border-neutral-300'
                        }`}>
                          {authMethod === 'credentials' && (
                            <div className="w-2 h-2 bg-white rounded-full mx-auto mt-0.5"></div>
                          )}
                        </div>
                        <div>
                          <h5 className="font-medium">API Credentials</h5>
                          <p className="text-sm text-neutral-600">Direct API access</p>
                        </div>
                      </div>
                    </button>
                  </div>

                  {oauthSupport[selectedTemplate.integration_type]?.oauth_config?.note && (
                    <div className="mb-6 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                      <p className="text-sm text-blue-800">
                        💡 {oauthSupport[selectedTemplate.integration_type].oauth_config?.note}
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* OAuth Configuration */}
              {authMethod === 'oauth' && (
                <div>
                  <h4 className="text-lg font-medium text-neutral-900 mb-4">
                    OAuth Configuration
                  </h4>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    <div>
                      <label htmlFor="client_id" className="block text-sm font-medium text-neutral-700 mb-2">
                        Client ID *
                      </label>
                      <input
                        {...register('client_id' as keyof IntegrationFormData)}
                        type="text"
                        id="client_id"
                        className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                        placeholder="Enter your OAuth client ID"
                      />
                    </div>
                    
                    <div>
                      <label htmlFor="client_secret" className="block text-sm font-medium text-neutral-700 mb-2">
                        Client Secret *
                      </label>
                      <input
                        {...register('client_secret' as keyof IntegrationFormData)}
                        type="password"
                        id="client_secret"
                        className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                        placeholder="Enter your OAuth client secret"
                      />
                    </div>
                  </div>

                  {/* Scopes Selection */}
                  {availableScopes.length > 0 && (
                    <div className="mb-4">
                      <label className="block text-sm font-medium text-neutral-700 mb-2">
                        Permissions (Scopes)
                      </label>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-32 overflow-y-auto p-3 border border-neutral-200 rounded-lg">
                        {availableScopes.map((scope) => (
                          <label key={scope} className="flex items-center space-x-2">
                            <input
                              type="checkbox"
                              checked={scopes.includes(scope)}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setScopes(prev => [...prev, scope]);
                                } else {
                                  setScopes(prev => prev.filter(s => s !== scope));
                                }
                              }}
                              className="rounded border-neutral-300 text-primary-600 focus:ring-primary-500"
                            />
                            <span className="text-sm text-neutral-700">{scope}</span>
                          </label>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Credential Configuration */}
              {authMethod === 'credentials' && (
                <div>
                  <h4 className="text-lg font-medium text-neutral-900 mb-4">
                    API Credentials
                  </h4>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {selectedTemplate.config.required_credentials.map((field) => (
                      <div key={field}>
                        <label htmlFor={field} className="block text-sm font-medium text-neutral-700 mb-2">
                          {field.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')} *
                        </label>
                        <input
                          {...register(field as keyof IntegrationFormData)}
                          type={field.includes('password') || field.includes('secret') || field.includes('token') ? 'password' : 'text'}
                          id={field}
                          className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                          placeholder={`Enter your ${field.replace('_', ' ')}`}
                        />
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Base URL for custom integrations */}
              {selectedTemplate.id === 'custom' && (
                <div>
                  <label htmlFor="base_url" className="block text-sm font-medium text-neutral-700 mb-2">
                    Base URL *
                  </label>
                  <input
                    {...register('base_url')}
                    type="url"
                    id="base_url"
                    className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    placeholder="https://api.example.com"
                  />
                  {errors.base_url && (
                    <p className="mt-1 text-sm text-red-600">{errors.base_url.message}</p>
                  )}
                </div>
              )}

              {/* Documentation Link */}
              {selectedTemplate.documentation_url && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <p className="text-sm text-blue-800">
                    Need help finding these credentials?{' '}
                    <a 
                      href={selectedTemplate.documentation_url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="font-medium underline hover:no-underline"
                    >
                      View {selectedTemplate.name} documentation
                    </a>
                  </p>
                </div>
              )}

              {/* Actions */}
              <div className="flex items-center justify-between pt-6 border-t border-neutral-200">
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => setCurrentStep(1)}
                >
                  <ArrowLeftIcon className="w-4 h-4 mr-2" />
                  Back
                </Button>
                
                <Button
                  type="submit"
                  loading={isTesting}
                  disabled={isTesting}
                >
                  {isTesting ? (
                    authMethod === 'oauth' ? 'Initiating OAuth...' : 'Testing Connection...'
                  ) : (
                    authMethod === 'oauth' ? 'Connect with OAuth' : 'Create & Test Integration'
                  )}
                  {!isTesting && <ArrowRightIcon className="w-4 h-4 ml-2" />}
                </Button>
              </div>
            </form>
          )}

          {/* Step 3: Success */}
          {currentStep === 3 && (
            <div className="text-center py-8">
              <CheckCircleIcon className="w-16 h-16 text-green-500 mx-auto mb-4" />
              <h3 className="text-xl font-bold text-neutral-900 mb-2">Integration Complete!</h3>
              <p className="text-neutral-600 mb-6">
                Your {selectedTemplate?.name} integration has been created and tested successfully.
              </p>
              
              {testResult && (
                <div className={`p-4 rounded-lg mb-6 ${
                  testResult.success 
                    ? 'bg-green-50 border border-green-200' 
                    : 'bg-red-50 border border-red-200'
                }`}>
                  <p className={`text-sm ${
                    testResult.success ? 'text-green-800' : 'text-red-800'
                  }`}>
                    {testResult.message}
                  </p>
                </div>
              )}
              
              <p className="text-sm text-neutral-500">
                You will be redirected to the integrations page shortly...
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}