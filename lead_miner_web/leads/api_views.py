from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count
from .models import Lead
from .serializers import LeadSerializer, LeadListSerializer, LeadStatsSerializer


class LeadViewSet(viewsets.ModelViewSet):
    """
    API endpoint for leads.

    Supports:
    - GET /api/leads/ - List all leads (paginated)
    - GET /api/leads/{id}/ - Get single lead
    - POST /api/leads/ - Create lead
    - PUT /api/leads/{id}/ - Update lead
    - PATCH /api/leads/{id}/ - Partial update
    - DELETE /api/leads/{id}/ - Delete lead
    - GET /api/leads/stats/ - Dashboard statistics
    """
    queryset = Lead.objects.all().order_by('-discovery_date', '-created_at')
    serializer_class = LeadSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['company_name', 'domain', 'details', 'location', 'industry']
    ordering_fields = ['company_name', 'discovery_date', 'signal_strength', 'status', 'created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return LeadListSerializer
        return LeadSerializer

    def get_queryset(self):
        queryset = Lead.objects.all().order_by('-discovery_date', '-created_at')

        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by signal_type
        signal_type = self.request.query_params.get('signal_type')
        if signal_type:
            queryset = queryset.filter(signal_type=signal_type)

        # Filter by signal_strength
        signal_strength = self.request.query_params.get('signal_strength')
        if signal_strength:
            queryset = queryset.filter(signal_strength=signal_strength)

        # Filter by discovery_source
        discovery_source = self.request.query_params.get('discovery_source')
        if discovery_source:
            queryset = queryset.filter(discovery_source=discovery_source)

        # Filter by location (partial match)
        location = self.request.query_params.get('location')
        if location:
            queryset = queryset.filter(location__icontains=location)

        # Filter by industry
        industry = self.request.query_params.get('industry')
        if industry:
            queryset = queryset.filter(industry__icontains=industry)

        return queryset

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Return dashboard statistics."""
        leads = Lead.objects.all()

        # Count by status
        by_status = dict(leads.values('status').annotate(count=Count('id')).values_list('status', 'count'))

        # Count by signal type
        by_signal_type = dict(leads.values('signal_type').annotate(count=Count('id')).values_list('signal_type', 'count'))

        # Count by signal strength
        by_signal_strength = dict(leads.values('signal_strength').annotate(count=Count('id')).values_list('signal_strength', 'count'))

        # Recent leads
        recent_leads = leads.order_by('-discovery_date', '-created_at')[:5]

        stats = {
            'total_leads': leads.count(),
            'new_leads': leads.filter(status='new').count(),
            'contacted_leads': leads.filter(status='contacted').count(),
            'qualified_leads': leads.filter(status='qualified').count(),
            'by_signal_type': by_signal_type,
            'by_signal_strength': by_signal_strength,
            'by_status': by_status,
            'recent_leads': LeadListSerializer(recent_leads, many=True).data,
        }

        return Response(stats)

    @action(detail=False, methods=['get'])
    def filters(self, request):
        """Return available filter options."""
        leads = Lead.objects.all()

        return Response({
            'statuses': [{'value': s[0], 'label': s[1]} for s in Lead.STATUS_CHOICES],
            'signal_strengths': [{'value': s[0], 'label': s[1]} for s in Lead.SIGNAL_STRENGTH_CHOICES],
            'signal_types': list(leads.values_list('signal_type', flat=True).distinct()),
            'discovery_sources': list(leads.values_list('discovery_source', flat=True).distinct()),
            'locations': list(leads.values_list('location', flat=True).distinct()),
            'industries': list(leads.exclude(industry='').values_list('industry', flat=True).distinct()),
        })

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Quick status update endpoint."""
        lead = self.get_object()
        new_status = request.data.get('status')

        if new_status not in dict(Lead.STATUS_CHOICES):
            return Response(
                {'error': f'Invalid status. Must be one of: {list(dict(Lead.STATUS_CHOICES).keys())}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        lead.status = new_status
        lead.save()

        return Response(LeadSerializer(lead).data)
