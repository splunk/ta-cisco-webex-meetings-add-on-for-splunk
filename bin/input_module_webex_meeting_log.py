
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

#from MaxStack_list import MaxStack_list
from xml_payload_format import xml_format

tag_map = {
    "LstmeetingattendeeHistory": "meetingAttendeeHistory",
    "LstmeetingusageHistory": "meetingUsageHistory",
    "LsteventsessionHistory": "eventSessionHistory",
    "LstrecordaccessHistory": "recordAccessHistory",
    "LstsupportsessionHistory": "supportSessionHistory",
    "LsttrainingsessionHistory": "trainingSessionHistory",
    "LstsummarySession": "session"
}

sourcetype_map = {
    "LstmeetingattendeeHistory": "cisco:webex:meetingattendeehistory:list",
    "LstmeetingusageHistory": "cisco:webex:meetingusagehistory:list",
    "LsteventsessionHistory": "cisco:webex:eventsessionhistory:list",
    "LstrecordaccessHistory": "cisco:webex:recordaccesshistory:list",
    "LstsupportsessionHistory": "cisco:webex:supportsessionhistory:list",
    "LsttrainingsessionHistory": "cisco:webex:trainingsessionhistory:list",
    "LstsummarySession": "cisco:webex:session:list"
}

# use this for timestamp checkpoint
# remove it if offset work
timestamp_map = {
    "LstmeetingattendeeHistory": "joinTime",
    "LstmeetingusageHistory": "meetingStartTime",
    "LsteventsessionHistory": "sessionStartTime",
    "LstrecordaccessHistory": "creationTime",
    "LstsupportsessionHistory": "sessionStartTime",
    "LsttrainingsessionHistory": "sessionStartTime",
    "LstsummarySession": "actualStartTime"
}
#maxStack = MaxStack_list()


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
    # site_name = definition.parameters.get('site_name', None)
    # username = definition.parameters.get('username', None)
    # password = definition.parameters.get('password', None)
    # start_time_start = definition.parameters.get('start_time_start', None)
    # start_time_end = definition.parameters.get('start_time_end', None)
    start_time_start = definition.parameters.get('start_time_start', None)
    start_time_end = definition.parameters.get('start_time_end', None)
    live = definition.parameters.get('live', None)

    if live == "1" and start_time_start:
        raise ValueError(
            "Start time is not required for Continuous Monitoring.")

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

    #   Feature: partner ID
        <partnerID>{partnertID}<partnerID>
        <siteID>{siteID}<siteID>

    """

    opt_start_time_start = helper.get_arg('start_time_start')
    opt_endpoints = helper.get_arg('endpoint')
    opt_interval = int(helper.get_arg('interval'))
    opt_live = helper.get_arg('live')

    params = {"opt_username": helper.get_arg('username'),
              "opt_password": helper.get_arg('password'),
              "opt_site_name": helper.get_arg('site_name'),
              "limit": 1000,
              "timezone": "20",
              "password_type": helper.get_arg('password_type')}

    if opt_live is True:
        # do the time magic
        # run the unique endpoint
        # End time : time.now -> convert to epoch
        # Start time : end time - 600
        # Then query the live session endpoint with these parameters, along with timezone (if applicable)
        # opt_interval = 600

        params.update({"opt_endpoint": "LstsummarySession"})

        timestamp_key = "timestamp_{}_{}_processing".format(
            helper.get_input_stanza_names(), params['opt_endpoint'])

        # Get previously ingested confID
        """
        params['confID_key'] = "confID_{}_{}_processing".format(
            helper.get_input_stanza_names(), params['opt_endpoint'])
        confID_keys = helper.get_check_point(params['confID_key'])
        if confID_keys:
            params['confID_keys'] = json.loads(confID_keys)
        else:
            params['confID_keys'] = json.loads('[]')
        """

        start_time = helper.get_check_point(timestamp_key)
        helper.log_debug("timestamp_value: {}".format(start_time))
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
            helper.save_check_point(timestamp_key, start_time)

        helper.log_debug("type of start time: {}".format(type(start_time)))
        helper.log_debug("---start time---: {}".format(start_time))

        end_time = datetime.datetime.fromtimestamp(
            int(end_time_epoch)).strftime('%m/%d/%Y %H:%M:%S')
        helper.log_debug("start time: {}".format(start_time))
        helper.log_debug("end time: {}".format(end_time))

        #  Update Parameters
        params.update({"mode": "live"})
        params.update({"start_time": start_time})
        params.update({"end_time": end_time})
        params.update({"timestamp_key": timestamp_key})
        params.update({"end_time_epoch": end_time_epoch})

        records = params['limit']
        offset = 1
        while (records == params['limit']):
            helper.log_debug("current_offset: {}".format(offset))
            params['offset'] = offset
            records = fetch_webex_logs(ew, helper, params)

            if records:
                offset += records

    # Historical Data (offset works)
    if opt_live is not True:
        helper.log_debug("Historical Data")
        for opt_endpoint in opt_endpoints:
            helper.log_debug("[-] \t At {}".format(opt_endpoint))

            end_time = datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S')

            # create checkpoint key for offest and timestamp
            timestamp_key = "timestamp_{}_{}_processing".format(
                helper.get_input_stanza_names(), opt_endpoint)

            start_time = helper.get_check_point(timestamp_key)
            if start_time is None:
                start_time = opt_start_time_start
                helper.save_check_point(timestamp_key, start_time)
            else:
                # shift the starttime by 1 second
                start_time = datetime.datetime.strptime(
                    start_time, '%m/%d/%Y %H:%M:%S').strftime("%s")
                start_time = int(start_time) + 1
                start_time = datetime.datetime.fromtimestamp(
                    int(start_time)).strftime('%m/%d/%Y %H:%M:%S')

            # maxStack.empty()

            helper.log_debug("Start time: {}".format(start_time))
            helper.log_debug("End time: {}".format(end_time))

            #  Update Parameters
            params.update({"mode": "historical"})
            params.update({"opt_endpoint": opt_endpoint})
            params.update({"start_time": start_time})
            params.update({"end_time": end_time})
            params.update({"timestamp_key": timestamp_key})

            records = params['limit']
            offset = 1
            while (records == params['limit']):
                helper.log_debug("current_offset: {}".format(offset))
                params['offset'] = offset
                records = fetch_webex_logs(ew, helper, params)
                helper.log_debug("\t Offet:{}\tLimit: {}\tRecords Returned: {}".format(
                    offset, params['limit'], records))
                if records:
                    offset += records


def fetch_webex_logs(ew, helper, params):

    mode = params['mode']
    if mode is "historical":
        helper.log_debug("== Historcial Data log ==")
    elif mode is "live":
        helper.log_debug("== Live Data log ==")
        end_time_epoch = params['end_time_epoch']

    records = 0
    url = "https://{}.webex.com/WBXService/XMLService".format(
        params['opt_site_name'])

    headers = {
        'Content-Type': 'application/xml'
    }

    # Build Payload
    payload = xml_format(params)
    helper.log_debug("payload start time: {}".format(params['start_time']))

    helper.log_debug(
        "[-] Debug Fetch Request: {} - {}".format(params['offset'], params['limit']))

    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        helper.log_debug(
            "[-] : response.status_code: {}".format(response.status_code))
        if response.status_code != 200:
            helper.log_debug(
                "\t[-] WebEx Meetings API Error: {}".format(response.text))

        ev = parse_xml_to_dict(response.text)
        ev = ev['message']
        response_key = tag_map[params['opt_endpoint']]
        helper.log_debug(ev)

        if "header" in ev:
            if "SUCCESS" in ev["header"]["response"]["result"]:
                conferences = ev["body"]["bodyContent"][response_key]
                helper.log_debug("Start to dump data")
                if isinstance(conferences, list):
                    for event in conferences:
                        if mode is "live" and "actualStartTime" in event:
                            dump_in_index(event, ew, helper,
                                          params['opt_endpoint'], params['timestamp_key'], params)
                        elif mode is "historical":
                            # Historical
                            dump_in_index(event, ew, helper,
                                          params['opt_endpoint'], params['timestamp_key'], params)
                else:
                    if mode is "live" and "actualStartTime" in conferences:
                        dump_in_index(conferences, ew, helper,
                                      params['opt_endpoint'], params['timestamp_key'], params)

                    elif mode is "historical":
                        # Historical
                        dump_in_index(conferences, ew, helper,
                                      params['opt_endpoint'], params['timestamp_key'], params)

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


def dump_in_index(event, ew, helper, opt_endpoint, timestamp_key, params):
    if isinstance(event, dict):
        time_tag = timestamp_map[opt_endpoint]
        helper.log_info("Event Returned: {}".format(event))
        this_event_time = event[time_tag]

    try:
        this_event_time = datetime.datetime.strptime(
            this_event_time, '%m/%d/%Y %H:%M:%S').strftime("%s")

        # Prevent Duplicates in Session Mode
        if params['mode'] == "live":
            start_time = datetime.datetime.strptime(
                params['start_time'], '%m/%d/%Y %H:%M:%S').strftime("%s")
            # actualStartTime is this_event_time
            helper.log_debug(
                "\t\t\t [--] {} < {}".format(this_event_time, start_time))
            if this_event_time < start_time:
                helper.log_debug("\t\t\t [--] RETURN - Duplicate")
                return

        ev = helper.new_event(json.dumps(event), time=this_event_time, host=None,
                              index=None, source=None, sourcetype=sourcetype_map[opt_endpoint], done=True, unbroken=True)
        ew.write_event(ev)

        # update the checkpoint for timestamp
        timestamp = helper.get_check_point(timestamp_key)
        timestamp = datetime.datetime.strptime(
            timestamp, '%m/%d/%Y %H:%M:%S').strftime("%s")
        timestamp = max(int(timestamp), int(this_event_time))
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
