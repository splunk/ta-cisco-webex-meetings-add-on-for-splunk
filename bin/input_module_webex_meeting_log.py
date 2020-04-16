
# encoding = utf-8

import os
import sys
import time
import datetime
import requests
import xml.etree.ElementTree as ET
from io import StringIO
from collections import defaultdict
from xml.etree import cElementTree as ETree
import json
from MaxStack_list import MaxStack_list


DEBUG_WRITEEV = True
tag_map = {
    "LstmeetingusageHistory": "meetingUsageHistory",
    "LsteventsessionHistory": "eventSessionHistory",
    "LstrecordaccessHistory": "recordAccessHistory",
    "LstsupportsessionHistory": "supportSessionHistory",
    "LsttrainingsessionHistory": "trainingSessionHistory",
    "LstsummaryMeeting": "meeting",
    "LstsummarySession": "session"
}

sourcetype_map = {
    "LstmeetingusageHistory": "cisco:webex:meetingusagehistory:list",
    "LsteventsessionHistory": "cisco:webex:eventsessionhistory:list",
    "LstrecordaccessHistory": "cisco:webex:recordaccesshistory:list",
    "LstsupportsessionHistory": "cisco:webex:supportsessionhistory:list",
    "LsttrainingsessionHistory": "cisco:webex:trainingsessionhistory:list",
    "LstsummaryMeeting": "cisco:webex:meeting:list",
    "LstsummarySession": "cisco:webex:session:list"
}

# use this for timestamp checkpoint
# remove it if offset work
timestamp_map = {
    "LstmeetingusageHistory": "meetingStartTime",
    "LsteventsessionHistory": "sessionStartTime",
    "LstrecordaccessHistory": "creationTime",
    "LstsupportsessionHistory": "sessionStartTime",
    "LsttrainingsessionHistory": "sessionStartTime",
    "LstsummaryMeeting": "startDate",
    "LstsummarySession": "startTime"
}
maxStack = MaxStack_list()
timezone = 20  # "4": "GMT-08:00, Pacific",

'''
    IMPORTANT
    Edit only the validate_input and collect_events functions.
    Do not edit any other part in this file.
    This file is generated only once when creating the modular input.
'''
'''
# For advanced users, if you want to create single instance mod input, uncomment this method.
def use_single_instance_mode():
    return True
'''


def validate_input(helper, definition):
    """Implement your own validation logic to validate the input stanza configurations"""
    # This example accesses the modular input variable
    # site_nmae = definition.parameters.get('site_nmae', None)
    # username = definition.parameters.get('username', None)
    # password = definition.parameters.get('password', None)
    # start_time_start = definition.parameters.get('start_time_start', None)
    # start_time_end = definition.parameters.get('start_time_end', None)
    start_time_start = definition.parameters.get('start_time_start', None)
    start_time_end = definition.parameters.get('start_time_end', None)
    live = definition.parameters.get('live', None)

    if live == "1" and start_time_start:
        raise ValueError(
            "Start time is not required for Continuous Monitoring. '{}' live:{}, start_time_start:{}".format(live, type(live), type(start_time_start)))

    try:
        # if not live:
        if start_time_start:
            datetime.datetime.strptime(
                start_time_start, '%m/%d/%Y %H:%M:%S')
        if start_time_end:
            datetime.datetime.strptime(start_time_end, '%m/%d/%Y %H:%M:%S')
    except ValueError:
        raise ValueError(
            "Incorrect data format, time should be MM/DD/YYYY hh:mm:ss")
    pass


