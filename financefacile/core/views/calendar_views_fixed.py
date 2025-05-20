"""Views for calendar events management.

This module provides views for managing calendar events, including listing,
creating, updating, and deleting events, as well as an API endpoint for
FullCalendar integration.
"""
import logging

import pytz
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views import generic
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
from datetime import datetime, timedelta
from django.contrib.auth.models import User

from core.forms import CalendarEventForm
from core.mixins import CompanyMixin
from core.models import CalendarEvent

logger = logging.getLogger(__name__)

# Timezone to use for date conversions
TIME_ZONE = getattr(settings, 'TIME_ZONE', 'UTC')
TZ = pytz.timezone(TIME_ZONE)


class CalendarEventListView(CompanyMixin, generic.ListView):
    model = CalendarEvent
    template_name = 'core/calendar/calendar_event_list.html'
    context_object_name = 'events'
    
    def get_queryset(self):
        return CalendarEvent.objects.filter(
            company=self.get_company()
        ).select_related('created_by')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['segment'] = 'calendar'
        return context


class CalendarEventCreateView(CompanyMixin, generic.CreateView):
    model = CalendarEvent
    form_class = CalendarEventForm
    template_name = 'core/calendar/calendar_event_form.html'
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        company = self.get_company()
        # Filter participants to only include users from this company
        # Get users that belong to this company through their profiles
        user_ids = company.members.values_list('user_id', flat=True)
        form.fields['participants'].queryset = User.objects.filter(id__in=user_ids)
        return form
    
    def form_valid(self, form):
        form.instance.company = self.get_company()
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, 'Event created successfully.')
        return response
    
    def get_success_url(self):
        return reverse_lazy('calendar-event-list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['segment'] = 'calendar'
        context['form_title'] = 'Create New Event'
        return context


class CalendarEventUpdateView(CompanyMixin, generic.UpdateView):
    model = CalendarEvent
    form_class = CalendarEventForm
    template_name = 'core/calendar/calendar_event_form.html'
    
    def get_queryset(self):
        return CalendarEvent.objects.filter(company=self.get_company())
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        company = self.get_company()
        # Filter participants to only include users from this company
        # Get users that belong to this company through their profiles
        user_ids = company.members.values_list('user_id', flat=True)
        form.fields['participants'].queryset = User.objects.filter(id__in=user_ids)
        return form
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Event updated successfully.')
        return response
    
    def get_success_url(self):
        return reverse_lazy('calendar-event-list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['segment'] = 'calendar'
        context['form_title'] = 'Update Event'
        return context


class CalendarEventDetailView(CompanyMixin, generic.DetailView):
    model = CalendarEvent
    template_name = 'core/calendar/calendar_event_detail.html'
    context_object_name = 'event'
    
    def get_queryset(self):
        return CalendarEvent.objects.filter(company=self.get_company())
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['segment'] = 'calendar'
        return context


class CalendarEventDeleteView(CompanyMixin, generic.DeleteView):
    model = CalendarEvent
    template_name = 'core/calendar/calendar_event_confirm_delete.html'
    
    def get_queryset(self):
        return CalendarEvent.objects.filter(company=self.get_company())
    
    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, 'Event deleted successfully.')
        return response
    
    def get_success_url(self):
        return reverse_lazy('calendar-event-list')


@require_http_methods(["GET"])
def calendar_events_json(request):
    """API endpoint for FullCalendar to fetch events.
    
    Args:
        request: The HTTP request object.
        
    Returns:
        JsonResponse: A JSON response containing the calendar events.
    """
    if not request.user.is_authenticated:
        logger.warning("User not authenticated in calendar_events_json")
        return JsonResponse([], safe=False)
    
    start = request.GET.get('start')
    end = request.GET.get('end')
    
    logger.info(f"Calendar events requested for range: {start} to {end}")
    
    try:
        # If no date range is provided, use a default range (current month + next month)
        if not start or not end:
            today = datetime.now()
            start_date = datetime(today.year, today.month, 1)
            if today.month == 12:
                end_date = datetime(today.year + 1, 1, 1)
            else:
                end_date = datetime(today.year, today.month + 2, 1)
            logger.info(f"Using default date range: {start_date} to {end_date}")
        else:
            # Convert string dates to datetime objects
            start_date = datetime.strptime(start, '%Y-%m-%d')
            end_date = datetime.strptime(end, '%Y-%m-%d')
        
        # Make the end date inclusive
        end_date = end_date + timedelta(days=1)
        
        # Get the user's company
        company = None
        if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'company'):
            company = request.user.profile.company
            logger.info(f"Found company for user: {company}")
        else:
            logger.warning(f"No company found for user: {request.user.username}")
        
        # Get events for the date range and company
        events_query = CalendarEvent.objects.all()
        
        # Apply date range filter
        events_query = events_query.filter(
            start_date__lt=end_date,
            end_date__gt=start_date
        )
        
        # Apply company filter if available
        if company:
            events_query = events_query.filter(company=company)
        
        events = events_query.order_by('start_date')
        logger.info(f"Found {events.count()} events for date range {start_date} to {end_date}")
        
        # Format events for FullCalendar
        events_data = []
        for event in events:
            # Debug output for each event
            logger.info(f"Processing event: {event.id} - {event.title} - {event.start_date} to {event.end_date}")
            
            event_data = {
                'id': event.id,
                'title': event.title,
                'start': event.start_date.isoformat(),
                'end': event.end_date.isoformat(),
                'allDay': event.all_day,
                'className': f'bg-{event.theme}',
                'description': event.description or '',
                'url': reverse_lazy('calendar-event-detail', kwargs={'pk': event.id}),
            }
            events_data.append(event_data)
        
        return JsonResponse(events_data, safe=False)
    except Exception as e:
        logger.error(f"Error in calendar_events_json: {str(e)}", exc_info=True)
        return JsonResponse([], safe=False)
