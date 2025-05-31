document.addEventListener('DOMContentLoaded', function () {
    // Get calendar events from Django context
    const calendarEvents = [
        {% for event in upcoming_events %}
            {
        id: "{{ event.id }}",
        title: "{{ event.title|escapejs }}",
        start: "{{ event.start_date|date:"c" }}",
                {% if event.end_date %}
end: "{{ event.end_date|date:"c" }}",
    {% endif %}
allDay: {% if event.all_day %} true{% else %} false{% endif %},
url: "{{ event.get_absolute_url }}",
    classNames: ["fc-event-theme-{{ event.theme|default:'primary' }}"],
        extendedProps: {
    description: "{{ event.description|default:''|escapejs }}"
}
            }{% if not forloop.last %}, {% endif %}
{% endfor %}
        ];

// Initialize the calendar
const calendarEl = document.getElementById('calendar');
if (calendarEl) {
    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay,listWeek'
        },
        events: calendarEvents,
        locale: 'fr',
        buttonText: {
            today: "Aujourd'hui",
            month: 'Mois',
            week: 'Semaine',
            day: 'Jour',
            list: 'Liste'
        },
        eventTimeFormat: {
            hour: '2-digit',
            minute: '2-digit',
            meridiem: false
        },
        firstDay: 1, // Monday
        eventClick: function (info) {
            if (info.event.url) {
                window.location.href = info.event.url;
                info.jsEvent.preventDefault(); // prevents browser from following link
            }
        },
        eventDidMount: function (info) {
            // Add tooltip with description if available
            if (info.event.extendedProps && info.event.extendedProps.description) {
                $(info.el).tooltip({
                    title: info.event.extendedProps.description,
                    placement: 'top',
                    trigger: 'hover',
                    container: 'body'
                });
            }
        }
    });

    calendar.render();
}
    });
