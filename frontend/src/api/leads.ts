import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
});

export interface Lead {
  id: number;
  company_name: string;
  domain: string;
  discovery_source: string;
  signal_type: string;
  signal_strength: string;
  discovery_date: string;
  signal_date: string;
  details: string;
  location: string;
  timeline: string;
  source_url: string;
  county: string;
  all_signals: string;
  notes: string;
  status: string;
  industry: string;
  contact_name: string;
  contact_email: string;
  contact_phone: string;
  created_at: string;
  updated_at: string;
}

export interface LeadListItem {
  id: number;
  company_name: string;
  domain: string;
  signal_type: string;
  signal_strength: string;
  discovery_date: string;
  location: string;
  status: string;
  industry: string;
  source_url: string;
}

export interface LeadStats {
  total_leads: number;
  new_leads: number;
  contacted_leads: number;
  qualified_leads: number;
  by_signal_type: Record<string, number>;
  by_signal_strength: Record<string, number>;
  by_status: Record<string, number>;
  recent_leads: LeadListItem[];
}

export interface LeadFilters {
  statuses: { value: string; label: string }[];
  signal_strengths: { value: string; label: string }[];
  signal_types: string[];
  discovery_sources: string[];
  locations: string[];
  industries: string[];
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface LeadQueryParams {
  page?: number;
  search?: string;
  status?: string;
  signal_type?: string;
  signal_strength?: string;
  location?: string;
  industry?: string;
  ordering?: string;
}

export const leadsApi = {
  getLeads: async (params: LeadQueryParams = {}): Promise<PaginatedResponse<LeadListItem>> => {
    const response = await api.get('/leads/', { params });
    return response.data;
  },

  getLead: async (id: number): Promise<Lead> => {
    const response = await api.get(`/leads/${id}/`);
    return response.data;
  },

  updateLead: async (id: number, data: Partial<Lead>): Promise<Lead> => {
    const response = await api.patch(`/leads/${id}/`, data);
    return response.data;
  },

  updateStatus: async (id: number, status: string): Promise<Lead> => {
    const response = await api.post(`/leads/${id}/update_status/`, { status });
    return response.data;
  },

  deleteLead: async (id: number): Promise<void> => {
    await api.delete(`/leads/${id}/`);
  },

  getStats: async (): Promise<LeadStats> => {
    const response = await api.get('/leads/stats/');
    return response.data;
  },

  getFilters: async (): Promise<LeadFilters> => {
    const response = await api.get('/leads/filters/');
    return response.data;
  },
};
