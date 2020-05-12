
# encoding = utf-8

import os
import sys
import time
import datetime
import requests
# import xml.etree.ElementTree as ET
try:
    from defusedxml1 import ElementTree as ET
except:
    # Splunk <=7.2.9 does not ship with defusedxml
    from dep.defusedxml import ElementTree as ET

from io import StringIO
from collections import defaultdict
from xml.etree import cElementTree as ETree
import json
from datetime import date, timedelta
from datetime import datetime

from xml_payload_format import xml_format
from webex_constant import tag_map, sourcetype_map, timestamp_map, start_time_map, authentication_type


def validate_input(helper, definition):
    """Implement your own validation logic to validate the input stanza configurations"""
    # This example accesses the modular input variable
    # site_name = definition.parameters.get('site_name', None)
    # username = definition.parameters.get('username', None)
    # password = definition.parameters.get('password', None)
    # start_time_start = definition.parameters.get('start_time_start', None)

    start_time_start = definition.parameters.get('start_time_start', None)
    interval = definition.parameters.get('interval', None)

    if int(interval) < 86400:
        raise ValueError(
            "Interval should be 86400 or more for historical data, not {}.".format(interval))

    try:
        # validate start_time_start format:
        if start_time_start:
            datetime.strptime(
                start_time_start, '%m/%d/%Y %H:%M:%S')
    except ValueError:
        raise ValueError(
            "Incorrect data format, time should be MM/DD/YYYY hh:mm:ss")

    enddt = datetime.utcnow().date() - timedelta(3)
    end_time = datetime.combine(enddt, datetime.max.time())
    start_time_start = datetime.strptime(start_time_start, '%m/%d/%Y %H:%M:%S')
    if start_time_start >= end_time:
        raise ValueError(
            "Begin Date must be at least 3 days ago. Please enter a time before {}.".format(end_time.strftime('%m/%d/%Y %H:%M:%S')))
    pass


def collect_events(helper, ew):
    """Implement your data collection logic here

    #   Feature: partner ID
        <partnerID>{partnertID}<partnerID>
        <siteID>{siteID}<siteID>

    """

    opt_start_time_start = helper.get_arg('start_time_start')
    opt_endpoints = helper.get_arg('endpoints')
    opt_interval = int(helper.get_arg('interval'))
    opt_live = False

    proxy = helper.get_proxy()
    if proxy:
        proxy_auth = "{}:{}".format(
            proxy['proxy_username'], proxy['proxy_password'])
        proxies = {
            "https": "{protocol}://{auth}@{host}:{port}/".format(protocol=proxy['proxy_type'], auth=proxy, host=proxy['proxy_url'], port=proxy['proxy_port']),
            "http": "{protocol}://{auth}@{host}:{port}/".format(protocol=proxy['proxy_type'], auth=proxy, host=proxy['proxy_url'], port=proxy['proxy_port'])
        }
    else:
        proxies = None

    params = {"opt_username": helper.get_global_setting("username"),
              "opt_password": helper.get_global_setting("password"),
              "opt_site_name": helper.get_global_setting("site_name"),
              "limit": 500,
              "timezone": "20",
              "password_type": authentication_type["Password Authentication"],
              "proxies": proxies}

    # Historical Data
    helper.log_debug("Historical Data")
    for opt_endpoint in opt_endpoints:
        helper.log_debug("[-] \t At {}".format(opt_endpoint))

        # endtime is midnight of GMT - 3days
        # end_time = datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S')
        enddt = datetime.utcnow().date() - timedelta(3)
        end_time = datetime.combine(
            enddt, datetime.max.time()).strftime('%m/%d/%Y %H:%M:%S')

        # create checkpoint key for offest and timestamp
        timestamp_key = "timestamp_{}_{}_processing".format(
            helper.get_input_stanza_names(), opt_endpoint)

        start_time = helper.get_check_point(timestamp_key)
        if start_time is None:
            start_time = opt_start_time_start
            helper.save_check_point(timestamp_key, start_time)
        else:
            # shift the starttime by 1 second
            start_time = datetime.strptime(
                start_time, '%m/%d/%Y %H:%M:%S').strftime('%s')
            # start_time = (start_time - datetime(1970, 1, 1)
            #              ).total_seconds()
            start_time = int(start_time) + 1
            start_time = datetime.fromtimestamp(
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

    helper.log_debug(
        "[-] Debug Fetch Request: {} - {}".format(params['offset'], params['limit']))

    try:
        response = requests.request(
            "POST", url, headers=headers, data=payload, proxies=params['proxies'])
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
        # get the end time of this event
        helper.log_info("Event Returned: {}".format(event))
        this_event_time = event[timestamp_map[opt_endpoint]]

        # get start time of this event
        this_event_start_time = event[start_time_map[opt_endpoint]]
        helper.log_debug(
            "\t Event start time: {}".format(this_event_start_time))
        this_event_start_time = datetime.strptime(
            this_event_start_time, '%m/%d/%Y %H:%M:%S')

        this_event_start_time = (
            this_event_start_time - datetime(1970, 1, 1)).total_seconds()

    try:
        this_event_time = datetime.strptime(
            this_event_time, '%m/%d/%Y %H:%M:%S').strftime('%s')
        # this_event_time = (
        #    this_event_time - datetime(1970, 1, 1)).total_seconds()

        # Prevent Duplicates in Session Mode
        if params['mode'] == "live":
            start_time = datetime.strptime(
                params['start_time'], '%m/%d/%Y %H:%M:%S').strftime('%s')
            # start_time = (
            #    start_time - datetime(1970, 1, 1)).total_seconds()
            # actualStartTime is this_event_time
            helper.log_debug(
                "\t\t\t [--] {} < {}".format(this_event_time, start_time))
            if int(this_event_time) < int(start_time):
                helper.log_debug("\t\t\t [--] RETURN - Duplicate")
                return

        ev = helper.new_event(json.dumps(event), time="%.3f" % int(this_event_start_time), host=None,
                              index=None, source=None, sourcetype=sourcetype_map[opt_endpoint], done=True, unbroken=True)
        ew.write_event(ev)

        # update the checkpoint for timestamp
        timestamp = helper.get_check_point(timestamp_key)
        timestamp = datetime.strptime(
            timestamp, '%m/%d/%Y %H:%M:%S').strftime('%s')
        # timestamp = (timestamp - datetime(1970, 1, 1)).total_seconds()
        timestamp = max(int(timestamp), int(this_event_time))
        helper.log_debug("\t\t[-]time: timestamp: {}".format(timestamp))
        helper.save_check_point(timestamp_key, datetime.fromtimestamp(
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
