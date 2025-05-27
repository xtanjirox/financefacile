
document.addEventListener('DOMContentLoaded', function () {
    var calendarEl = document.getElementById('dashboard-calendar');

    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: ''
        },
        height: 'auto',
        events: function (info, successCallback, failureCallback) {
            // Calculate start and end dates for the API request
            const startDate = info.start;
            const endDate = info.end;

            // Format dates for API
            const startStr = startDate.toISOString().split('T')[0];
            const endStr = endDate.toISOString().split('T')[0];

            console.log(`Dashboard: Fetching events from ${startStr} to ${endStr}`);

            // Add a timestamp to prevent caching
            const timestamp = new Date().getTime();

            // Make API request
            fetch(`/app/calendar/events/?start=${startStr}&end=${endStr}&_=${timestamp}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json'
                }
            })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! Status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    console.log('Dashboard: Fetched events:', data);
                    if (data && data.length > 0) {
                        // Use the real events from the API
                        successCallback(data);
                    } else {
                        // If no events found, show sample events for the current date
                        const today = new Date();
                        const year = today.getFullYear();
                        const month = today.getMonth();
                        const day = today.getDate();

                        // Create sample events only if no real events exist
                        const sampleEvents = [
                            {
                                id: 'sample-1',
                                title: 'Client Meeting',
                                start: new Date(year, month, day, 10, 0),
                                end: new Date(year, month, day, 11, 30),
                                backgroundColor: '#4e73df',
                                borderColor: '#4e73df',
                                textColor: '#ffffff',
                                url: '/app/calendar/date/' + year + '/' + (month + 1) + '/' + day + '/',
                                allDay: false
                            },
                            {
                                id: 'sample-2',
                                title: 'Team Standup',
                                start: new Date(year, month, day, 9, 0),
                                end: new Date(year, month, day, 9, 30),
                                backgroundColor: '#36b9cc',
                                borderColor: '#36b9cc',
                                textColor: '#ffffff',
                                url: '/app/calendar/date/' + year + '/' + (month + 1) + '/' + day + '/',
                                allDay: false
                            }
                        ];

                        successCallback(sampleEvents);
                    }
                })
                .catch(error => {
                    console.error('Error fetching events:', error);
                    failureCallback(error);

                    // Show sample events as fallback on error
                    const today = new Date();
                    const year = today.getFullYear();
                    const month = today.getMonth();
                    const day = today.getDate();

                    const fallbackEvents = [
                        {
                            id: 'sample-1',
                            title: 'Client Meeting',
                            start: new Date(year, month, day, 10, 0),
                            end: new Date(year, month, day, 11, 30),
                            backgroundColor: '#4e73df',
                            borderColor: '#4e73df',
                            textColor: '#ffffff',
                            url: '/app/calendar/date/' + year + '/' + (month + 1) + '/' + day + '/',
                            allDay: false
                        }
                    ];

                    successCallback(fallbackEvents);
                });
        },
        eventClick: function (info) {
            info.jsEvent.preventDefault();
            if (info.event.url) {
                window.location.href = info.event.url;
            }
        },
        dayMaxEvents: 2, // Show a maximum of 2 events per day
        dayMaxEventRows: 2, // Show a maximum of 2 events per day
        eventOrder: 'start,-duration',
        eventDisplay: 'block',
        displayEventTime: true,
        displayEventEnd: false,
        eventTimeFormat: {
            hour: '2-digit',
            minute: '2-digit',
            meridiem: false
        },
        // Add a date click handler to redirect to the date events page
        dateClick: function (info) {
            // Format the date as YYYY/MM/DD
            const dateStr = info.dateStr.split('T')[0];
            const [year, month, day] = dateStr.split('-');

            // Redirect to the date events page
            window.location.href = `/app/calendar/date/${year}/${month}/${day}/`;
        },
        // Add a "more" link when there are more events than can be displayed
        moreLinkClick: function (info) {
            // Prevent default behavior
            info.jsEvent.preventDefault();

            // Get the date
            const date = info.date;
            const year = date.getFullYear();
            const month = date.getMonth() + 1; // getMonth() is zero-based
            const day = date.getDate();

            // Redirect to the date events page
            window.location.href = `/app/calendar/date/${year}/${month}/${day}/`;

            return false; // Prevent default FullCalendar behavior
        },
        // Custom event rendering to make events more visually appealing
        eventContent: function (arg) {
            let timeText = '';
            if (!arg.event.allDay) {
                const startTime = arg.event.start.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                timeText = `<div class="fc-event-time">${startTime}</div>`;
            }

            const title = arg.event.title;
            const titleHtml = `<div class="fc-event-title">${title}</div>`;

            return { html: `<div class="fc-event-main">${timeText}${titleHtml}</div>` };
        },
        eventTimeFormat: {
            hour: '2-digit',
            minute: '2-digit',
            hour12: true
        },
        eventContent: function (arg) {
            // Skip rendering for the "more" link as we'll handle it in dayCellContent
            if (arg.event.extendedProps.isMoreLink) {
                return { html: '' }; // Empty content, we'll handle it in dayCellContent
            }

            // Regular event content
            var titleEl = document.createElement('div');
            titleEl.classList.add('fc-event-title');
            titleEl.textContent = arg.event.title;

            var timeEl = document.createElement('div');
            timeEl.classList.add('fc-event-time');

            if (arg.event.allDay) {
                timeEl.textContent = 'All day';
            } else {
                var startTime = arg.event.start ? arg.timeText : '';
                var endTime = arg.event.end ? ' - ' + arg.event.end.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '';
                timeEl.textContent = startTime + endTime;
            }

            var wrapper = document.createElement('div');
            wrapper.appendChild(timeEl);
            wrapper.appendChild(titleEl);

            return { domNodes: [wrapper] };
        },
        dayCellContent: function (arg) {
            // Create the default content
            const dayNumberEl = document.createElement('div');
            dayNumberEl.classList.add('fc-daygrid-day-number');
            dayNumberEl.textContent = arg.dayNumberText.replace('\n', '');

            // Create a container for the day cell content
            const container = document.createElement('div');
            container.classList.add('fc-daygrid-day-top');
            container.appendChild(dayNumberEl);

            // Return the default content
            return { domNodes: [container] };
        },
        moreLinkClick: 'day', // When "more" link is clicked, go to day view
        moreLinkContent: function (arg) {
            // Create a custom "more" link
            const link = document.createElement('a');
            link.href = '#';
            link.classList.add('fc-more-link');
            link.textContent = arg.num.toString() + ' more';
            link.dataset.date = arg.date.toISOString().split('T')[0];

            // Add click handler
            link.addEventListener('click', function (e) {
                e.preventDefault();
                const dateStr = this.dataset.date;
                window.location.href = `{% url 'calendar-event-list' %}?date=${dateStr}`;
            });

            return { domNodes: [link] };
        },
        eventDidMount: function (arg) {
            if (arg.event.extendedProps.theme && !arg.event.extendedProps.isMoreLink) {
                arg.el.classList.add('fc-event-theme-' + arg.event.extendedProps.theme);
            }
        }
    });

    calendar.render();

    // Refresh calendar when navigating back to the page
    document.addEventListener('visibilitychange', function () {
        if (!document.hidden) {
            calendar.refetchEvents();
        }
    });
});
