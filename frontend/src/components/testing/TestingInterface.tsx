'use client';

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/Button';
import { 
  PlayIcon,
  StopIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  ArrowPathIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline';

interface TestResult {
  id: string;
  name: string;
  status: 'pass' | 'fail' | 'running' | 'pending';
  duration?: number;
  error?: string;
  details?: string;
  timestamp: string;
}

interface TestSuite {
  id: string;
  name: string;
  description: string;
  totalTests: number;
  passedTests: number;
  failedTests: number;
  status: 'idle' | 'running' | 'completed' | 'failed';
  results: TestResult[];
}

const mockTestSuites: TestSuite[] = [
  {
    id: 'unit-tests',
    name: 'Unit Tests',
    description: 'Backend and frontend unit tests',
    totalTests: 156,
    passedTests: 156,
    failedTests: 0,
    status: 'completed',
    results: [
      {
        id: 'ut-1',
        name: 'User authentication validation',
        status: 'pass',
        duration: 0.12,
        timestamp: new Date().toISOString()
      },
      {
        id: 'ut-2',
        name: 'Integration model creation',
        status: 'pass',
        duration: 0.08,
        timestamp: new Date().toISOString()
      }
    ]
  },
  {
    id: 'integration-tests',
    name: 'Integration Tests',
    description: 'End-to-end system integration tests',
    totalTests: 23,
    passedTests: 23,
    failedTests: 0,
    status: 'completed',
    results: [
      {
        id: 'it-1',
        name: 'WebSocket chat flow',
        status: 'pass',
        duration: 2.45,
        timestamp: new Date().toISOString()
      },
      {
        id: 'it-2',
        name: 'Kafka event streaming',
        status: 'pass',
        duration: 1.87,
        timestamp: new Date().toISOString()
      }
    ]
  },
  {
    id: 'load-tests',
    name: 'Load Tests',
    description: 'Performance and scalability tests',
    totalTests: 8,
    passedTests: 8,
    failedTests: 0,
    status: 'completed',
    results: [
      {
        id: 'lt-1',
        name: '1000 concurrent users',
        status: 'pass',
        duration: 45.2,
        timestamp: new Date().toISOString()
      },
      {
        id: 'lt-2',
        name: 'High-volume log streaming',
        status: 'pass',
        duration: 32.1,
        timestamp: new Date().toISOString()
      }
    ]
  },
  {
    id: 'security-tests',
    name: 'Security Tests',
    description: 'Authentication and authorization tests',
    totalTests: 15,
    passedTests: 15,
    failedTests: 0,
    status: 'completed',
    results: [
      {
        id: 'st-1',
        name: 'JWT token validation',
        status: 'pass',
        duration: 0.05,
        timestamp: new Date().toISOString()
      },
      {
        id: 'st-2',
        name: 'API key encryption',
        status: 'pass',
        duration: 0.03,
        timestamp: new Date().toISOString()
      }
    ]
  }
];

export default function TestingInterface() {
  const [testSuites, setTestSuites] = useState<TestSuite[]>(mockTestSuites);
  const [runningTests, setRunningTests] = useState<string[]>([]);
  const [selectedSuite, setSelectedSuite] = useState<string | null>(null);
  const [testOutput, setTestOutput] = useState<string>('');

  const runTestSuite = async (suiteId: string) => {
    const suite = testSuites.find(s => s.id === suiteId);
    if (!suite) return;

    // Mark suite as running
    setTestSuites(prev => prev.map(s => 
      s.id === suiteId 
        ? { ...s, status: 'running', results: s.results.map(r => ({ ...r, status: 'pending' })) }
        : s
    ));

    setRunningTests(prev => [...prev, suiteId]);
    setTestOutput(`Starting ${suite.name}...\n`);

    // Simulate test execution
    for (const test of suite.results) {
      await simulateTestExecution(suiteId, test.id);
    }

    // Mark suite as completed
    setTestSuites(prev => prev.map(s => 
      s.id === suiteId 
        ? { ...s, status: 'completed' }
        : s
    ));

    setRunningTests(prev => prev.filter(id => id !== suiteId));
    setTestOutput(prev => prev + `\n${suite.name} completed successfully!\n`);
  };

  const runAllTests = async () => {
    setTestOutput('Starting all test suites...\n');
    
    for (const suite of testSuites) {
      await runTestSuite(suite.id);
    }
    
    setTestOutput(prev => prev + '\nAll tests completed!\n');
  };

  const simulateTestExecution = async (suiteId: string, testId: string) => {
    // Simulate test running
    setTestSuites(prev => prev.map(s => 
      s.id === suiteId 
        ? {
            ...s,
            results: s.results.map(r => 
              r.id === testId ? { ...r, status: 'running' } : r
            )
          }
        : s
    ));

    setTestOutput(prev => prev + `Running test: ${testId}\n`);

    // Simulate execution time
    const executionTime = Math.random() * 2 + 0.5;
    await new Promise(resolve => setTimeout(resolve, executionTime * 1000));

    // Simulate test result (90% pass rate for demo)
    const passed = Math.random() > 0.1;
    const status = passed ? 'pass' : 'fail';
    const error = passed ? undefined : 'Test assertion failed: expected true but got false';

    setTestSuites(prev => prev.map(s => 
      s.id === suiteId 
        ? {
            ...s,
            results: s.results.map(r => 
              r.id === testId 
                ? { 
                    ...r, 
                    status, 
                    duration: executionTime,
                    error,
                    timestamp: new Date().toISOString()
                  } 
                : r
            ),
            passedTests: s.results.filter(r => r.status === 'pass').length,
            failedTests: s.results.filter(r => r.status === 'fail').length
          }
        : s
    ));

    setTestOutput(prev => prev + `${testId}: ${status.toUpperCase()} (${executionTime.toFixed(2)}s)\n`);
  };

  const stopTestSuite = (suiteId: string) => {
    setTestSuites(prev => prev.map(s => 
      s.id === suiteId 
        ? { ...s, status: 'idle' }
        : s
    ));
    setRunningTests(prev => prev.filter(id => id !== suiteId));
    setTestOutput(prev => prev + `Stopped ${suiteId}\n`);
  };

  const clearTestOutput = () => {
    setTestOutput('');
  };

  const exportTestResults = () => {
    const results = testSuites.map(suite => ({
      suite: suite.name,
      status: suite.status,
      total: suite.totalTests,
      passed: suite.passedTests,
      failed: suite.failedTests,
      results: suite.results.map(r => ({
        test: r.name,
        status: r.status,
        duration: r.duration,
        error: r.error
      }))
    }));

    const jsonContent = JSON.stringify(results, null, 2);
    const blob = new Blob([jsonContent], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `test_results_${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pass':
        return <CheckCircleIcon className="h-5 w-5 text-green-600" />;
      case 'fail':
        return <XCircleIcon className="h-5 w-5 text-red-600" />;
      case 'running':
        return <ArrowPathIcon className="h-5 w-5 text-blue-600 animate-spin" />;
      case 'pending':
        return <InformationCircleIcon className="h-5 w-5 text-neutral-400" />;
      default:
        return <InformationCircleIcon className="h-5 w-5 text-neutral-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pass':
        return 'bg-green-50 border-green-200 text-green-800';
      case 'fail':
        return 'bg-red-50 border-red-200 text-red-800';
      case 'running':
        return 'bg-blue-50 border-blue-200 text-blue-800';
      case 'pending':
        return 'bg-neutral-50 border-neutral-200 text-neutral-600';
      default:
        return 'bg-neutral-50 border-neutral-200 text-neutral-600';
    }
  };

  const getSuiteStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-50 border-green-200';
      case 'running':
        return 'bg-blue-50 border-blue-200';
      case 'failed':
        return 'bg-red-50 border-red-200';
      default:
        return 'bg-neutral-50 border-neutral-200';
    }
  };

  const overallStats = testSuites.reduce((acc, suite) => ({
    total: acc.total + suite.totalTests,
    passed: acc.passed + suite.passedTests,
    failed: acc.failed + suite.failedTests
  }), { total: 0, passed: 0, failed: 0 });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-neutral-900">Testing Interface</h1>
          <p className="text-neutral-600 mt-1">Run and monitor all system tests</p>
        </div>
        
        <div className="flex items-center space-x-3">
          <Button
            onClick={runAllTests}
            disabled={runningTests.length > 0}
            leftIcon={<PlayIcon className="h-4 w-4" />}
            size="lg"
          >
            Run All Tests
          </Button>
          
          <Button
            onClick={exportTestResults}
            variant="outline"
            leftIcon={<DocumentTextIcon className="h-4 w-4" />}
          >
            Export Results
          </Button>
        </div>
      </div>

      {/* Overall Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-6 rounded-lg border border-neutral-200 shadow-soft">
          <div className="text-2xl font-bold text-neutral-900">{overallStats.total}</div>
          <div className="text-sm text-neutral-600">Total Tests</div>
        </div>
        
        <div className="bg-white p-6 rounded-lg border border-neutral-200 shadow-soft">
          <div className="text-2xl font-bold text-green-600">{overallStats.passed}</div>
          <div className="text-sm text-neutral-600">Passed</div>
        </div>
        
        <div className="bg-white p-6 rounded-lg border border-neutral-200 shadow-soft">
          <div className="text-2xl font-bold text-red-600">{overallStats.failed}</div>
          <div className="text-sm text-neutral-600">Failed</div>
        </div>
        
        <div className="bg-white p-6 rounded-lg border border-neutral-200 shadow-soft">
          <div className="text-2xl font-bold text-blue-600">
            {overallStats.total > 0 ? Math.round((overallStats.passed / overallStats.total) * 100) : 0}%
          </div>
          <div className="text-sm text-neutral-600">Success Rate</div>
        </div>
      </div>

      {/* Test Suites */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {testSuites.map((suite) => (
          <div
            key={suite.id}
            className={`bg-white rounded-lg border shadow-soft ${getSuiteStatusColor(suite.status)}`}
          >
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-neutral-900">{suite.name}</h3>
                  <p className="text-sm text-neutral-600">{suite.description}</p>
                </div>
                
                <div className="text-right">
                  <div className="text-2xl font-bold text-neutral-900">{suite.passedTests}/{suite.totalTests}</div>
                  <div className="text-sm text-neutral-600">Tests Passed</div>
                </div>
              </div>

              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(suite.status)}`}>
                    {suite.status.toUpperCase()}
                  </span>
                  {suite.failedTests > 0 && (
                    <span className="text-sm text-red-600">
                      {suite.failedTests} failed
                    </span>
                  )}
                </div>

                <div className="flex space-x-2">
                  {suite.status === 'running' ? (
                    <Button
                      onClick={() => stopTestSuite(suite.id)}
                      variant="outline"
                      size="sm"
                      leftIcon={<StopIcon className="h-4 w-4" />}
                    >
                      Stop
                    </Button>
                  ) : (
                    <Button
                      onClick={() => runTestSuite(suite.id)}
                      disabled={runningTests.includes(suite.id)}
                      size="sm"
                      leftIcon={<PlayIcon className="h-4 w-4" />}
                    >
                      Run
                    </Button>
                  )}
                </div>
              </div>

              {/* Test Results */}
              <div className="space-y-2">
                {suite.results.slice(0, 3).map((test) => (
                  <div key={test.id} className="flex items-center justify-between p-2 bg-white rounded border">
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(test.status)}
                      <span className="text-sm text-neutral-700">{test.name}</span>
                    </div>
                    <div className="text-xs text-neutral-500">
                      {test.duration ? `${test.duration.toFixed(2)}s` : '-'}
                    </div>
                  </div>
                ))}
                
                {suite.results.length > 3 && (
                  <div className="text-center text-sm text-neutral-500">
                    +{suite.results.length - 3} more tests
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Test Output */}
      <div className="bg-white rounded-lg border border-neutral-200 shadow-soft">
        <div className="px-6 py-4 border-b border-neutral-200">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-neutral-900">Test Output</h3>
            <Button
              onClick={clearTestOutput}
              variant="outline"
              size="sm"
            >
              Clear
            </Button>
          </div>
        </div>
        
        <div className="p-6">
          <div className="bg-neutral-900 text-green-400 p-4 rounded-lg font-mono text-sm h-64 overflow-y-auto">
            {testOutput || 'No test output yet. Run some tests to see results here.'}
          </div>
        </div>
      </div>

      {/* Detailed Results */}
      {selectedSuite && (
        <div className="bg-white rounded-lg border border-neutral-200 shadow-soft">
          <div className="px-6 py-4 border-b border-neutral-200">
            <h3 className="text-lg font-medium text-neutral-900">
              Detailed Results: {testSuites.find(s => s.id === selectedSuite)?.name}
            </h3>
          </div>
          
          <div className="p-6">
            <div className="space-y-2">
              {testSuites.find(s => s.id === selectedSuite)?.results.map((test) => (
                <div key={test.id} className="flex items-center justify-between p-3 bg-neutral-50 rounded border">
                  <div className="flex items-center space-x-3">
                    {getStatusIcon(test.status)}
                    <div>
                      <div className="font-medium text-neutral-900">{test.name}</div>
                      {test.error && (
                        <div className="text-sm text-red-600">{test.error}</div>
                      )}
                    </div>
                  </div>
                  <div className="text-sm text-neutral-500">
                    {test.duration ? `${test.duration.toFixed(2)}s` : '-'}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
