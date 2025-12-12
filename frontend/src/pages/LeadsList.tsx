import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Search, ExternalLink, ChevronLeft, ChevronRight } from 'lucide-react';
import type { LeadQueryParams } from '../api/leads';
import { leadsApi } from '../api/leads';
import { StatusBadge } from '../components/StatusBadge';
import { SignalBadge } from '../components/SignalBadge';

export function LeadsList() {
  const [params, setParams] = useState<LeadQueryParams>({ page: 1 });
  const [searchInput, setSearchInput] = useState('');

  const { data: leads, isLoading } = useQuery({
    queryKey: ['leads', params],
    queryFn: () => leadsApi.getLeads(params),
  });

  const { data: filters } = useQuery({
    queryKey: ['filters'],
    queryFn: leadsApi.getFilters,
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setParams({ ...params, search: searchInput, page: 1 });
  };

  const handleFilterChange = (key: string, value: string) => {
    setParams({ ...params, [key]: value || undefined, page: 1 });
  };

  const totalPages = leads ? Math.ceil(leads.count / 25) : 0;

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Leads</h1>
        <p className="text-slate-500 mt-1">Manage and track your sales leads</p>
      </div>

      {/* Search and Filters */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4 mb-6">
        <div className="flex flex-wrap gap-4">
          {/* Search */}
          <form onSubmit={handleSearch} className="flex-1 min-w-[200px]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
              <input
                type="text"
                placeholder="Search companies..."
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </form>

          {/* Status Filter */}
          <select
            value={params.status || ''}
            onChange={(e) => handleFilterChange('status', e.target.value)}
            className="px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Statuses</option>
            {filters?.statuses.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>

          {/* Signal Strength Filter */}
          <select
            value={params.signal_strength || ''}
            onChange={(e) => handleFilterChange('signal_strength', e.target.value)}
            className="px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Strengths</option>
            {filters?.signal_strengths.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>

          {/* Signal Type Filter */}
          <select
            value={params.signal_type || ''}
            onChange={(e) => handleFilterChange('signal_type', e.target.value)}
            className="px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Types</option>
            {filters?.signal_types.map((t) => (
              <option key={t} value={t}>
                {t.replace('_', ' ')}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Leads Table */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : (
          <>
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Company
                  </th>
                  <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Signal
                  </th>
                  <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Strength
                  </th>
                  <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Location
                  </th>
                  <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-6 py-3"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {leads?.results.map((lead) => (
                  <tr key={lead.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-6 py-4">
                      <Link to={`/leads/${lead.id}`} className="group">
                        <p className="font-medium text-slate-900 group-hover:text-blue-600">
                          {lead.company_name}
                        </p>
                        {lead.industry && (
                          <p className="text-sm text-slate-500">{lead.industry}</p>
                        )}
                      </Link>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-sm text-slate-600 capitalize">
                        {lead.signal_type.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <SignalBadge strength={lead.signal_strength} />
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-sm text-slate-600">{lead.location || '-'}</span>
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge status={lead.status} />
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-sm text-slate-500">{lead.discovery_date}</span>
                    </td>
                    <td className="px-6 py-4">
                      {lead.source_url && (
                        <a
                          href={lead.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-slate-400 hover:text-blue-600"
                        >
                          <ExternalLink size={16} />
                        </a>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Pagination */}
            {leads && leads.count > 0 && (
              <div className="px-6 py-4 border-t border-slate-200 flex items-center justify-between">
                <p className="text-sm text-slate-500">
                  Showing {((params.page || 1) - 1) * 25 + 1} to{' '}
                  {Math.min((params.page || 1) * 25, leads.count)} of {leads.count} leads
                </p>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setParams({ ...params, page: (params.page || 1) - 1 })}
                    disabled={!leads.previous}
                    className="p-2 border border-slate-200 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-50"
                  >
                    <ChevronLeft size={18} />
                  </button>
                  <span className="text-sm text-slate-600">
                    Page {params.page || 1} of {totalPages}
                  </span>
                  <button
                    onClick={() => setParams({ ...params, page: (params.page || 1) + 1 })}
                    disabled={!leads.next}
                    className="p-2 border border-slate-200 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-50"
                  >
                    <ChevronRight size={18} />
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
