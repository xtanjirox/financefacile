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

from core.forms import CalendarEventForm, CalendarEventFilterForm
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
        queryset = CalendarEvent.objects.filter(
            company=self.get_company()
        ).select_related('created_by')
        
        # Apply filters from form
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        themes = self.request.GET.getlist('theme')
        
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
                queryset = queryset.filter(start_date__gte=start_date)
            except ValueError:
                pass
                
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
                # Add one day to include the end date fully
                end_date = end_date + timedelta(days=1)
                queryset = queryset.filter(start_date__lt=end_date)
            except ValueError:
                pass
                
        if themes:
            queryset = queryset.filter(theme__in=themes)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['segment'] = 'calendar'
        
        # Add additional context for filtering
        now = datetime.now()
        upcoming_events = CalendarEvent.objects.filter(
            company=self.get_company(),
            start_date__gte=now,
            start_date__lte=now + timedelta(days=7)
        )
        all_day_events = CalendarEvent.objects.filter(
            company=self.get_company(),
            all_day=True
        )
        
        context['upcoming_events'] = upcoming_events
        context['all_day_events'] = all_day_events
        
        # Create filter form
        theme_choices = [(k, v) for k, v in dict(CalendarEvent.THEME_CHOICES).items()]
        filter_form = CalendarEventFilterForm(
            data=self.request.GET,
            theme_choices=theme_choices
        )
        
        context['filter_form'] = filter_form
        context['page_title'] = 'Calendar Events'
        context['page_title_badge'] = 'Calendar Events'
        return context


class CalendarEventCreateView(CompanyMixin, generic.CreateView):
    model = CalendarEvent
    form_class = CalendarEventForm
    template_name = 'core/calendar/calendar_event_form.html'
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        company = self.get_company()
        # Filter participants to only include users from this company
        from django.contrib.auth.models import User
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
        context['page_title'] = 'Create Event'
        context['page_title_badge'] = 'Create Event'
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
        from django.contrib.auth.models import User
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
        context['page_title'] = 'Update Event'
        context['page_title_badge'] = 'Update Event'
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
        context['page_title'] = 'Event Detail'
        context['page_title_badge'] = 'Event Detail'
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
            try:
                start_date = datetime.fromisoformat(start.replace('Z', '+00:00'))
                end_date = datetime.fromisoformat(end.replace('Z', '+00:00'))
            except ValueError:
                # Fallback to older format if ISO format fails
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
        
        # Also include events where the current user is a participant
        user_events = CalendarEvent.objects.filter(participants=request.user)
        events = (events_query | user_events).distinct().order_by('start_date')
        
        logger.info(f"Found {events.count()} events for date range {start_date} to {end_date}")
        
        # Format events for FullCalendar
        events_data = []
        for event in events:
            # Debug output for each event
            logger.info(f"Processing event: {event.id} - {event.title} - {event.start_date} to {event.end_date}")
            
            # Get theme color
            theme_colors = {
                'primary': '#4e73df',
                'secondary': '#858796',
                'success': '#1cc88a',
                'info': '#36b9cc',
                'warning': '#f6c23e',
                'danger': '#e74a3b',
                'dark': '#5a5c69',
            }
            color = theme_colors.get(event.theme, '#4e73df')  # Default to primary if theme not found
            
            event_data = {
                'id': event.id,
                'title': event.title,
                'start': event.start_date.isoformat(),
                'end': event.end_date.isoformat(),
                'allDay': event.all_day,
                'description': event.description or '',
                'backgroundColor': color,
                'borderColor': color,
                'textColor': '#ffffff' if event.theme != 'warning' else '#5a5c69',  # Dark text for light backgrounds
                'url': str(reverse_lazy('calendar-event-detail', kwargs={'pk': event.pk})),
                'className': f"bg-{event.theme}",  # Add class for additional styling
                'editable': True,
            }
            events_data.append(event_data)
            logger.debug(f"Added event to response: {event.title} on {event.start_date}")
        
        # If no events found, return an empty array (this is normal)
        if not events_data:
            logger.info("No events found for the requested date range")
            return JsonResponse([], safe=False)
        
        # Debug output for the final response
        logger.info(f"Returning {len(events_data)} events")
        return JsonResponse(events_data, safe=False)
        
    except Exception as e:
        logger.error("Error in calendar_events_json: %s", str(e), exc_info=True)
        return JsonResponse([], safe=False)


def date_events(request, year, month, day):
    """View to display events for a specific date.
    
    Args:
        request: The HTTP request object.
        year: The year of the date to show events for.
        month: The month of the date to show events for.
        day: The day of the date to show events for.
        
    Returns:
        HttpResponse: Rendered template with events for the specified date.
    """
    try:
        # Parse the date from URL parameters
        date_str = f"{year}-{month:02d}-{day:02d}"
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        next_day = target_date + timedelta(days=1)
        
        # Get the user's company
        company = None
        if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'company'):
            company = request.user.profile.company
        
        # Get events for the specified date
        events = CalendarEvent.objects.filter(
            start_date__lt=next_day,
            end_date__gt=target_date,
            company=company
        ).order_by('start_date')
        
        context = {
            'date': target_date,
            'events': events,
            'segment': 'calendar',
        }
        
        return render(request, 'core/calendar/date_events.html', context)
        
    except Exception as e:
        logger.error("Error in date_events: %s", str(e), exc_info=True)
        messages.error(request, 'An error occurred while fetching events for this date.')
        return render(request, 'core/calendar/date_events.html', {
            'date': None,
            'events': [],
            'segment': 'calendar',
            'error': str(e)
        })
