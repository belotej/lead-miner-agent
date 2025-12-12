from django.db import models


class Lead(models.Model):
    """Model representing a discovered lead from various sources."""

    # Status choices for lead tracking
    STATUS_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('qualified', 'Qualified'),
        ('proposal', 'Proposal Sent'),
        ('won', 'Won'),
        ('lost', 'Lost'),
        ('archived', 'Archived'),
    ]

    # Signal strength choices
    SIGNAL_STRENGTH_CHOICES = [
        ('Very High', 'Very High'),
        ('High', 'High'),
        ('Medium', 'Medium'),
        ('Low', 'Low'),
    ]

    # Core fields matching existing schema
    company_name = models.CharField(max_length=255)
    domain = models.CharField(max_length=255, blank=True, default='')
    discovery_source = models.CharField(max_length=100)
    signal_type = models.CharField(max_length=100)
    signal_strength = models.CharField(max_length=20, choices=SIGNAL_STRENGTH_CHOICES, default='Medium')
    discovery_date = models.DateField()
    signal_date = models.CharField(max_length=100, blank=True, default='')
    details = models.TextField(blank=True, default='')
    location = models.CharField(max_length=255, blank=True, default='')
    timeline = models.CharField(max_length=100, blank=True, default='Unknown')
    source_url = models.URLField(max_length=500, unique=True)  # Prevents duplicates
    county = models.CharField(max_length=100, blank=True, default='')
    all_signals = models.CharField(max_length=255, blank=True, default='')
    notes = models.TextField(blank=True, default='')

    # Additional fields for lead management
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Optional enrichment fields (for Phase 2)
    employee_count = models.IntegerField(null=True, blank=True)
    industry = models.CharField(max_length=100, blank=True, default='')
    contact_name = models.CharField(max_length=255, blank=True, default='')
    contact_email = models.EmailField(blank=True, default='')
    contact_phone = models.CharField(max_length=50, blank=True, default='')

    class Meta:
        ordering = ['-discovery_date', '-created_at']
        verbose_name = 'Lead'
        verbose_name_plural = 'Leads'

    def __str__(self):
        return f"{self.company_name} ({self.signal_type})"
