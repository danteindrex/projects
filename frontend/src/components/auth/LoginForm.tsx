'use client';

import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/Button';
import { EyeIcon, EyeSlashIcon } from '@heroicons/react/24/outline';

const loginSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  password: z.string().min(1, 'Password is required'),
});

type LoginFormData = z.infer<typeof loginSchema>;

interface LoginFormProps {
  onSubmit: (data: LoginFormData) => void;
  isLoading?: boolean;
  error?: string;
}

export default function LoginForm({ onSubmit, isLoading = false, error }: LoginFormProps) {
  const [showPassword, setShowPassword] = useState(false);
  
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  const handleFormSubmit = (data: LoginFormData) => {
    onSubmit(data);
  };

  return (
    <div className="w-full max-w-md mx-auto">
      <div className="bg-white py-8 px-6 shadow-soft rounded-lg border border-neutral-200">
        <div className="text-center mb-8">
          <div className="mx-auto h-12 w-12 bg-gradient-to-br from-primary-500 to-teal-500 rounded-lg flex items-center justify-center mb-4">
            <span className="text-white font-bold text-xl">BS</span>
          </div>
          <h2 className="text-2xl font-bold text-neutral-900">Welcome back</h2>
          <p className="text-neutral-600 mt-2">Sign in to your account</p>
        </div>

        <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          <div>
            <label htmlFor="email" className="block text-sm font-medium text-neutral-700 mb-2">
              Email address
            </label>
            <input
              {...register('email')}
              type="email"
              id="email"
              className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 ${
                errors.email ? 'border-red-300' : 'border-neutral-300'
              }`}
              placeholder="Enter your email"
            />
            {errors.email && (
              <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-neutral-700 mb-2">
              Password
            </label>
            <div className="relative">
              <input
                {...register('password')}
                type={showPassword ? 'text' : 'password'}
                id="password"
                className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 pr-10 ${
                  errors.password ? 'border-red-300' : 'border-neutral-300'
                }`}
                placeholder="Enter your password"
              />
              <button
                type="button"
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? (
                  <EyeSlashIcon className="h-5 w-5 text-neutral-400" />
                ) : (
                  <EyeIcon className="h-5 w-5 text-neutral-400" />
                )}
              </button>
            </div>
            {errors.password && (
              <p className="mt-1 text-sm text-red-600">{errors.password.message}</p>
            )}
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <input
                id="remember-me"
                name="remember-me"
                type="checkbox"
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-neutral-300 rounded"
              />
              <label htmlFor="remember-me" className="ml-2 block text-sm text-neutral-700">
                Remember me
              </label>
            </div>
            <a
              href="#"
              className="text-sm text-primary-600 hover:text-primary-500"
            >
              Forgot password?
            </a>
          </div>

          <Button
            type="submit"
            className="w-full"
            loading={isLoading}
            disabled={isLoading}
          >
            {isLoading ? 'Signing in...' : 'Sign in'}
          </Button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-sm text-neutral-600">
            Don't have an account?{' '}
            <a href="/register" className="font-medium text-primary-600 hover:text-primary-500">
              Sign up
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}
