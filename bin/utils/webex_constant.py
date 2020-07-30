tag_map = {
    "LstmeetingattendeeHistory": "meetingAttendeeHistory",
    "LstmeetingusageHistory": "meetingUsageHistory",
    "LsteventsessionHistory": "eventSessionHistory",
    "LstrecordaccessHistory": "recordAccessHistory",
    "LstsupportsessionHistory": "supportSessionHistory",
    "LsttrainingsessionHistory": "trainingSessionHistory",
    "LstsummarySession": "session",
    "LsteventattendeeHistory": "eventAttendeeHistory",
    "LstsupportattendeeHistory": "supportAttendeeHistory",
    "LsttrainingattendeeHistory": "trainingAttendeeHistory"
}

sourcetype_map = {
    "LstmeetingattendeeHistory": "cisco:webex:meetings:history:meetingattendeehistory",
    "LstmeetingusageHistory": "cisco:webex:meetings:history:meetingusagehistory",
    "LsteventsessionHistory": "cisco:webex:meetings:history:eventsessionhistory",
    "LstrecordaccessHistory": "cisco:webex:meetings:history:recordaccesshistory",
    "LstsupportsessionHistory": "cisco:webex:meetings:history:supportsessionhistory",
    "LsttrainingsessionHistory": "cisco:webex:meetings:history:trainingsessionhistory",
    "LstsummarySession": "cisco:webex:meetings:general:summarysession",
    "LsteventattendeeHistory": "cisco:webex:meetings:history:eventattendeehistory",
    "LstsupportattendeeHistory": "cisco:webex:meetings:history:supportattendeehistory",
    "LsttrainingattendeeHistory": "cisco:webex:meetings:history:trainingattendeehistory"
}

# End time tag map: use this for timestamp checkpoint
timestamp_map = {
    "LstmeetingattendeeHistory": "leaveTime",
    "LstmeetingusageHistory": "meetingEndTime",
    "LsteventsessionHistory": "sessionEndTime",
    "LstrecordaccessHistory": "creationTime",
    "LstsupportsessionHistory": "sessionEndTime",
    "LsttrainingsessionHistory": "sessionEndTime",
    "LstsummarySession": "actualStartTime",
    "LsteventattendeeHistory": "endTime",
    "LstsupportattendeeHistory": "endTime",
    "LsttrainingattendeeHistory": "endTime"
}

# Start time tag map: use this for time extration
start_time_map = {
    "LstmeetingattendeeHistory": "joinTime",
    "LstmeetingusageHistory": "meetingStartTime",
    "LsteventsessionHistory": "sessionStartTime",
    "LstrecordaccessHistory": "creationTime",
    "LstsupportsessionHistory": "sessionStartTime",
    "LsttrainingsessionHistory": "sessionStartTime",
    "LstsummarySession": "actualStartTime",
    "LsteventattendeeHistory": "startTime",
    "LstsupportattendeeHistory": "startTime",
    "LsttrainingattendeeHistory": "startTime"
}

# webExAccessToken
authentication_type = {
    "Password Authentication": "password",
    "OAuth": "webExAccessToken",
    "SAML SSO": "sessionTicket"
}
