from django.contrib import admin
from .models import Lead


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    """Admin configuration for Lead model."""

    # Columns displayed in the list view
    list_display = [
        'company_name',
        'signal_type',
        'signal_strength',
        'location',
        'discovery_date',
        'status',
        'industry',
    ]

    # Filters in the right sidebar
    list_filter = [
        'status',
        'signal_strength',
        'signal_type',
        'discovery_source',
        'discovery_date',
        'location',
    ]

    # Searchable fields
    search_fields = [
        'company_name',
        'domain',
        'details',
        'notes',
        'location',
        'industry',
    ]

    # Fields that can be edited directly in list view
    list_editable = ['status']

    # Default ordering
    ordering = ['-discovery_date', '-created_at']

    # Pagination
    list_per_page = 50

    # Date hierarchy for drilling down
    date_hierarchy = 'discovery_date'

    # Fieldsets for the detail/edit view
    fieldsets = (
        ('Company Information', {
            'fields': ('company_name', 'domain', 'industry', 'location', 'county')
        }),
        ('Signal Details', {
            'fields': ('signal_type', 'signal_strength', 'discovery_source', 'discovery_date', 'signal_date', 'timeline')
        }),
        ('Lead Status', {
            'fields': ('status',)
        }),
        ('Details', {
            'fields': ('details', 'notes', 'source_url', 'all_signals'),
            'classes': ('collapse',)  # Collapsible section
        }),
        ('Contact Information (Phase 2)', {
            'fields': ('contact_name', 'contact_email', 'contact_phone', 'employee_count'),
            'classes': ('collapse',)
        }),
    )

    # Read-only fields
    readonly_fields = ['created_at', 'updated_at']

    # Actions for bulk operations
    actions = ['mark_as_contacted', 'mark_as_qualified', 'mark_as_archived']

    @admin.action(description='Mark selected leads as Contacted')
    def mark_as_contacted(self, request, queryset):
        updated = queryset.update(status='contacted')
        self.message_user(request, f'{updated} leads marked as contacted.')

    @admin.action(description='Mark selected leads as Qualified')
    def mark_as_qualified(self, request, queryset):
        updated = queryset.update(status='qualified')
        self.message_user(request, f'{updated} leads marked as qualified.')

    @admin.action(description='Archive selected leads')
    def mark_as_archived(self, request, queryset):
        updated = queryset.update(status='archived')
        self.message_user(request, f'{updated} leads archived.')
