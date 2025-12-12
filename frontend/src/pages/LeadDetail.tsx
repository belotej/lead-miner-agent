import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, ExternalLink, Building2, MapPin, Save } from 'lucide-react';
import { useState } from 'react';
import { leadsApi } from '../api/leads';
import { StatusBadge } from '../components/StatusBadge';
import { SignalBadge } from '../components/SignalBadge';

export function LeadDetail() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const [isEditing, setIsEditing] = useState(false);
  const [notes, setNotes] = useState('');

  const { data: lead, isLoading } = useQuery({
    queryKey: ['lead', id],
    queryFn: () => leadsApi.getLead(Number(id)),
    enabled: !!id,
  });

  const { data: filters } = useQuery({
    queryKey: ['filters'],
    queryFn: leadsApi.getFilters,
  });

  const updateMutation = useMutation({
    mutationFn: (data: { status?: string; notes?: string }) =>
      leadsApi.updateLead(Number(id), data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lead', id] });
      queryClient.invalidateQueries({ queryKey: ['leads'] });
      queryClient.invalidateQueries({ queryKey: ['stats'] });
      setIsEditing(false);
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!lead) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-500">Lead not found</p>
        <Link to="/leads" className="text-blue-600 hover:underline mt-2 inline-block">
          Back to leads
        </Link>
      </div>
    );
  }

  const handleStatusChange = (newStatus: string) => {
    updateMutation.mutate({ status: newStatus });
  };

  const handleSaveNotes = () => {
    updateMutation.mutate({ notes });
  };

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <Link
          to="/leads"
          className="inline-flex items-center gap-2 text-slate-500 hover:text-slate-700 mb-4"
        >
          <ArrowLeft size={18} />
          Back to leads
        </Link>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">{lead.company_name}</h1>
            <div className="flex items-center gap-4 mt-2">
              {lead.industry && (
                <span className="text-slate-500 flex items-center gap-1">
                  <Building2 size={16} />
                  {lead.industry}
                </span>
              )}
              {lead.location && (
                <span className="text-slate-500 flex items-center gap-1">
                  <MapPin size={16} />
                  {lead.location}
                </span>
              )}
            </div>
          </div>
          <div className="flex items-center gap-3">
            <SignalBadge strength={lead.signal_strength} />
            <StatusBadge status={lead.status} />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Info */}
        <div className="lg:col-span-2 space-y-6">
          {/* Signal Details */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Signal Details</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-slate-500">Signal Type</p>
                <p className="font-medium text-slate-900 capitalize mt-1">
                  {lead.signal_type.replace('_', ' ')}
                </p>
              </div>
              <div>
                <p className="text-sm text-slate-500">Discovery Source</p>
                <p className="font-medium text-slate-900 capitalize mt-1">
                  {lead.discovery_source.replace('_', ' ')}
                </p>
              </div>
              <div>
                <p className="text-sm text-slate-500">Discovery Date</p>
                <p className="font-medium text-slate-900 mt-1">{lead.discovery_date}</p>
              </div>
              <div>
                <p className="text-sm text-slate-500">Timeline</p>
                <p className="font-medium text-slate-900 mt-1">{lead.timeline || 'Unknown'}</p>
              </div>
            </div>
            {lead.details && (
              <div className="mt-4 pt-4 border-t border-slate-100">
                <p className="text-sm text-slate-500 mb-2">Details</p>
                <p className="text-slate-700">{lead.details}</p>
              </div>
            )}
            {lead.source_url && (
              <div className="mt-4">
                <a
                  href={lead.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700"
                >
                  <ExternalLink size={16} />
                  View source
                </a>
              </div>
            )}
          </div>

          {/* Notes */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-slate-900">Notes</h3>
              {!isEditing && (
                <button
                  onClick={() => {
                    setNotes(lead.notes || '');
                    setIsEditing(true);
                  }}
                  className="text-sm text-blue-600 hover:text-blue-700"
                >
                  Edit
                </button>
              )}
            </div>
            {isEditing ? (
              <div>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={4}
                  className="w-full p-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Add notes about this lead..."
                />
                <div className="flex justify-end gap-2 mt-3">
                  <button
                    onClick={() => setIsEditing(false)}
                    className="px-4 py-2 text-sm text-slate-600 hover:text-slate-700"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSaveNotes}
                    disabled={updateMutation.isPending}
                    className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
                  >
                    <Save size={16} />
                    Save
                  </button>
                </div>
              </div>
            ) : (
              <p className="text-slate-600">
                {lead.notes || 'No notes yet. Click edit to add notes.'}
              </p>
            )}
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Status Update */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Update Status</h3>
            <div className="space-y-2">
              {filters?.statuses.map((s) => (
                <button
                  key={s.value}
                  onClick={() => handleStatusChange(s.value)}
                  disabled={updateMutation.isPending}
                  className={`w-full text-left px-4 py-2 rounded-lg text-sm transition-colors ${
                    lead.status === s.value
                      ? 'bg-blue-50 text-blue-700 border-2 border-blue-500'
                      : 'bg-slate-50 text-slate-600 hover:bg-slate-100 border-2 border-transparent'
                  }`}
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>

          {/* Contact Info */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Contact Info</h3>
            {lead.contact_name || lead.contact_email || lead.contact_phone ? (
              <div className="space-y-3">
                {lead.contact_name && (
                  <div>
                    <p className="text-sm text-slate-500">Name</p>
                    <p className="font-medium text-slate-900">{lead.contact_name}</p>
                  </div>
                )}
                {lead.contact_email && (
                  <div>
                    <p className="text-sm text-slate-500">Email</p>
                    <a
                      href={`mailto:${lead.contact_email}`}
                      className="font-medium text-blue-600 hover:underline"
                    >
                      {lead.contact_email}
                    </a>
                  </div>
                )}
                {lead.contact_phone && (
                  <div>
                    <p className="text-sm text-slate-500">Phone</p>
                    <a
                      href={`tel:${lead.contact_phone}`}
                      className="font-medium text-blue-600 hover:underline"
                    >
                      {lead.contact_phone}
                    </a>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-slate-500 text-sm">No contact info available</p>
            )}
          </div>

          {/* Metadata */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Metadata</h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-500">Created</span>
                <span className="text-slate-900">
                  {new Date(lead.created_at).toLocaleDateString()}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Updated</span>
                <span className="text-slate-900">
                  {new Date(lead.updated_at).toLocaleDateString()}
                </span>
              </div>
              {lead.domain && (
                <div className="flex justify-between">
                  <span className="text-slate-500">Domain</span>
                  <span className="text-slate-900">{lead.domain}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