def collect_events(helper, ew):
    """Implement your data collection logic here

    """
    opt_site_name = helper.get_arg('site_nmae')
    opt_username = helper.get_arg('username')
    opt_password = helper.get_arg('password')
    opt_start_time_start = helper.get_arg('start_time_start')
    # opt_start_time_end = helper.get_arg('start_time_end')
    opt_endpoints = helper.get_arg('endpoint')
    opt_interval = int(helper.get_arg('interval'))
    # opt_timezone = helper.get_arg('timezone')
    opt_live = helper.get_arg('live')

    helper.log_info("[-] WebEx API Endpoint: {}".format(opt_endpoints))
    helper.log_info("[-] WebEx interval: {}".format(opt_interval))
    helper.log_info(
        "[-] WebEx isLive: {} - {}".format(opt_live, type(opt_live)))
    # ## Feature: To handle saml and oauth: password_type
    '''
    Docs: https://developer.cisco.com/docs/webex-xml-api-reference-guide/#!request-authentication/request-authentication
    OAuth = webExAccessToken
    SAML SSO = sessionTicket

    password_type = helper.get_arg('password_type')
    '''
    password_type = "password"

    # ## Feature: partner ID
    '''
    <partnerID>{partnertID}<partnerID>
    <siteID>{siteID}<siteID>
    '''

    # Live data - time slice
    # start time = last_run
    # end time = now() in user selected time zone
    limit = 500
    if opt_live is True:
        # do the time magic
        # run the unique endpoint
        # End time : time.now -> convert to epoch
        # Start time : end time - 600
        # Then query the live session endpoint with these parameters, along with timezone (if applicable)
        # opt_interval = 600
        opt_endpoint = "LstsummarySession"
        key = "{}_{}_processing".format(
            helper.get_input_stanza_names(), opt_endpoint)
        start_time = helper.get_check_point(key)
        if start_time:
            start_time = datetime.datetime.strptime(
                start_time, '%m/%d/%Y %H:%M:%S').strftime("%s")
            start_time = int(start_time) + 1
            start_time = datetime.datetime.fromtimestamp(
                int(start_time)).strftime('%m/%d/%Y %H:%M:%S')

        end_time_epoch = datetime.datetime.utcnow().strftime("%s")

        if start_time is None:
            start_time = int(end_time_epoch) - opt_interval + 1
            helper.log_debug("type of start time: {}".format(type(start_time)))
            helper.log_debug("***start time***: {}".format(start_time))
            start_time = datetime.datetime.fromtimestamp(
                int(start_time)).strftime('%m/%d/%Y %H:%M:%S')

        helper.log_debug("type of start time: {}".format(type(start_time)))
        helper.log_debug("---start time---: {}".format(start_time))

        end_time = datetime.datetime.fromtimestamp(
            int(end_time_epoch)).strftime('%m/%d/%Y %H:%M:%S')
        helper.log_debug("start time: {}".format(start_time))
        helper.log_debug("end time: {}".format(end_time))
        offset = 1
        records = limit

        while (records == limit):
            helper.log_debug("current_offset: {}".format(offset))
            records = fetch_webex_logs_live(opt_username, opt_password, opt_site_name,
                                            start_time, end_time, offset, limit, ew, helper, key, password_type, opt_endpoint, end_time_epoch)
            if records:
                offset += records

    # Historical Data (offset works)
    if opt_live is not True:
        helper.log_debug("Historical Data")
        for opt_endpoint in opt_endpoints:
            helper.log_debug("[-] \t At {}".format(opt_endpoint))

            opt_start_time_end = "04/10/2050 10:30:34"

            end_time = datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S')

            # create checkpoint key for offest and timestamp
            timestamp_key = "timestamp_{}_{}_processing".format(
                helper.get_input_stanza_names(), opt_endpoint)

            start_time = helper.get_check_point(timestamp_key)
            if start_time is None:
                start_time = opt_start_time_start
            else:
                # shift the starttime by 1 second
                start_time = datetime.datetime.strptime(
                    start_time, '%m/%d/%Y %H:%M:%S').strftime("%s")
                start_time = int(start_time) + 1
                start_time = datetime.datetime.fromtimestamp(
                    int(start_time)).strftime('%m/%d/%Y %H:%M:%S')

            offset = 1
            records = limit
            maxStack.empty()

            helper.log_debug("start time: {}".format(start_time))
            helper.log_debug("end time: {}".format(end_time))
            while (records == limit):
                helper.log_debug("Go to fetch")
                helper.log_debug("current_offset: {}".format(offset))
                records = fetch_webex_logs(opt_username, opt_password, opt_site_name,
                                           start_time, end_time, offset, limit, ew, helper, password_type, opt_endpoint, timestamp_key)
                helper.log_debug("\t Offet:{}\tLimit: {}\tRecords Returned: {}".format(
                    offset, limit, records))
                if records:
                    offset += records


