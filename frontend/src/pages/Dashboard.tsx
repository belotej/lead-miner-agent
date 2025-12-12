import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Users, UserPlus, UserCheck, TrendingUp } from 'lucide-react';
import { leadsApi } from '../api/leads';
import { StatCard } from '../components/StatCard';
import { StatusBadge } from '../components/StatusBadge';
import { SignalBadge } from '../components/SignalBadge';

export function Dashboard() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['stats'],
    queryFn: leadsApi.getStats,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!stats) return null;

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
        <p className="text-slate-500 mt-1">Overview of your lead pipeline</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard title="Total Leads" value={stats.total_leads} icon={Users} color="blue" />
        <StatCard title="New Leads" value={stats.new_leads} icon={UserPlus} color="green" />
        <StatCard title="Contacted" value={stats.contacted_leads} icon={TrendingUp} color="yellow" />
        <StatCard title="Qualified" value={stats.qualified_leads} icon={UserCheck} color="purple" />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* By Signal Type */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">By Signal Type</h3>
          <div className="space-y-3">
            {Object.entries(stats.by_signal_type).map(([type, count]) => (
              <div key={type} className="flex items-center justify-between">
                <span className="text-sm text-slate-600 capitalize">{type.replace('_', ' ')}</span>
                <div className="flex items-center gap-3">
                  <div className="w-32 bg-slate-100 rounded-full h-2">
                    <div
                      className="bg-blue-500 h-2 rounded-full"
                      style={{ width: `${(count / stats.total_leads) * 100}%` }}
                    />
                  </div>
                  <span className="text-sm font-medium text-slate-900 w-8 text-right">{count}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* By Signal Strength */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">By Signal Strength</h3>
          <div className="space-y-3">
            {Object.entries(stats.by_signal_strength).map(([strength, count]) => (
              <div key={strength} className="flex items-center justify-between">
                <SignalBadge strength={strength} />
                <div className="flex items-center gap-3">
                  <div className="w-32 bg-slate-100 rounded-full h-2">
                    <div
                      className="bg-green-500 h-2 rounded-full"
                      style={{ width: `${(count / stats.total_leads) * 100}%` }}
                    />
                  </div>
                  <span className="text-sm font-medium text-slate-900 w-8 text-right">{count}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Leads */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200">
        <div className="p-6 border-b border-slate-200 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-slate-900">Recent Leads</h3>
          <Link
            to="/leads"
            className="text-sm text-blue-600 hover:text-blue-700 font-medium"
          >
            View all
          </Link>
        </div>
        <div className="divide-y divide-slate-100">
          {stats.recent_leads.map((lead) => (
            <Link
              key={lead.id}
              to={`/leads/${lead.id}`}
              className="flex items-center justify-between p-4 hover:bg-slate-50 transition-colors"
            >
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 bg-slate-100 rounded-full flex items-center justify-center">
                  <span className="text-sm font-semibold text-slate-600">
                    {lead.company_name.charAt(0)}
                  </span>
                </div>
                <div>
                  <p className="font-medium text-slate-900">{lead.company_name}</p>
                  <p className="text-sm text-slate-500">
                    {lead.location || 'Unknown location'} · {lead.signal_type.replace('_', ' ')}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <SignalBadge strength={lead.signal_strength} />
                <StatusBadge status={lead.status} />
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
