'use client';

import React from 'react';
import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XCircleIcon,
  ClockIcon,
  EyeSlashIcon,
  SignalIcon,
  WifiIcon,
  SignalSlashIcon
} from '@heroicons/react/24/outline';

interface IntegrationStatusBadgeProps {
  status: 'active' | 'error' | 'testing' | 'inactive';
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
  showPulse?: boolean;
  className?: string;
}

export function IntegrationStatusBadge({ 
  status, 
  size = 'md', 
  showIcon = true, 
  showPulse = true,
  className = '' 
}: IntegrationStatusBadgeProps) {
  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'active':
        return {
          label: 'Active',
          color: 'bg-green-100 text-green-800 border-green-300 shadow-sm',
          icon: CheckCircleIcon,
          pulseColor: 'bg-green-500'
        };
      case 'error':
        return {
          label: 'Error',
          color: 'bg-red-100 text-red-800 border-red-300 shadow-sm',
          icon: XCircleIcon,
          pulseColor: 'bg-red-500'
        };
      case 'testing':
        return {
          label: 'Testing',
          color: 'bg-yellow-100 text-yellow-800 border-yellow-300 shadow-sm',
          icon: ClockIcon,
          pulseColor: 'bg-yellow-500'
        };
      case 'inactive':
        return {
          label: 'Inactive',
          color: 'bg-gray-100 text-gray-800 border-gray-300 shadow-sm',
          icon: EyeSlashIcon,
          pulseColor: 'bg-gray-500'
        };
      default:
        return {
          label: 'Unknown',
          color: 'bg-gray-100 text-gray-800 border-gray-300 shadow-sm',
          icon: ExclamationTriangleIcon,
          pulseColor: 'bg-gray-500'
        };
    }
  };

  const getSizeClasses = (size: string) => {
    switch (size) {
      case 'sm':
        return 'px-2 py-1 text-xs';
      case 'lg':
        return 'px-4 py-2 text-base';
      default:
        return 'px-3 py-1 text-sm';
    }
  };

  const getIconSize = (size: string) => {
    switch (size) {
      case 'sm':
        return 'h-3 w-3';
      case 'lg':
        return 'h-5 w-5';
      default:
        return 'h-4 w-4';
    }
  };

  const config = getStatusConfig(status);
  const StatusIcon = config.icon;

  return (
    <span className={`
      inline-flex items-center space-x-1.5 font-semibold rounded-full border-2 transition-all duration-200
      ${config.color}
      ${getSizeClasses(size)}
      ${className}
    `}>
      {showIcon && (
        <StatusIcon className={getIconSize(size)} />
      )}
      <span>{config.label}</span>
      {showPulse && status === 'active' && (
        <div className={`w-2 h-2 ${config.pulseColor} rounded-full animate-pulse`}></div>
      )}
    </span>
  );
}

interface ConnectivityIndicatorProps {
  isConnected: boolean;
  responseTime?: number;
  className?: string;
}

export function ConnectivityIndicator({ 
  isConnected, 
  responseTime, 
  className = '' 
}: ConnectivityIndicatorProps) {
  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      {isConnected ? (
        <WifiIcon className="h-4 w-4 text-green-600" />
      ) : (
        <SignalSlashIcon className="h-4 w-4 text-red-600" />
      )}
      
      <div className="flex items-center space-x-1 text-sm">
        <span className={isConnected ? 'text-green-700' : 'text-red-700'}>
          {isConnected ? 'Connected' : 'Disconnected'}
        </span>
        
        {isConnected && responseTime && (
          <span className="text-neutral-500">
            · {responseTime}ms
          </span>
        )}
      </div>
      
      {isConnected && (
        <div className="flex space-x-0.5">
          {[...Array(4)].map((_, i) => (
            <div
              key={i}
              className={`w-1 rounded-full ${
                responseTime && responseTime < 100 ? 'bg-green-500' :
                responseTime && responseTime < 300 ? 'bg-yellow-500' :
                'bg-red-500'
              }`}
              style={{
                height: `${4 + i * 2}px`,
                opacity: responseTime && responseTime < (100 + i * 100) ? 1 : 0.3
              }}
            />
          ))}
        </div>
      )}
    </div>
  );
}

interface HealthScoreProps {
  score: number; // 0-100
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  className?: string;
}

export function HealthScore({ 
  score, 
  size = 'md', 
  showLabel = true, 
  className = '' 
}: HealthScoreProps) {
  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-700 bg-green-100';
    if (score >= 70) return 'text-yellow-700 bg-yellow-100';
    if (score >= 50) return 'text-orange-700 bg-orange-100';
    return 'text-red-700 bg-red-100';
  };

  const getProgressColor = (score: number) => {
    if (score >= 90) return 'bg-green-500';
    if (score >= 70) return 'bg-yellow-500';
    if (score >= 50) return 'bg-orange-500';
    return 'bg-red-500';
  };

  const getSizeClasses = (size: string) => {
    switch (size) {
      case 'sm':
        return {
          container: 'w-16 h-16',
          text: 'text-xs',
          stroke: '3'
        };
      case 'lg':
        return {
          container: 'w-24 h-24',
          text: 'text-lg',
          stroke: '4'
        };
      default:
        return {
          container: 'w-20 h-20',
          text: 'text-base',
          stroke: '3'
        };
    }
  };

  const sizeClasses = getSizeClasses(size);
  const radius = size === 'sm' ? 28 : size === 'lg' ? 40 : 32;
  const circumference = 2 * Math.PI * radius;
  const strokeDasharray = circumference;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  return (
    <div className={`relative ${sizeClasses.container} ${className}`}>
      {/* Background circle */}
      <svg className="w-full h-full transform -rotate-90">
        <circle
          cx="50%"
          cy="50%"
          r={radius}
          stroke="currentColor"
          strokeWidth={sizeClasses.stroke}
          fill="none"
          className="text-neutral-200"
        />
        {/* Progress circle */}
        <circle
          cx="50%"
          cy="50%"
          r={radius}
          stroke="currentColor"
          strokeWidth={sizeClasses.stroke}
          fill="none"
          strokeLinecap="round"
          strokeDasharray={strokeDasharray}
          strokeDashoffset={strokeDashoffset}
          className={getProgressColor(score).replace('bg-', 'text-')}
          style={{
            transition: 'stroke-dashoffset 0.5s ease-in-out'
          }}
        />
      </svg>
      
      {/* Score text */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="text-center">
          <div className={`font-bold ${sizeClasses.text} ${getScoreColor(score).split(' ')[0]}`}>
            {score}%
          </div>
          {showLabel && size !== 'sm' && (
            <div className="text-xs text-neutral-500 mt-0.5">Health</div>
          )}
        </div>
      </div>
    </div>
  );
}