def fetch_webex_logs_live(opt_username, opt_password, opt_site_name,
                          opt_start_time_start, opt_start_time_end, offset, limit, ew, helper, key, password_type, opt_endpoint, end_time_epoch):

    url = "https://{}.webex.com/WBXService/XMLService".format(opt_site_name)

    headers = {
        'Content-Type': 'application/xml'
    }

    # Build Payload
    payload = xml_format(opt_username, opt_password, opt_site_name,
                         opt_start_time_start, opt_start_time_end, offset, limit, password_type, opt_endpoint, helper, timezone)

    # debug_index(payload, ew, helper, opt_endpoint)
    # REMOTE THIS LATER
    helper.log_debug("[-] Debug Fetch Request: {} - {}".format(offset, limit))

    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        if response.status_code != 200:
            helper.log_debug(
                "\t[-] WebEx Meetings API Error: {}".format(response.text))

        events = response.text
        ev = parse_xml_to_dict(events)
        records = 0

        ev = ev['message']

        response_key = tag_map[opt_endpoint]
        if "header" in ev:
            if "SUCCESS" in ev["header"]["response"]["result"]:
                conferences = ev["body"]["bodyContent"][response_key]

                if isinstance(conferences, list):
                    for event in conferences:
                        returned_time = datetime.datetime.strptime(
                            event['startTime'], '%m/%d/%Y %H:%M:%S').strftime("%s")
                        helper.log_debug(
                            "\t\t\t[-] {}>{}  ?".format(end_time_epoch, returned_time))

                        if end_time_epoch >= returned_time:  # Checking if the event started early
                            dump_it_in_index(event, ew, helper, opt_endpoint)
                        else:
                            helper.log_debug(
                                "\t\t\t[-] Skipped an event. {} ".format(event))

                else:
                    returned_time = datetime.datetime.strptime(
                        conferences['startTime'], '%m/%d/%Y %H:%M:%S').strftime("%s")
                    helper.log_debug(
                        "\t\t\t[-] {}>{}  ?".format(end_time_epoch, returned_time))
                    if end_time_epoch >= returned_time:  # Checking if the event started early
                        dump_it_in_index(conferences, ew, helper,
                                         opt_endpoint)
                    else:
                        helper.log_debug(
                            "\t\t\t[-] Skipped an event. {} ".format(conferences))
                # Save last end_time
                helper.save_check_point(key, opt_start_time_end)

                # Record Meta Data
                matchingRecords = ev["body"]["bodyContent"]['matchingRecords']
                if "returned" in matchingRecords:
                    records = int(matchingRecords['returned'])
                    return records
                else:
                    helper.log_debug(
                        "[-] WebEx Empty records: {}".format(repr(records)))
            elif "no record found" in ev["header"]["response"]["reason"]:
                return 0
            else:
                helper.log_info(
                    "[-] WebEx Response: {}".format(repr(ev["header"]["response"]["reason"])))
        else:
            helper.log_info("Condition not match for : {}".format(repr(ev)))

    except Exception as e:
        helper.save_check_point(key, opt_start_time_start)
        helper.log_info(
            "[-] WebEx Request Failed (Check URL and Given Error): {}".format(repr(e)))
        raise e


def fetch_webex_logs(opt_username, opt_password, opt_site_name,
                     opt_start_time_start, opt_start_time_end, offset, limit, ew, helper, password_type, opt_endpoint, timestamp_key):
    helper.log_debug("== Historcial Data log ==")
    url = "https://{}.webex.com/WBXService/XMLService".format(opt_site_name)

    headers = {
        'Content-Type': 'application/xml'
    }

    # Build Payload
    payload = xml_format(opt_username, opt_password, opt_site_name,
                         opt_start_time_start, opt_start_time_end, offset, limit, password_type, opt_endpoint, helper, timezone)

    helper.log_debug("[-] Debug Fetch Request: {} - {}".format(offset, limit))

    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        if response.status_code != 200:
            helper.log_debug(
                "\t[-] WebEx Meetings API Error: {}".format(response.text))

        events = response.text
        ev = parse_xml_to_dict(events)
        records = 0

        ev = ev['message']
        response_key = tag_map[opt_endpoint]

        if "header" in ev:
            if "SUCCESS" in ev["header"]["response"]["result"]:
                conferences = ev["body"]["bodyContent"][response_key]
                helper.log_debug("Start to dump data")
                if isinstance(conferences, list):
                    for event in conferences:
                        dump_historical_data_in_index(event, ew, helper,
                                                      opt_endpoint, timestamp_key)
                else:
                    dump_historical_data_in_index(conferences, ew, helper,
                                                  opt_endpoint, timestamp_key)

                # Record Meta Data
                matchingRecords = ev["body"]["bodyContent"]['matchingRecords']
                if "returned" in matchingRecords:
                    records = int(matchingRecords['returned'])
                    helper.log_debug(
                        "[-] Returned Records: {}".format(repr(records)))
                    return records
                else:
                    helper.log_debug(
                        "[-] WebEx Empty records: {}".format(repr(records)))
            elif "no record found" in ev["header"]["response"]["reason"]:
                helper.log_debug("[-] WebEx Empty records: 0")
                helper.log_debug(
                    "[-] WebEx Response: {}".format(repr(ev["header"]["response"]["reason"])))
                return 0
            else:
                helper.log_debug(
                    "[-] WebEx Response: {}".format(repr(ev["header"]["response"]["reason"])))
        else:
            helper.log_info("Condition not match for : {}".format(repr(ev)))

    except Exception as e:
        helper.log_info(
            "[-] WebEx Request Failed (Check URL and Given Error): {}".format(repr(e)))
        raise e


