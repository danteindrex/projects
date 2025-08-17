import React from 'react';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { 
  ChartBarIcon, 
  PuzzlePieceIcon, 
  ChatBubbleLeftRightIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ClockIcon
} from '@heroicons/react/24/outline';

export default function DashboardPage() {
  // Mock data - replace with real data from API
  const stats = [
    { name: 'Active Integrations', value: '12', change: '+2', changeType: 'positive', icon: PuzzlePieceIcon },
    { name: 'Chat Sessions', value: '89', change: '+12', changeType: 'positive', icon: ChatBubbleLeftRightIcon },
    { name: 'System Health', value: '98%', change: '+1%', changeType: 'positive', icon: CheckCircleIcon },
    { name: 'Pending Tasks', value: '5', change: '-2', changeType: 'negative', icon: ClockIcon },
  ];

  const recentActivity = [
    { id: 1, type: 'integration', message: 'Jira integration updated successfully', time: '2 minutes ago', status: 'success' },
    { id: 2, type: 'chat', message: 'New chat session started', time: '5 minutes ago', status: 'info' },
    { id: 3, type: 'system', message: 'System health check completed', time: '10 minutes ago', status: 'success' },
    { id: 4, type: 'warning', message: 'Zendesk integration experiencing delays', time: '15 minutes ago', status: 'warning' },
  ];

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Page header */}
        <div>
          <h1 className="text-2xl font-bold text-neutral-900">Dashboard</h1>
          <p className="mt-2 text-sm text-neutral-600">
            Welcome back! Here's what's happening with your business systems.
          </p>
        </div>

        {/* Stats grid */}
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {stats.map((stat) => (
            <div
              key={stat.name}
              className="relative overflow-hidden rounded-lg bg-white px-4 py-5 shadow-soft border border-neutral-200"
            >
              <dt>
                <div className="absolute rounded-md bg-primary-500 p-3">
                  <stat.icon className="h-6 w-6 text-white" />
                </div>
                <p className="ml-16 truncate text-sm font-medium text-neutral-600">
                  {stat.name}
                </p>
              </dt>
              <dd className="ml-16 flex items-baseline">
                <p className="text-2xl font-semibold text-neutral-900">{stat.value}</p>
                <p
                  className={`ml-2 flex items-baseline text-sm font-semibold ${
                    stat.changeType === 'positive' ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  {stat.change}
                </p>
              </dd>
            </div>
          ))}
        </div>

        {/* Quick actions */}
        <div className="bg-white shadow-soft rounded-lg border border-neutral-200">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg font-medium leading-6 text-neutral-900 mb-4">
              Quick Actions
            </h3>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <button className="flex items-center p-4 border border-neutral-200 rounded-lg hover:bg-neutral-50 transition-colors">
                <PuzzlePieceIcon className="h-8 w-8 text-primary-600 mr-3" />
                <div className="text-left">
                  <p className="font-medium text-neutral-900">Add Integration</p>
                  <p className="text-sm text-neutral-600">Connect a new business system</p>
                </div>
              </button>
              
              <button className="flex items-center p-4 border border-neutral-200 rounded-lg hover:bg-neutral-50 transition-colors">
                <ChatBubbleLeftRightIcon className="h-8 w-8 text-teal-600 mr-3" />
                <div className="text-left">
                  <p className="font-medium text-neutral-900">Start Chat</p>
                  <p className="text-sm text-neutral-600">Ask about your systems</p>
                </div>
              </button>
              
              <button className="flex items-center p-4 border border-neutral-200 rounded-lg hover:bg-neutral-50 transition-colors">
                <CheckCircleIcon className="h-8 w-8 text-green-600 mr-3" />
                <div className="text-left">
                  <p className="font-medium text-neutral-900">Run Checklist</p>
                  <p className="text-sm text-neutral-600">Verify system readiness</p>
                </div>
              </button>
            </div>
          </div>
        </div>

        {/* Recent activity */}
        <div className="bg-white shadow-soft rounded-lg border border-neutral-200">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg font-medium leading-6 text-neutral-900 mb-4">
              Recent Activity
            </h3>
            <div className="flow-root">
              <ul className="-mb-8">
                {recentActivity.map((activity, activityIdx) => (
                  <li key={activity.id}>
                    <div className="relative pb-8">
                      {activityIdx !== recentActivity.length - 1 ? (
                        <span
                          className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-neutral-200"
                          aria-hidden="true"
                        />
                      ) : null}
                      <div className="relative flex space-x-3">
                        <div>
                          <span
                            className={`h-8 w-8 rounded-full flex items-center justify-center ring-8 ring-white ${
                              activity.status === 'success'
                                ? 'bg-green-500'
                                : activity.status === 'warning'
                                ? 'bg-yellow-500'
                                : 'bg-blue-500'
                            }`}
                          >
                            {activity.status === 'success' && <CheckCircleIcon className="h-5 w-5 text-white" />}
                            {activity.status === 'warning' && <ExclamationTriangleIcon className="h-5 w-5 text-white" />}
                            {activity.status === 'info' && <ChatBubbleLeftRightIcon className="h-5 w-5 text-white" />}
                          </span>
                        </div>
                        <div className="flex min-w-0 flex-1 justify-between space-x-4 pt-1.5">
                          <div>
                            <p className="text-sm text-neutral-900">{activity.message}</p>
                          </div>
                          <div className="whitespace-nowrap text-right text-sm text-neutral-500">
                            {activity.time}
                          </div>
                        </div>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
