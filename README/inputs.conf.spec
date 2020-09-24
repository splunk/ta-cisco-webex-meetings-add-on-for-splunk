[general_service://<name>]
live = Use this to retrieve Active Session Data such as information for all service types, including Meeting Center, Training Center, Event Center, Sales Center, and Support Center.

[history_service://<name>]
endpoints = Choose the endpoints to retrieve data.  Note: Meeting Usage & Meeting Attendees endpoints helps populate Dashboard.
start_time_start = This is the time from where you want to ingest the historical data.  Please enter UTC time. Format: MM/DD/YYYY hh:mm:ssNOTE: Begin Date must be at least 3 days ago and ideally no more than 90 days.
paging_interval = This is used to slice the large time range. For example, if it is set to 1 day, the data will be ingested day by day.
paging_interval_unit = Choose the unit of the paging interval.