"""
def debug_index(event, ew, helper, opt_endpoint):
    if DEBUG_WRITEEV:
        dump_it_in_index(event, ew, helper, opt_endpoint)
"""


def dump_it_in_index(event, ew, helper, opt_endpoint):
    if isinstance(event, dict):
        event = json.dumps(event)

    try:
        ev = helper.new_event(event, time=None, host=None,
                              index=None, source=None, sourcetype=sourcetype_map[opt_endpoint], done=True, unbroken=True)
        ew.write_event(ev)
    except Exception as e:
        helper.log_info("[-] WebEx Meetings Event Exception {}".format(e))


def dump_historical_data_in_index(event, ew, helper, opt_endpoint, timestamp_key):
    if isinstance(event, dict):
        time_tag = timestamp_map[opt_endpoint]
        this_event_time = event[time_tag]
        event = json.dumps(event)
    try:
        ev = helper.new_event(event, time=None, host=None,
                              index=None, source=None, sourcetype=sourcetype_map[opt_endpoint], done=True, unbroken=True)
        ew.write_event(ev)

        # update the checkpoint for timestamp
        timestamp = helper.get_check_point(timestamp_key)

        # convert to epoch time
        if timestamp is None:
            timestamp = this_event_time
            helper.save_check_point(timestamp_key, timestamp)
            #helper.log_info("timestamp: {}".format(timestamp))
        else:
            timestamp = datetime.datetime.strptime(
                timestamp, '%m/%d/%Y %H:%M:%S').strftime("%s")
            this_event_time = datetime.datetime.strptime(
                this_event_time, '%m/%d/%Y %H:%M:%S').strftime("%s")
            maxStack.push(int(this_event_time))
            current_max_time = maxStack.peekMax()
            helper.log_debug(
                "\t [-] Size of stack: {}".format(maxStack.size()))
            helper.log_debug(
                "\t [-] Time: this_event_time: {}".format(this_event_time))
            helper.log_debug(
                "\t [-] Time: current_max_time: {}".format(current_max_time))
            timestamp = max(int(timestamp), current_max_time)
            helper.log_debug("\t\t[-]time: timestamp: {}".format(timestamp))
            helper.save_check_point(timestamp_key, datetime.datetime.fromtimestamp(
                int(timestamp)).strftime('%m/%d/%Y %H:%M:%S'))

    except Exception as e:
        helper.log_info("[-] WebEx Meetings Event Exception {}".format(e))


# ETREE to dict
def etree_to_dict(t):
    d = {t.tag: {} if t.attrib else None}
    children = list(t)
    if children:
        dd = defaultdict(list)
        for dc in map(etree_to_dict, children):
            for k, v in dc.items():
                dd[k].append(v)
        d = {t.tag: {k: v[0] if len(v) == 1 else v for k, v in dd.items()}}
    if t.attrib:
        d[t.tag].update(('@' + k, v) for k, v in t.attrib.items())
    if t.text:
        text = t.text.strip()
        if children or t.attrib:
            if text:
                d[t.tag]['#text'] = text
        else:
            d[t.tag] = text
    return d


def parse_xml_to_dict(xml_string):
    it = ET.iterparse(StringIO(xml_string))
    for _, el in it:
        prefix, has_namespace, postfix = el.tag.partition('}')
        if has_namespace:
            el.tag = postfix  # strip all namespaces
    root = it.root
    return etree_to_dict(root)


def xml_format(username, password, site_name, start_time_start, start_time_end, offset, limit, password_type, endpoint, helper, timezone):

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
