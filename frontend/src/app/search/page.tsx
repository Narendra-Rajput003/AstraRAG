'use client';

import React, { useState, useEffect } from 'react';
import { Search, Filter, SortAsc, SortDesc, FileText, Calendar, User, Tag, Download, Highlighter } from 'lucide-react';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { searchAPI } from '@/services/api';
import { SearchRequest, SearchResult, SearchFacet } from '@/types';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/hooks/useToast';
import { SkeletonList } from '@/components/LoadingSkeleton';

const SearchPage: React.FC = () => {
  const { user } = useAuth();
  const { error: showError } = useToast();

  return (
    <ErrorBoundary>
      <SearchPageContent />
    </ErrorBoundary>
  );
};

const SearchPageContent: React.FC = () => {
  const { user } = useAuth();
  const { error: showError } = useToast();

  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<any>({});
  const [sortBy, setSortBy] = useState('uploaded_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(20);

  const [searchResults, setSearchResults] = useState<SearchResult | null>(null);
  const [facets, setFacets] = useState<SearchFacet | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [searchHistory, setSearchHistory] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  useEffect(() => {
    loadFacets();
  }, []);

  useEffect(() => {
    if (searchQuery || Object.keys(filters).length > 0) {
      performSearch();
    }
  }, [searchQuery, filters, sortBy, sortOrder, currentPage]);

  const loadFacets = async () => {
    try {
      const facetData = await searchAPI.getFacets();
      setFacets(facetData);
    } catch (error) {
      console.error('Failed to load facets:', error);
    }
  };

  const performSearch = async () => {
    setIsLoading(true);
    try {
      const searchRequest: SearchRequest = {
        query: searchQuery,
        filters: Object.keys(filters).length > 0 ? filters : undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
        page: currentPage,
        size: pageSize,
      };

      const results = await searchAPI.searchDocuments(searchRequest);
      setSearchResults(results);
    } catch (error) {
      console.error('Search failed:', error);
      showError('Search failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleFilterChange = (key: string, value: any) => {
    setFilters((prev: any) => {
      const newFilters = { ...prev };
      if (value === '' || value === null || value === undefined) {
        delete newFilters[key];
      } else {
        newFilters[key] = value;
      }
      return newFilters;
    });
    setCurrentPage(1); // Reset to first page when filters change
  };

  const clearFilters = () => {
    setFilters({});
    setCurrentPage(1);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  // Highlight search terms in text
  const highlightText = (text: string, query: string) => {
    if (!query || !text) return text;

    const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    const parts = text.split(regex);

    return parts.map((part, index) =>
      regex.test(part) ? (
        <mark key={index} className="bg-yellow-200 text-gray-900 px-1 rounded">
          {part}
        </mark>
      ) : part
    );
  };

  // Export search results
  const exportResults = (format: 'csv' | 'json') => {
    if (!searchResults?.documents) return;

    const data = searchResults.documents.map(doc => ({
      filename: doc.filename,
      content: doc.content.substring(0, 500), // Truncate for export
      uploaded_by: doc.uploaded_by,
      uploaded_at: doc.uploaded_at,
      file_type: doc.file_type,
      file_size: doc.file_size,
      status: doc.status,
      tags: doc.tags?.join(', ') || '',
    }));

    if (format === 'csv') {
      const headers = Object.keys(data[0]).join(',');
      const rows = data.map(row => Object.values(row).map(val => `"${val}"`).join(','));
      const csv = [headers, ...rows].join('\n');

      const blob = new Blob([csv], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `search_results_${new Date().toISOString().split('T')[0]}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    } else {
      const json = JSON.stringify(data, null, 2);
      const blob = new Blob([json], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `search_results_${new Date().toISOString().split('T')[0]}.json`;
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  // Load search history from localStorage
  useEffect(() => {
    const history = localStorage.getItem('search_history');
    if (history) {
      setSearchHistory(JSON.parse(history));
    }
  }, []);

  // Save search to history
  const saveToHistory = (query: string) => {
    if (!query.trim()) return;

    const updatedHistory = [query, ...searchHistory.filter(h => h !== query)].slice(0, 10);
    setSearchHistory(updatedHistory);
    localStorage.setItem('search_history', JSON.stringify(updatedHistory));
  };

  // Handle search submission
  const handleSearch = () => {
    if (searchQuery.trim()) {
      saveToHistory(searchQuery);
      performSearch();
    }
  };

  if (!user) {
    return <div>Please log in to access search.</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">Document Search</h1>

          {/* Search Bar */}
          <div className="flex flex-col sm:flex-row gap-4 mb-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search documents..."
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setShowSuggestions(e.target.value.length > 0);
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleSearch();
                    setShowSuggestions(false);
                  } else if (e.key === 'Escape') {
                    setShowSuggestions(false);
                  }
                }}
                onFocus={() => setShowSuggestions(searchQuery.length > 0)}
                onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />

              {/* Search Suggestions */}
              {showSuggestions && (
                <div className="absolute top-full left-0 right-0 bg-white border border-gray-300 rounded-lg shadow-lg z-10 max-h-60 overflow-y-auto">
                  {searchHistory.filter(h => h.toLowerCase().includes(searchQuery.toLowerCase())).map((suggestion, index) => (
                    <div
                      key={index}
                      className="px-4 py-2 hover:bg-gray-100 cursor-pointer border-b border-gray-100 last:border-b-0"
                      onClick={() => {
                        setSearchQuery(suggestion);
                        setShowSuggestions(false);
                        handleSearch();
                      }}
                    >
                      <div className="flex items-center gap-2">
                        <Search className="h-4 w-4 text-gray-400" />
                        <span>{suggestion}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <button
              onClick={handleSearch}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
            >
              <Search className="h-5 w-5" />
              Search
            </button>

            <button
              onClick={() => setShowFilters(!showFilters)}
              className="px-4 py-3 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2"
            >
              <Filter className="h-5 w-5" />
              Filters
            </button>
          </div>

          {/* Filters Panel */}
          {showFilters && (
            <div className="bg-white p-4 md:p-6 rounded-lg shadow-sm border border-gray-200 mb-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* File Type Filter */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">File Type</label>
                  <select
                    value={filters.file_type || ''}
                    onChange={(e) => handleFilterChange('file_type', e.target.value)}
                    className="w-full p-2 border border-gray-300 rounded-md"
                  >
                    <option value="">All Types</option>
                    {facets?.file_types.map((type) => (
                      <option key={type} value={type}>{type.toUpperCase()}</option>
                    ))}
                  </select>
                </div>

                {/* Status Filter */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
                  <select
                    value={filters.status || ''}
                    onChange={(e) => handleFilterChange('status', e.target.value)}
                    className="w-full p-2 border border-gray-300 rounded-md"
                  >
                    <option value="">All Statuses</option>
                    {facets?.statuses.map((status) => (
                      <option key={status} value={status}>{status}</option>
                    ))}
                  </select>
                </div>

                {/* Date Range */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">From Date</label>
                  <input
                    type="date"
                    value={filters.date_from || ''}
                    onChange={(e) => handleFilterChange('date_from', e.target.value)}
                    className="w-full p-2 border border-gray-300 rounded-md"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">To Date</label>
                  <input
                    type="date"
                    value={filters.date_to || ''}
                    onChange={(e) => handleFilterChange('date_to', e.target.value)}
                    className="w-full p-2 border border-gray-300 rounded-md"
                  />
                </div>
              </div>

              {/* Sort Options */}
              <div className="mt-4 flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <label className="text-sm font-medium text-gray-700">Sort by:</label>
                  <select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value)}
                    className="p-2 border border-gray-300 rounded-md"
                  >
                    <option value="uploaded_at">Upload Date</option>
                    <option value="filename">Filename</option>
                    <option value="file_size">File Size</option>
                    <option value="_score">Relevance</option>
                  </select>
                </div>

                <button
                  onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                  className="p-2 border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  {sortOrder === 'asc' ? <SortAsc className="h-5 w-5" /> : <SortDesc className="h-5 w-5" />}
                </button>

                <button
                  onClick={clearFilters}
                  className="px-4 py-2 text-sm text-blue-600 hover:text-blue-800"
                >
                  Clear Filters
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Results */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          {isLoading ? (
            <div className="p-6">
              <SkeletonList count={5} />
            </div>
          ) : searchResults ? (
            <>
              {/* Results Header */}
              <div className="p-4 md:p-6 border-b border-gray-200">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div>
                    <h2 className="text-lg font-semibold text-gray-900">
                      {searchResults.total} results found
                    </h2>
                    <p className="text-sm text-gray-500 mt-1">
                      Page {searchResults.page} of {Math.ceil(searchResults.total / searchResults.size)}
                    </p>
                  </div>

                  {/* Export Buttons */}
                  <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
                    <button
                      onClick={() => exportResults('csv')}
                      className="px-3 sm:px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center justify-center gap-2 text-sm"
                    >
                      <Download className="h-4 w-4" />
                      <span className="hidden sm:inline">Export CSV</span>
                      <span className="sm:hidden">CSV</span>
                    </button>
                    <button
                      onClick={() => exportResults('json')}
                      className="px-3 sm:px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center justify-center gap-2 text-sm"
                    >
                      <Download className="h-4 w-4" />
                      <span className="hidden sm:inline">Export JSON</span>
                      <span className="sm:hidden">JSON</span>
                    </button>
                  </div>
                </div>
              </div>

              {/* Results List */}
              <div className="divide-y divide-gray-200">
                {searchResults.documents.map((doc) => (
                  <div key={doc.doc_id} className="p-4 md:p-6 hover:bg-gray-50">
                    <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <FileText className="h-5 w-5 text-gray-400" />
                          <h3 className="text-lg font-medium text-blue-600 hover:text-blue-800 cursor-pointer">
                            {doc.filename}
                          </h3>
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            doc.status === 'active' ? 'bg-green-100 text-green-800' :
                            doc.status === 'pending_review' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-red-100 text-red-800'
                          }`}>
                            {doc.status}
                          </span>
                        </div>

                        <p className="text-gray-600 mb-3 line-clamp-2">
                          {highlightText(doc.content.substring(0, 300), searchQuery)}...
                        </p>

                        <div className="flex flex-wrap items-center gap-2 sm:gap-4 text-sm text-gray-500">
                          <div className="flex items-center gap-1">
                            <User className="h-4 w-4" />
                            <span className="truncate max-w-20 sm:max-w-none">{doc.uploaded_by}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <Calendar className="h-4 w-4" />
                            <span className="hidden sm:inline">{formatDate(doc.uploaded_at)}</span>
                            <span className="sm:hidden">{new Date(doc.uploaded_at).toLocaleDateString()}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <span>{formatFileSize(doc.file_size)}</span>
                          </div>
                          <div className="uppercase text-xs bg-gray-100 px-2 py-1 rounded">
                            {doc.file_type}
                          </div>
                        </div>

                        {doc.tags && doc.tags.length > 0 && (
                          <div className="flex items-center gap-2 mt-2">
                            <Tag className="h-4 w-4 text-gray-400" />
                            <div className="flex gap-1">
                              {doc.tags.map((tag) => (
                                <span key={tag} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                                  {tag}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>

                      {doc._score && (
                        <div className="text-sm text-gray-500">
                          Score: {doc._score.toFixed(2)}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {/* Pagination */}
              {searchResults.total > searchResults.size && (
                <div className="p-4 md:p-6 border-t border-gray-200 flex items-center justify-between">
                  <button
                    onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                    disabled={currentPage === 1}
                    className="px-3 md:px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>

                  <div className="text-sm text-gray-700 text-center">
                    <span className="hidden sm:inline">
                      Page {currentPage} of {Math.ceil(searchResults.total / searchResults.size)}
                    </span>
                    <span className="sm:hidden">
                      {currentPage}/{Math.ceil(searchResults.total / searchResults.size)}
                    </span>
                  </div>

                  <button
                    onClick={() => setCurrentPage(Math.min(Math.ceil(searchResults.total / searchResults.size), currentPage + 1))}
                    disabled={currentPage === Math.ceil(searchResults.total / searchResults.size)}
                    className="px-3 md:px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </div>
              )}
            </>
          ) : (
            <div className="p-12 text-center text-gray-500">
              <Search className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No search results</h3>
              <p>Try adjusting your search query or filters.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SearchPage;