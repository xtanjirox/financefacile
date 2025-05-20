"""View for calendar display.

This module provides a view for displaying calendar events in a
calendar format using FullCalendar.
"""
import logging
from django.views import generic
from django.urls import reverse_lazy
from core.mixins import CompanyMixin
from core.models import CalendarEvent

logger = logging.getLogger(__name__)

class CalendarDisplayView(CompanyMixin, generic.TemplateView):
    """View for displaying calendar events in a calendar format."""
    
    template_name = 'core/calendar/calendar_display.html'
    
    def get_context_data(self, **kwargs):
        """Get the context data for the view."""
        context = super().get_context_data(**kwargs)
        context['segment'] = 'calendar'
        context['title'] = 'Calendar'
        
        # Add API endpoint for FullCalendar to fetch events
        context['events_json_url'] = reverse_lazy('calendar-events-json')
        
        # Add theme choices for filtering
        context['theme_choices'] = dict(CalendarEvent.THEME_CHOICES)
        
        return context
