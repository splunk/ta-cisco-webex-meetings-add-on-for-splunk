def xml_format(params):

    # Assign param to appropriate payload values
    username = params['opt_username']
    password = params['opt_password']
    site_name = params['opt_site_name']
    start_time_start = params['start_time']
    start_time_end = params['end_time']
    offset = params['offset']
    limit = params['limit']
    password_type = params['password_type']
    endpoint = params['opt_endpoint']
    timezone = params['timezone']

    # Authentication Header
    auth = '''<securityContext>
                <webExID>{username}</webExID>
                <{password_type}>{password}</{password_type}>
                <siteName>{site_name}</siteName>
            </securityContext>
    ''' .format(username=username, password_type=password_type, password=password, site_name=site_name)

    # Order Header
    order = '''
            <order>
                <orderBy>STARTTIME</orderBy>
                <orderAD>ASC</orderAD>
            </order>
        '''
    # Endpooint specific Payload
    startTimeScope = ""
    if endpoint == "LstmeetingusageHistory" or endpoint == "LstsupportsessionHistory" or endpoint == "LsttrainingsessionHistory" or endpoint == "LsteventsessionHistory":
        endpoint = "java:com.webex.service.binding.history.{}".format(
            endpoint)

        startTimeScope = '''
                        <startTimeScope>
                            <sessionStartTimeStart>{start_time_start}</sessionStartTimeStart>
                            <sessionStartTimeEnd>{start_time_end}</sessionStartTimeEnd>
                        </startTimeScope>
        '''.format(start_time_start=start_time_start, start_time_end=start_time_end)
    elif endpoint == "LstmeetingattendeeHistory":
        endpoint = "java:com.webex.service.binding.history.{}".format(
            endpoint)
        startTimeScope = '''
                        <startTimeScope>
                            <sessionStartTimeStart>{start_time_start}</sessionStartTimeStart>
                            <sessionStartTimeEnd>{start_time_end}</sessionStartTimeEnd>
                        </startTimeScope>
        '''.format(start_time_start=start_time_start, start_time_end=start_time_end)
    elif endpoint == "LstrecordaccessHistory":
        endpoint = "java:com.webex.service.binding.history.{}".format(
            endpoint)
        startTimeScope = '''
                        <viewTimeScope>
                            <viewTimeStart>{start_time_start}</viewTimeStart>
                            <viewTimeEnd>{start_time_end}</viewTimeEnd>
                        </viewTimeScope>
        '''.format(start_time_start=start_time_start, start_time_end=start_time_end)
        order = '''
            <order>
                <orderBy>RECORDID</orderBy>
                <orderAD>ASC</orderAD>
            </order >
        '''
    elif endpoint == "LstsummarySession":
        endpoint = "java:com.webex.service.binding.ep.{}".format(
            endpoint)
        startTimeScope = '''
                    <dateScope>
                        <startDateStart>{start_time_start}</startDateStart>
                        <startDateEnd>{start_time_end}</startDateEnd>
                        <timeZoneID>{timezone}</timeZoneID>
                    </dateScope>
        '''.format(start_time_start=start_time_start, start_time_end=start_time_end, timezone=timezone)
    elif endpoint == "LstsummaryMeeting":
        endpoint = "java:com.webex.service.binding.meeting.{}".format(
            endpoint)
        startTimeScope = ""
    else:
        startTimeScope = ""

    # Final Payload
    payload = """<?xml version="1.0" encoding="UTF-8"?>
    <serv:message xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <header>{auth}</header>
        <body>
            <bodyContent xsi:type="{endpoint}">
                {startTimeScope}
                <listControl>
                    <startFrom>{offset}</startFrom>
                    <maximumNum>{limit}</maximumNum>
                    <listMethod>AND</listMethod>
                </listControl>
                {order}
            </bodyContent>
        </body>
    </serv:message>""".format(auth=auth, endpoint=endpoint, startTimeScope=startTimeScope, offset=offset, limit=limit, order=order)
    return payload
