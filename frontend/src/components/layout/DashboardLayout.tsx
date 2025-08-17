'use client';

import React, { useState } from 'react';
import { 
  Bars3Icon, 
  XMarkIcon, 
  HomeIcon, 
  CogIcon, 
  ChatBubbleLeftRightIcon,
  ChartBarIcon,
  PuzzlePieceIcon,
  UserGroupIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';
import { cn } from '@/lib/utils';

interface DashboardLayoutProps {
  children: React.ReactNode;
}

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: HomeIcon, current: true },
  { name: 'Integrations', href: '/integrations', icon: PuzzlePieceIcon, current: false },
  { name: 'Chat', href: '/chat', icon: ChatBubbleLeftRightIcon, current: false },
  { name: 'Analytics', href: '/analytics', icon: ChartBarIcon, current: false },
  { name: 'Admin', href: '/admin', icon: CogIcon, current: false },
  { name: 'Checklist', href: '/checklist', icon: CheckCircleIcon, current: false },
  { name: 'Team', href: '/team', icon: UserGroupIcon, current: false },
];

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-white">
      {/* Mobile sidebar */}
      <div className={cn(
        "fixed inset-0 z-50 lg:hidden",
        sidebarOpen ? "block" : "hidden"
      )}>
        <div className="fixed inset-0 bg-neutral-900/80" onClick={() => setSidebarOpen(false)} />
        <div className="fixed inset-y-0 left-0 w-64 bg-white shadow-xl">
          <div className="flex h-full flex-col">
            <div className="flex h-16 items-center justify-between px-6 border-b border-neutral-200">
              <div className="flex items-center">
                <div className="h-8 w-8 bg-gradient-to-br from-primary-500 to-teal-500 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">BS</span>
                </div>
                <span className="ml-3 text-lg font-semibold text-neutral-900">
                  Business Systems
                </span>
              </div>
              <button
                type="button"
                className="text-neutral-400 hover:text-neutral-600"
                onClick={() => setSidebarOpen(false)}
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>
            <nav className="flex-1 space-y-1 px-3 py-4">
              {navigation.map((item) => (
                <a
                  key={item.name}
                  href={item.href}
                  className={cn(
                    item.current
                      ? 'bg-primary-50 text-primary-700 border-r-2 border-primary-600'
                      : 'text-neutral-600 hover:bg-neutral-50 hover:text-neutral-900',
                    'group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors'
                  )}
                >
                  <item.icon
                    className={cn(
                      item.current ? 'text-primary-600' : 'text-neutral-400 group-hover:text-neutral-500',
                      'mr-3 h-5 w-5 flex-shrink-0'
                    )}
                  />
                  {item.name}
                </a>
              ))}
            </nav>
          </div>
        </div>
      </div>

      {/* Desktop sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:z-50 lg:flex lg:w-64 lg:flex-col">
        <div className="flex flex-col flex-grow bg-white border-r border-neutral-200">
          <div className="flex h-16 items-center px-6 border-b border-neutral-200">
            <div className="flex items-center">
              <div className="h-8 w-8 bg-gradient-to-br from-primary-500 to-teal-500 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">BS</span>
              </div>
              <span className="ml-3 text-lg font-semibold text-neutral-900">
                Business Systems
              </span>
            </div>
          </div>
          <nav className="flex-1 space-y-1 px-3 py-4">
            {navigation.map((item) => (
              <a
                key={item.name}
                href={item.href}
                className={cn(
                  item.current
                    ? 'bg-primary-50 text-primary-700 border-r-2 border-primary-600'
                    : 'text-neutral-600 hover:bg-neutral-50 hover:text-neutral-900',
                  'group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors'
                )}
              >
                <item.icon
                  className={cn(
                    item.current ? 'text-primary-600' : 'text-neutral-400 group-hover:text-neutral-500',
                    'mr-3 h-5 w-5 flex-shrink-0'
                  )}
                />
                {item.name}
              </a>
            ))}
          </nav>
        </div>
      </div>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Top bar */}
        <div className="sticky top-0 z-40 flex h-16 shrink-0 items-center gap-x-4 border-b border-neutral-200 bg-white px-4 shadow-sm sm:gap-x-6 sm:px-6 lg:px-8">
          <button
            type="button"
            className="-m-2.5 p-2.5 text-neutral-700 lg:hidden"
            onClick={() => setSidebarOpen(true)}
          >
            <Bars3Icon className="h-6 w-6" />
          </button>

          <div className="flex flex-1 gap-x-4 self-stretch lg:gap-x-6">
            <div className="flex flex-1 items-center">
              <h1 className="text-lg font-semibold text-neutral-900">
                Dashboard
              </h1>
            </div>
            <div className="flex items-center gap-x-4 lg:gap-x-6">
              {/* Add user menu, notifications, etc. here */}
            </div>
          </div>
        </div>

        {/* Page content */}
        <main className="py-6">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
