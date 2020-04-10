
# encoding = utf-8

import os
import sys
import time
import datetime
import requests
import xml.etree.ElementTree as ET
# from xml.etree import cElementTree as ElementTree
from io import StringIO
from collections import defaultdict
from xml.etree import cElementTree as ETree
import json


DEBUG_WRITEEV = True
tag_map = {
    "LstmeetingusageHistory": "meetingUsageHistory",
    "LsteventsessionHistory": "eventSessionHistory",
    "LstrecordaccessHistory": "recordAccessHistory",
    "LstsupportsessionHistory": "supportSessionHistory",
    "LsttrainingsessionHistory": "trainingSessionHistory",
    "LstsummaryMeeting": "meeting"
}

sourcetype_map = {
    "LstmeetingusageHistory": "cisco:webex:meetingusagehistory:list",
    "LsteventsessionHistory": "cisco:webex:eventsessionhistory:list",
    "LstrecordaccessHistory": "cisco:webex:recordaccesshistory:list",
    "LstsupportsessionHistory": "cisco:webex:supportsessionhistory:list",
    "LsttrainingsessionHistory": "cisco:webex:trainingsessionhistory:list",
    "LstsummaryMeeting": "cisco:webex:meeting:list"
}

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
    try:
        datetime.datetime.strptime(start_time_start, '%m/%d/%Y %H:%M:%S')
        if start_time_end:
            datetime.datetime.strptime(start_time_end, '%m/%d/%Y %H:%M:%S')
    except ValueError:
        raise ValueError(
            "Incorrect data format, time should be MM/DD/YYYY hh:mm:ss")
    pass


def collect_events(helper, ew):
    """Implement your data collection logic here

    """
    opt_site_nmae = helper.get_arg('site_nmae')
    opt_username = helper.get_arg('username')
    opt_password = helper.get_arg('password')
    opt_start_time_start = helper.get_arg('start_time_start')
    opt_start_time_end = helper.get_arg('start_time_end')
    opt_start_time_end = helper.get_arg('start_time_end')
    opt_endpoints = helper.get_arg('endpoint')

    helper.log_info("[-] WebEx API Endpoint: {}".format(opt_endpoints))
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
    for opt_endpoint in opt_endpoints:
        helper.log_info("[-] \t At {}".format(opt_endpoint))
        if not opt_start_time_end:
            opt_start_time_end = "04/10/2050 10:30:34"

        # create checkpoint key
        #key = helper.get_input_stanza_names() + "_processing"
        key = helper.get_input_stanza_names() + opt_endpoint + "_processing"

        offset = helper.get_check_point(key)
        if offset is None:
            offset = 1
        else:
            offset = int(offset)
        limit = 100
        records = limit
        while(records == limit):
            records = fetch_webex_logs(opt_username, opt_password, opt_site_nmae,
                                       opt_start_time_start, opt_start_time_end, offset, limit, ew, helper, key, password_type, opt_endpoint)
            if records:
                offset = offset + records


def fetch_webex_logs(opt_username, opt_password, opt_site_nmae,
                     opt_start_time_start, opt_start_time_end, offset, limit, ew, helper, key, password_type, opt_endpoint):

    url = "https://{}.webex.com/WBXService/XMLService".format(opt_site_nmae)

    headers = {
        'Content-Type': 'application/xml'
    }

    # Build Payload
    payload = xml_format(opt_username, opt_password, opt_site_nmae,
                         opt_start_time_start, opt_start_time_end, offset, limit, password_type, opt_endpoint, helper)

    # debug_index(payload, ew, helper, opt_endpoint)
    # REMOTE THIS LATER
    helper.log_info("[-] Debug Fetch Request: {} - {}".format(offset, limit))

    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        if response.status_code != 200:
            helper.log_debug(
                "\t[-] WebEx Meetings API Error: {}".format(response.text))

        events = response.text
        # helper.log_info(events)
        ev = parse_xml_to_dict(events)
        helper.log_info(type(ev))
        helper.log_info("ev")
        helper.log_info(ev)
        records = 0

        ev = ev['message']

        response_key = tag_map[opt_endpoint]
        if "header" in ev:
            if "SUCCESS" in ev["header"]["response"]["result"]:
                conferences = ev["body"]["bodyContent"][response_key]

                if isinstance(conferences, list):
                    for event in conferences:
                        # if "sessionKey" in event:
                        dump_it_in_index(event, ew, helper, opt_endpoint)
                else:
                    # if "sessionKey" in conferences:
                    dump_it_in_index(conferences, ew, helper, opt_endpoint)

                # Record Meta Data
                matchingRecords = ev["body"]["bodyContent"]['matchingRecords']
                if "returned" in matchingRecords:
                    records = int(matchingRecords['returned'])
                    if records < limit:
                        # Last Page - Save Offset
                        helper.save_check_point(key, offset + records)
                    return records
                else:
                    helper.log_info(
                        "[-] WebEx Empty records: {}".format(repr(records)))
            elif "no record found" in ev["header"]["response"]["reason"]:
                return 0
            else:
                helper.log_info(
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
    '''
    event["SessionID"] = event["confID"]
    event["Attended"] = event["totalParticipants"]
    event["SessionNo"] = event["sessionKey"]
    event["MeetingType"] = event["meetingType"]
    event["Duration"] = event["duration"]
    event["Topic"] = event["confName"]
    event["Date"] = event["meetingStartTime"][:10]
    '''

    if isinstance(event, dict):
        event = json.dumps(event)
    try:
        ev = helper.new_event(event, time=None, host=None,
                              index=None, source=None, sourcetype=sourcetype_map[opt_endpoint], done=True, unbroken=True)
        ew.write_event(ev)
    except Exception as e:
        helper.log_debug("[-] WebEx Meetings Event Exception {}".format(e))

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
    # ev = XmlDictConfig(root)

    # e = ETree.XML(root)
    # ev = etree_to_dict(e)
    ev = etree_to_dict(root)
    return ev


def xml_format(username, password, site_name, start_time_start, start_time_end, offset, limit, password_type, endpoint, helper):

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
                <orderBy>CONFNAME</orderBy>
                <orderAD>ASC</orderAD>
            </order >
        '''
    # Endpooint specific Payload
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
    elif endpoint == "LstsummaryMeeting":
        endpoint = "java:com.webex.service.binding.meeting.{}".format(
            endpoint)
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
                    <listMethod>OR</listMethod>
                </listControl>
                {order}
            </bodyContent>
        </body>
    </serv:message>""".format(auth=auth, endpoint=endpoint, startTimeScope=startTimeScope, offset=offset, limit=limit, order=order)
    return payload
