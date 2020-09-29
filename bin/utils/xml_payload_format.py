def xml_format(params):

    # Assign param to appropriate payload values
    username = params['opt_username']
    password = params['opt_password']
    site_name = params['opt_site_name']
    start_time = params['start_time']
    end_time = params['end_time']
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
    TimeScope = ""
    if endpoint == "LstmeetingusageHistory" or endpoint == "LsttrainingsessionHistory" or endpoint == "LsteventsessionHistory":
        endpoint = "java:com.webex.service.binding.history.{}".format(
            endpoint)

        TimeScope = '''
                        <endTimeScope>
                            <sessionEndTimeStart>{start_time}</sessionEndTimeStart>
                            <sessionEndTimeEnd>{end_time}</sessionEndTimeEnd>
                        </endTimeScope>
        '''.format(start_time=start_time, end_time=end_time)
    elif endpoint == "LstmeetingattendeeHistory" or endpoint == "LsteventattendeeHistory" or endpoint == "LstsupportattendeeHistory" or endpoint == "LsttrainingattendeeHistory":
        endpoint = "java:com.webex.service.binding.history.{}".format(
            endpoint)
        TimeScope = '''
                        <endTimeScope>
                            <sessionEndTimeStart>{start_time}</sessionEndTimeStart>
                            <sessionEndTimeEnd>{end_time}</sessionEndTimeEnd>
                        </endTimeScope>
        '''.format(start_time=start_time, end_time=end_time)
    elif endpoint == "LstsupportsessionHistory":
        endpoint = "java:com.webex.service.binding.history.{}".format(
            endpoint)
        TimeScope = '''
                        <endTimeScope>
                            <sessionEndTimeStart>{start_time}</sessionEndTimeStart>
                            <sessionEndTimeEnd>{end_time}</sessionEndTimeEnd>
                        </endTimeScope>
        '''.format(start_time=start_time, end_time=end_time)
        order = '''
            <order>
                <orderBy>CONFID</orderBy>
                <orderAD>ASC</orderAD>
            </order >
        '''
    elif endpoint == "LstrecordaccessHistory":
        endpoint = "java:com.webex.service.binding.history.{}".format(
            endpoint)
        TimeScope = '''
                        <creationTimeScope>
                            <creationTimeStart>{start_time}</creationTimeStart>
                            <creationTimeEnd>{end_time}</creationTimeEnd>
                        </creationTimeScope>
        '''.format(start_time=start_time, end_time=end_time)
        order = '''
            <order>
                <orderBy>RECORDID</orderBy>
                <orderAD>ASC</orderAD>
            </order >
        '''
    elif endpoint == "LstsummarySession":
        endpoint = "java:com.webex.service.binding.ep.{}".format(
            endpoint)
        TimeScope = '''
                    <dateScope>
                        <startDateStart>{start_time}</startDateStart>
                        <startDateEnd>{end_time}</startDateEnd>
                        <timeZoneID>{timezone}</timeZoneID>
                    </dateScope>
        '''.format(start_time=start_time, end_time=end_time, timezone=timezone)
    else:
        TimeScope = ""

    # Final Payload
    payload = """<?xml version="1.0" encoding="UTF-8"?>
    <serv:message xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <header>{auth}</header>
        <body>
            <bodyContent xsi:type="{endpoint}">
                {TimeScope}
                <listControl>
                    <startFrom>{offset}</startFrom>
                    <maximumNum>{limit}</maximumNum>
                    <listMethod>AND</listMethod>
                </listControl>
                {order}
            </bodyContent>
        </body>
    </serv:message>""".format(auth=auth, endpoint=endpoint, TimeScope=TimeScope, offset=offset, limit=limit, order=order)
    return payload
