'use client';

import React, { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api';
import { 
  RectangleStackIcon,
  CreditCardIcon,
  UserGroupIcon,
  ExclamationCircleIcon,
  CheckCircleIcon,
  ClockIcon,
  ListBulletIcon
} from '@heroicons/react/24/outline';

interface TrelloAnalyticsProps {
  integrationId: number;
  integrationName: string;
}

export default function TrelloAnalytics({ integrationId, integrationName }: TrelloAnalyticsProps) {
  const [boards, setBoards] = useState<any[]>([]);
  const [cards, setCards] = useState<any[]>([]);
  const [lists, setLists] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadTrelloData();
  }, [integrationId]);

  const loadTrelloData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [boardsResponse, cardsResponse, listsResponse] = await Promise.allSettled([
        apiClient.getTrelloBoards(integrationId),
        apiClient.getTrelloCards(integrationId),
        apiClient.getTrelloLists(integrationId)
      ]);

      if (boardsResponse.status === 'fulfilled') {
        if (!boardsResponse.value.data) {
          throw new Error('Trello boards data not available');
        }
        setBoards(boardsResponse.value.data);
      } else {
        throw new Error('Failed to load Trello boards');
      }

      if (cardsResponse.status === 'fulfilled') {
        if (!cardsResponse.value.data) {
          throw new Error('Trello cards data not available');
        }
        setCards(cardsResponse.value.data);
      } else {
        throw new Error('Failed to load Trello cards');
      }

      if (listsResponse.status === 'fulfilled') {
        if (!listsResponse.value.data) {
          throw new Error('Trello lists data not available');
        }
        setLists(listsResponse.value.data);
      } else {
        throw new Error('Failed to load Trello lists');
      }
    } catch (err) {
      setError('Error loading Trello analytics');
      console.error('Trello analytics error:', err);
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

  const activeBoards = boards.filter(board => !board.closed);
  const completedCards = cards.filter(card => {
    const cardList = lists.find(list => list.id === card.idList);
    return cardList && (cardList.name.toLowerCase().includes('done') || cardList.name.toLowerCase().includes('complete'));
  });
  const overduecards = cards.filter(card => card.due && new Date(card.due) < new Date() && !card.dueComplete);

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-neutral-50 rounded-lg p-4 border border-neutral-200">
          <div className="flex items-center space-x-2">
            <RectangleStackIcon className="h-5 w-5 text-neutral-600" />
            <div>
              <p className="text-sm font-medium text-neutral-700">Active Boards</p>
              <p className="text-xl font-bold text-neutral-900">{activeBoards.length}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-neutral-50 rounded-lg p-4 border border-neutral-200">
          <div className="flex items-center space-x-2">
            <CreditCardIcon className="h-5 w-5 text-neutral-600" />
            <div>
              <p className="text-sm font-medium text-neutral-700">Total Cards</p>
              <p className="text-xl font-bold text-neutral-900">{cards.length}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-neutral-50 rounded-lg p-4 border border-neutral-200">
          <div className="flex items-center space-x-2">
            <CheckCircleIcon className="h-5 w-5 text-neutral-600" />
            <div>
              <p className="text-sm font-medium text-neutral-700">Completed</p>
              <p className="text-xl font-bold text-neutral-900">{completedCards.length}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-neutral-50 rounded-lg p-4 border border-neutral-200">
          <div className="flex items-center space-x-2">
            <ClockIcon className="h-5 w-5 text-neutral-600" />
            <div>
              <p className="text-sm font-medium text-neutral-700">Overdue</p>
              <p className="text-xl font-bold text-neutral-900">{overduecards.length}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Cards */}
      <div>
        <h3 className="text-lg font-medium text-neutral-900 mb-4 flex items-center space-x-2">
          <CreditCardIcon className="h-5 w-5" />
          <span>Recent Cards</span>
        </h3>
        {cards.length > 0 ? (
          <div className="space-y-3">
            {cards
              .sort((a, b) => new Date(b.dateLastActivity).getTime() - new Date(a.dateLastActivity).getTime())
              .slice(0, 8)
              .map((card) => {
                const cardList = lists.find(list => list.id === card.idList);
                const cardBoard = boards.find(board => board.id === card.idBoard);
                return (
                  <div key={card.id} className="bg-white border border-neutral-200 rounded-lg p-4 hover:shadow-sm transition-shadow">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          {cardList && (
                            <span className="inline-flex px-2 py-1 rounded-full text-xs font-medium bg-neutral-100 text-neutral-800">
                              {cardList.name}
                            </span>
                          )}
                          {card.due && (
                            <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${
                              card.dueComplete ? 'bg-green-100 text-green-800' :
                              new Date(card.due) < new Date() ? 'bg-red-100 text-red-800' :
                              'bg-yellow-100 text-yellow-800'
                            }`}>
                              {card.dueComplete ? 'Complete' : 
                               new Date(card.due) < new Date() ? 'Overdue' : 'Due Soon'}
                            </span>
                          )}
                        </div>
                        <h4 className="font-medium text-neutral-900 mb-1">{card.name}</h4>
                        <div className="flex items-center space-x-4 text-sm text-neutral-600">
                          {cardBoard && (
                            <span>Board: {cardBoard.name}</span>
                          )}
                          {card.due && (
                            <span>Due: {new Date(card.due).toLocaleDateString()}</span>
                          )}
                          <span>Updated: {new Date(card.dateLastActivity).toLocaleDateString()}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })
            }
          </div>
        ) : (
          <p className="text-sm text-neutral-600">No cards found</p>
        )}
      </div>

      {/* Active Boards */}
      <div>
        <h3 className="text-lg font-medium text-neutral-900 mb-4 flex items-center space-x-2">
          <ListBulletIcon className="h-5 w-5" />
          <span>Active Boards</span>
        </h3>
        {activeBoards.length > 0 ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {activeBoards.slice(0, 6).map((board) => {
              const boardCards = cards.filter(card => card.idBoard === board.id);
              const boardLists = lists.filter(list => list.idBoard === board.id);
              
              return (
                <div key={board.id} className="bg-white border border-neutral-200 rounded-lg p-4 hover:shadow-sm transition-shadow">
                  <div className="flex items-start space-x-3">
                    <div className="w-6 h-6 bg-primary-100 rounded flex items-center justify-center">
                      <span className="text-xs font-bold text-primary-600">
                        {board.name?.slice(0, 2)}
                      </span>
                    </div>
                    <div className="flex-1">
                      <h4 className="font-medium text-neutral-900 mb-1">{board.name}</h4>
                      {board.desc && (
                        <p className="text-sm text-neutral-500 mb-2 truncate">{board.desc}</p>
                      )}
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-neutral-600">
                          {boardCards.length} cards
                        </span>
                        <span className="text-neutral-500">
                          {boardLists.length} lists
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-sm text-neutral-600">No active boards found</p>
        )}
      </div>
    </div>
  );
}