from rest_framework import serializers
from .models import Lead


class LeadSerializer(serializers.ModelSerializer):
    """Serializer for Lead model."""

    class Meta:
        model = Lead
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class LeadListSerializer(serializers.ModelSerializer):
    """Lighter serializer for list views."""

    class Meta:
        model = Lead
        fields = [
            'id', 'company_name', 'domain', 'signal_type', 'signal_strength',
            'discovery_date', 'location', 'status', 'industry', 'source_url'
        ]


class LeadStatsSerializer(serializers.Serializer):
    """Serializer for dashboard statistics."""
    total_leads = serializers.IntegerField()
    new_leads = serializers.IntegerField()
    contacted_leads = serializers.IntegerField()
    qualified_leads = serializers.IntegerField()
    by_signal_type = serializers.DictField()
    by_signal_strength = serializers.DictField()
    by_status = serializers.DictField()
    recent_leads = LeadListSerializer(many=True)
