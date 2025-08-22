'use client';

import React, { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
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
  { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
  { name: 'Integrations', href: '/integrations', icon: PuzzlePieceIcon },
  { name: 'Chat', href: '/chat', icon: ChatBubbleLeftRightIcon },
  { name: 'Analytics', href: '/analytics', icon: ChartBarIcon },
  { name: 'Admin', href: '/admin', icon: CogIcon },
  { name: 'Checklist', href: '/checklist', icon: CheckCircleIcon },
  { name: 'Team', href: '/team', icon: UserGroupIcon },
];

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { user, logout } = useAuth();
  const pathname = usePathname();

  const handleLogout = () => {
    logout();
    window.location.href = '/login';
  };

  return (
    <div className="min-h-screen bg-white">
      {/* Mobile sidebar */}
      <div className={cn(
        "fixed inset-0 z-50 lg:hidden",
        sidebarOpen ? "block" : "hidden"
      )}>
        <div className="fixed inset-0 bg-neutral-900/80" onClick={() => setSidebarOpen(false)} />
        <div className="fixed inset-y-0 left-0 w-64 bg-neutral-900 shadow-xl">
          <div className="flex h-full flex-col">
            <div className="flex h-16 items-center justify-between px-6 border-b border-neutral-700">
              <div className="flex items-center">
                <div className="h-8 w-8 bg-gradient-to-br from-primary-500 to-teal-500 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">BS</span>
                </div>
                <span className="ml-3 text-lg font-semibold text-white">
                  Business Systems
                </span>
              </div>
              <button
                type="button"
                className="text-neutral-400 hover:text-white"
                onClick={() => setSidebarOpen(false)}
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>
            <nav className="flex-1 space-y-1 px-3 py-4">
              {navigation.map((item) => {
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={cn(
                      isActive
                        ? 'bg-primary-50 text-primary-700 border-r-2 border-primary-600'
                        : 'text-white hover:bg-neutral-50 hover:text-neutral-900',
                      'group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors'
                    )}
                  >
                    <item.icon
                      className={cn(
                        isActive ? 'text-primary-600' : 'text-white group-hover:text-neutral-500',
                        'mr-3 h-5 w-5 flex-shrink-0'
                      )}
                    />
                    {item.name}
                  </Link>
                );
              })}
            </nav>
            
            {/* User info and logout at bottom */}
            <div className="p-3 border-t border-neutral-700">
              <div className="flex items-center space-x-3 mb-3">
                <div className="text-sm flex-1">
                  <div className="font-medium text-white">{user?.full_name || user?.username}</div>
                  <div className="text-neutral-300 text-xs">{user?.email}</div>
                </div>
              </div>
              <button
                onClick={handleLogout}
                className="w-full rounded-md bg-neutral-700 px-3 py-2 text-sm font-medium text-white shadow-sm hover:bg-neutral-600 transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Desktop sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:z-50 lg:flex lg:w-64 lg:flex-col">
        <div className="flex flex-col flex-grow bg-neutral-900 border-r border-neutral-700">
          <div className="flex h-16 items-center px-6 border-b border-neutral-700">
            <div className="flex items-center">
              <div className="h-8 w-8 bg-gradient-to-br from-primary-500 to-teal-500 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">BS</span>
              </div>
              <span className="ml-3 text-lg font-semibold text-white">
                Business Systems
              </span>
            </div>
          </div>
          <nav className="flex-1 space-y-1 px-3 py-4">
            {navigation.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    isActive
                      ? 'bg-primary-50 text-primary-700 border-r-2 border-primary-600'
                      : 'text-white hover:bg-neutral-50 hover:text-neutral-900',
                    'group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors'
                  )}
                >
                  <item.icon
                    className={cn(
                      isActive ? 'text-primary-600' : 'text-white group-hover:text-neutral-500',
                      'mr-3 h-5 w-5 flex-shrink-0'
                    )}
                  />
                  {item.name}
                </Link>
              );
            })}
          </nav>
          
          {/* User info and logout at bottom */}
          <div className="p-3 border-t border-neutral-700">
            <div className="flex items-center space-x-3 mb-3">
              <div className="text-sm flex-1">
                <div className="font-medium text-white">{user?.full_name || user?.username}</div>
                <div className="text-neutral-300 text-xs">{user?.email}</div>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="w-full rounded-md bg-neutral-700 px-3 py-2 text-sm font-medium text-white shadow-sm hover:bg-neutral-600 transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Mobile menu button - only visible on mobile */}
        <div className="lg:hidden sticky top-0 z-40 flex h-16 shrink-0 items-center gap-x-4 border-b border-neutral-200 bg-white px-4 shadow-sm">
          <button
            type="button"
            className="-m-2.5 p-2.5 text-neutral-700"
            onClick={() => setSidebarOpen(true)}
          >
            <Bars3Icon className="h-6 w-6" />
          </button>
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
