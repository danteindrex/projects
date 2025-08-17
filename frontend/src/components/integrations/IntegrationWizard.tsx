'use client';

import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/Button';
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
  integration_type: z.enum(['jira', 'zendesk', 'salesforce', 'github', 'custom']),
  base_url: z.string().url('Please enter a valid URL'),
  api_key: z.string().min(1, 'API key is required'),
  username: z.string().optional(),
  password: z.string().optional(),
  config: z.record(z.any()).optional(),
});

type IntegrationFormData = z.infer<typeof integrationSchema>;

interface IntegrationTemplate {
  id: string;
  name: string;
  description: string;
  icon: string;
  fields: string[];
  config: Record<string, any>;
}

const integrationTemplates: IntegrationTemplate[] = [
  {
    id: 'jira',
    name: 'Jira',
    description: 'Connect to Jira for issue tracking and project management',
    icon: '🎯',
    fields: ['base_url', 'api_key', 'username'],
    config: {
      endpoints: {
        issues: '/rest/api/2/issue',
        projects: '/rest/api/2/project',
        users: '/rest/api/2/user'
      }
    }
  },
  {
    id: 'zendesk',
    name: 'Zendesk',
    description: 'Connect to Zendesk for customer support ticket management',
    icon: '🎫',
    fields: ['base_url', 'api_key', 'username'],
    config: {
      endpoints: {
        tickets: '/api/v2/tickets',
        users: '/api/v2/users',
        organizations: '/api/v2/organizations'
      }
    }
  },
  {
    id: 'salesforce',
    name: 'Salesforce',
    description: 'Connect to Salesforce for CRM and sales data',
    icon: '☁️',
    fields: ['base_url', 'api_key', 'username', 'password'],
    config: {
      endpoints: {
        leads: '/services/data/v52.0/sobjects/Lead',
        contacts: '/services/data/v52.0/sobjects/Contact',
        opportunities: '/services/data/v52.0/sobjects/Opportunity'
      }
    }
  },
  {
    id: 'github',
    name: 'GitHub',
    description: 'Connect to GitHub for repository and issue management',
    icon: '🐙',
    fields: ['base_url', 'api_key'],
    config: {
      endpoints: {
        repos: '/user/repos',
        issues: '/repos/{owner}/{repo}/issues',
        pull_requests: '/repos/{owner}/{repo}/pulls'
      }
    }
  },
  {
    id: 'custom',
    name: 'Custom API',
    description: 'Connect to any custom API endpoint',
    icon: '🔌',
    fields: ['base_url', 'api_key'],
    config: {}
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
    
    try {
      // Simulate API test
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Mock test result
      const success = Math.random() > 0.3; // 70% success rate for demo
      setTestResult({
        success,
        message: success 
          ? 'Connection successful! Integration is ready to use.'
          : 'Connection failed. Please check your credentials and try again.'
      });
      
      if (success) {
        setCurrentStep(4);
      }
    } catch (error) {
      setTestResult({
        success: false,
        message: 'An error occurred while testing the connection.'
      });
    } finally {
      setIsTesting(false);
    }
  };

  const handleFormSubmit = (data: IntegrationFormData) => {
    if (currentStep === 2) {
      setCurrentStep(3);
    } else if (currentStep === 3) {
      handleTestConnection(data);
    } else if (currentStep === 4) {
      onComplete(data);
    }
  };

  const goBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const renderStep1 = () => (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-neutral-900">Choose Integration Type</h2>
        <p className="text-neutral-600 mt-2">Select the type of system you want to connect</p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {integrationTemplates.map((template) => (
          <button
            key={template.id}
            onClick={() => handleTemplateSelect(template)}
            className="p-6 border border-neutral-200 rounded-lg hover:border-primary-300 hover:shadow-soft transition-all text-left"
          >
            <div className="flex items-center space-x-3 mb-3">
              <span className="text-2xl">{template.icon}</span>
              <h3 className="font-semibold text-neutral-900">{template.name}</h3>
            </div>
            <p className="text-sm text-neutral-600">{template.description}</p>
          </button>
        ))}
      </div>
    </div>
  );

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
            className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 ${
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
            className="w-full px-3 py-2 border border-neutral-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            placeholder="Describe what this integration is for..."
          />
        </div>

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

        <div>
          <label htmlFor="api_key" className="block text-sm font-medium text-neutral-700 mb-2">
            API Key / Token
          </label>
          <input
            {...register('api_key')}
            type="password"
            id="api_key"
            className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 ${
              errors.api_key ? 'border-red-300' : 'border-neutral-300'
            }`}
            placeholder="Enter your API key or token"
          />
          {errors.api_key && (
            <p className="mt-1 text-sm text-red-600">{errors.api_key.message}</p>
          )}
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
              className="w-full px-3 py-2 border border-neutral-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
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
              className="w-full px-3 py-2 border border-neutral-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              placeholder="Enter your password"
            />
          </div>
        )}

        <div className="flex justify-between pt-4">
          <Button
            type="button"
            variant="outline"
            onClick={goBack}
            leftIcon={<ArrowLeftIcon className="h-4 w-4" />}
          >
            Back
          </Button>
          <Button
            type="submit"
            disabled={!isValid}
            rightIcon={<ArrowRightIcon className="h-4 w-4" />}
          >
            Continue
          </Button>
        </div>
      </form>
    </div>
  );

  const renderStep3 = () => (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-neutral-900">Test Connection</h2>
        <p className="text-neutral-600 mt-2">Let's verify your integration works before saving</p>
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
      
      <div className="flex justify-between pt-4">
        <Button
          type="button"
          variant="outline"
          onClick={goBack}
          leftIcon={<ArrowLeftIcon className="h-4 w-4" />}
        >
          Back
        </Button>
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
    <div className="max-w-2xl mx-auto">
      <div className="bg-white shadow-soft rounded-lg border border-neutral-200">
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
        <div className="px-6 py-8">
          {renderCurrentStep()}
        </div>
      </div>
    </div>
  );
}
