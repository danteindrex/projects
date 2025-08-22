'use client';

import React, { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api';
import { 
  UserGroupIcon,
  BanknotesIcon,
  TrophyIcon,
  ExclamationCircleIcon,
  ChartPieIcon,
  BuildingOfficeIcon
} from '@heroicons/react/24/outline';

interface SalesforceAnalyticsProps {
  integrationId: number;
  integrationName: string;
}

export default function SalesforceAnalytics({ integrationId, integrationName }: SalesforceAnalyticsProps) {
  const [accounts, setAccounts] = useState<any[]>([]);
  const [opportunities, setOpportunities] = useState<any[]>([]);
  const [leads, setLeads] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadSalesforceData();
  }, [integrationId]);

  const loadSalesforceData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [accountsResponse, opportunitiesResponse, leadsResponse] = await Promise.allSettled([
        apiClient.getSalesforceAccounts(integrationId),
        apiClient.getSalesforceOpportunities(integrationId),
        apiClient.getSalesforceLeads(integrationId)
      ]);

      if (accountsResponse.status === 'fulfilled') {
        if (!accountsResponse.value.data) {
          throw new Error('Salesforce accounts data not available');
        }
        setAccounts(accountsResponse.value.data);
      } else {
        throw new Error('Failed to load Salesforce accounts');
      }

      if (opportunitiesResponse.status === 'fulfilled') {
        if (!opportunitiesResponse.value.data) {
          throw new Error('Salesforce opportunities data not available');
        }
        setOpportunities(opportunitiesResponse.value.data);
      } else {
        throw new Error('Failed to load Salesforce opportunities');
      }

      if (leadsResponse.status === 'fulfilled') {
        if (!leadsResponse.value.data) {
          throw new Error('Salesforce leads data not available');
        }
        setLeads(leadsResponse.value.data);
      } else {
        throw new Error('Failed to load Salesforce leads');
      }
    } catch (err) {
      setError('Error loading Salesforce analytics');
      console.error('Salesforce analytics error:', err);
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

  const openOpportunities = opportunities.filter(opp => opp.StageName !== 'Closed Won' && opp.StageName !== 'Closed Lost');
  const wonOpportunities = opportunities.filter(opp => opp.StageName === 'Closed Won');
  const qualifiedLeads = leads.filter(lead => lead.Status === 'Qualified');
  const totalOpportunityValue = opportunities.reduce((sum, opp) => sum + (opp.Amount || 0), 0);

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-neutral-50 rounded-lg p-4 border border-neutral-200">
          <div className="flex items-center space-x-2">
            <BuildingOfficeIcon className="h-5 w-5 text-neutral-600" />
            <div>
              <p className="text-sm font-medium text-neutral-700">Accounts</p>
              <p className="text-xl font-bold text-neutral-900">{accounts.length}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-neutral-50 rounded-lg p-4 border border-neutral-200">
          <div className="flex items-center space-x-2">
            <ChartPieIcon className="h-5 w-5 text-neutral-600" />
            <div>
              <p className="text-sm font-medium text-neutral-700">Open Opportunities</p>
              <p className="text-xl font-bold text-neutral-900">{openOpportunities.length}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-neutral-50 rounded-lg p-4 border border-neutral-200">
          <div className="flex items-center space-x-2">
            <UserGroupIcon className="h-5 w-5 text-neutral-600" />
            <div>
              <p className="text-sm font-medium text-neutral-700">Qualified Leads</p>
              <p className="text-xl font-bold text-neutral-900">{qualifiedLeads.length}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-neutral-50 rounded-lg p-4 border border-neutral-200">
          <div className="flex items-center space-x-2">
            <BanknotesIcon className="h-5 w-5 text-neutral-600" />
            <div>
              <p className="text-sm font-medium text-neutral-700">Pipeline Value</p>
              <p className="text-xl font-bold text-neutral-900">${totalOpportunityValue.toLocaleString()}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Opportunities */}
      <div>
        <h3 className="text-lg font-medium text-neutral-900 mb-4 flex items-center space-x-2">
          <TrophyIcon className="h-5 w-5" />
          <span>Recent Opportunities</span>
        </h3>
        {opportunities.length > 0 ? (
          <div className="space-y-3">
            {opportunities
              .sort((a, b) => new Date(b.CreatedDate).getTime() - new Date(a.CreatedDate).getTime())
              .slice(0, 8)
              .map((opportunity) => (
                <div key={opportunity.Id} className="bg-white border border-neutral-200 rounded-lg p-4 hover:shadow-sm transition-shadow">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <span className="inline-flex px-2 py-1 rounded-full text-xs font-medium bg-neutral-100 text-neutral-800">
                          {opportunity.StageName}
                        </span>
                        {opportunity.Type && (
                          <span className="inline-flex px-2 py-1 rounded-full text-xs font-medium bg-neutral-100 text-neutral-800">
                            {opportunity.Type}
                          </span>
                        )}
                      </div>
                      <h4 className="font-medium text-neutral-900 mb-1">{opportunity.Name}</h4>
                      <div className="flex items-center space-x-4 text-sm text-neutral-600">
                        <span>Amount: ${(opportunity.Amount || 0).toLocaleString()}</span>
                        {opportunity.Account && (
                          <span>Account: {opportunity.Account.Name}</span>
                        )}
                        {opportunity.CloseDate && (
                          <span>Close Date: {new Date(opportunity.CloseDate).toLocaleDateString()}</span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))
            }
          </div>
        ) : (
          <p className="text-sm text-neutral-600">No opportunities found</p>
        )}
      </div>

      {/* Top Accounts */}
      <div>
        <h3 className="text-lg font-medium text-neutral-900 mb-4 flex items-center space-x-2">
          <BuildingOfficeIcon className="h-5 w-5" />
          <span>Top Accounts</span>
        </h3>
        {accounts.length > 0 ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {accounts.slice(0, 6).map((account) => {
              const accountOpportunities = opportunities.filter(opp => opp.AccountId === account.Id);
              const accountValue = accountOpportunities.reduce((sum, opp) => sum + (opp.Amount || 0), 0);
              
              return (
                <div key={account.Id} className="bg-white border border-neutral-200 rounded-lg p-4 hover:shadow-sm transition-shadow">
                  <div className="flex items-start space-x-3">
                    <div className="w-6 h-6 bg-primary-100 rounded flex items-center justify-center">
                      <span className="text-xs font-bold text-primary-600">
                        {account.Name?.slice(0, 2)}
                      </span>
                    </div>
                    <div className="flex-1">
                      <h4 className="font-medium text-neutral-900 mb-1">{account.Name}</h4>
                      {account.Industry && (
                        <p className="text-sm text-neutral-500 mb-2">{account.Industry}</p>
                      )}
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-neutral-600">
                          {accountOpportunities.length} opportunities
                        </span>
                        <span className="text-neutral-500">
                          ${accountValue.toLocaleString()}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-sm text-neutral-600">No accounts found</p>
        )}
      </div>
    </div>
  );
}