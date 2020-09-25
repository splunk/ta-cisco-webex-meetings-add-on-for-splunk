import os
import sys
import time
import datetime
import requests
from collections import defaultdict
import json
from datetime import date, timedelta
from datetime import datetime
try:
    from defusedxml1 import ElementTree as ET
except:
    # Splunk <=7.2.9 does not ship with defusedxml
    from dep.defusedxml import ElementTree as ET
from io import StringIO


from utils.webex_constant import tag_map, sourcetype_map, timestamp_map, start_time_map
from utils.xml_payload_format import xml_format
from utils.access_token_functions import update_access_token_with_validation


def fetch_webex_logs(ew, helper, params):

    mode = params['mode']
    if mode is "historical":
        helper.log_debug("== Historcial Data log ==")
    elif mode is "live":
        helper.log_debug("== Live Data log ==")

    records = 0
    url = "https://{}.webex.com/WBXService/XMLService".format(
        params['opt_site_name'])

    headers = {
        'Content-Type': 'application/xml',
        'Connection': 'close'
    }

    # Build Payload
    payload = xml_format(params)

    helper.log_debug(
        "[-] Endpoint: {}, Debug Fetch Request: {} - {}".format(params['opt_endpoint'], params['offset'], params['limit']))

    try:
        response = requests.request(
            "POST", url, headers=headers, data=payload, proxies=params['proxies'])
        helper.log_debug(
            "[-] Endpoint: {}, response.status_code: {}".format(params['opt_endpoint'], response.status_code))
        if response.status_code != 200:
            helper.log_debug(
                "\t[-] Endpoint: {}, WebEx Meetings API Error: {}".format(params['opt_endpoint'], response.text))

        ev = parse_xml_to_dict(response.text)
        ev = ev['message']
        response_key = tag_map[params['opt_endpoint']]

        if "header" in ev:
            if "SUCCESS" in ev["header"]["response"]["result"]:
                conferences = ev["body"]["bodyContent"][response_key]
                helper.log_debug("[-] Endpoint: {}, Start to dump data".format(params['opt_endpoint']))
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
                        "[-] Endpoint: {}, Returned Records: {}".format(params['opt_endpoint'], repr(records)))
                    return records
                else:
                    helper.log_debug(
                        "[-] Endpoint: {}, WebEx Empty records: {}".format(params['opt_endpoint'], repr(records)))
            elif "no record found" in ev["header"]["response"]["reason"]:
                helper.log_debug("[-] Endpoint: {}, WebEx Empty records: 0".format(params['opt_endpoint']))
                helper.log_debug(
                    "[-] Endpoint: {}, WebEx Response: {}".format(params['opt_endpoint'], repr(ev["header"]["response"]["reason"])))
                return 0
            # Check if the access token is invalid
            elif "WebEx access token is invalid" in ev["header"]["response"]["reason"]:
                helper.log_debug(
                    "[-] Endpoint: {}, WebEx Response: {}".format(params['opt_endpoint'], repr(ev["header"]["response"]["reason"])))
                if params['password_type'] != "password":
                    helper.log_info("[-] Endpoint: {}, WebEx access token is either expired or invalid, trying to update it using refresh token".format(params['opt_endpoint']))
                    update_access_token_with_validation(helper, params)
                    time.sleep(10)
                    fetch_webex_logs(ew, helper, params)
            else:
                helper.log_debug(
                    "[-] Endpoint: {}, WebEx Response: {}".format(params['opt_endpoint'], repr(ev["header"]["response"]["reason"])))
        else:
            helper.log_info("Endpoint: {}, Condition not match for : {}".format(params['opt_endpoint'], repr(ev)))

    except Exception as e:
        helper.log_info(
            "[-] Endpoint: {}, WebEx Request Failed (Check URL and Given Error): {}".format(params['opt_endpoint'], repr(e)))
        helper.log_debug("[-] Endpoint: {}, WebEx Request failed with error, Ingestion Interval: {}-{}, failed time (Local time zone): {}".format(params['opt_endpoint'], params['start_time'], params['end_time'], datetime.now().strftime('%m/%d/%Y %H:%M:%S.%f')))

        raise e


def dump_in_index(event, ew, helper, opt_endpoint, timestamp_key, params):
    if isinstance(event, dict):
        # get the end time of this event
        this_event_time = event[timestamp_map[opt_endpoint]]

        # get start time of this event and convert it to epoch time
        this_event_start_time = event[start_time_map[opt_endpoint]]
        this_event_start_time = datetime.strptime(
            this_event_start_time, '%m/%d/%Y %H:%M:%S')

        this_event_start_time = (
            this_event_start_time - datetime(1970, 1, 1)).total_seconds()

    try:
        this_event_time = datetime.strptime(
            this_event_time, '%m/%d/%Y %H:%M:%S')

        # Prevent Duplicates in Session Mode
        if params['mode'] == "live":
            start_time = datetime.strptime(
                params['start_time'], '%m/%d/%Y %H:%M:%S')

            # actualStartTime is this_event_time
            if this_event_time < start_time:
                # helper.log_debug("\t\t\t [--] RETURN - Duplicate")
                return

        ev = helper.new_event(json.dumps(event), time="%.3f" % int(this_event_start_time), host=None,
                              index=None, source=None, sourcetype=sourcetype_map[opt_endpoint], done=True, unbroken=True)
        ew.write_event(ev)

        # update the checkpoint for timestamp
        timestamp = helper.get_check_point(timestamp_key)
        timestamp = datetime.strptime(timestamp, '%m/%d/%Y %H:%M:%S')
        timestamp = max(timestamp, this_event_time).strftime(
            '%m/%d/%Y %H:%M:%S')
        helper.save_check_point(timestamp_key, timestamp)

    except Exception as e:
        helper.log_info("[-] Endpoint: {}, WebEx Meetings Event Exception {}".format(params['opt_endpoint'], e))


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


def get_slice_time(start_time, end_time, steps, helper):
    """
    @param start: string, UTC start time
    @param end: string, UTC end time
    @param steps: int
    @return time_list: list of time string tuple
    """
    time_list = []
    # convert UTC time string to UTC epoch
    start = int((datetime.strptime(start_time, '%m/%d/%Y %H:%M:%S') - datetime(1970, 1, 1)).total_seconds())
    end = int((datetime.strptime(end_time, '%m/%d/%Y %H:%M:%S') - datetime(1970, 1, 1)).total_seconds())
    chunks = range(start, end, steps)
    counter = 0
    for chunk in chunks:
        counter += 1
        if len(chunks) is counter:
            # convert UTC epoch to UTC time string
            cur_start_time = datetime.utcfromtimestamp(
            int(chunk)).strftime('%m/%d/%Y %H:%M:%S')
            cur_end_time = datetime.utcfromtimestamp(
            int(end)).strftime('%m/%d/%Y %H:%M:%S')
            time_list.append((cur_start_time, cur_end_time))
        else:
            # convert UTC epoch to UTC time string
            cur_start_time = datetime.utcfromtimestamp(
            int(chunk)).strftime('%m/%d/%Y %H:%M:%S')
            cur_end_time = datetime.utcfromtimestamp(
            int(chunk+steps-1)).strftime('%m/%d/%Y %H:%M:%S')
            time_list.append((cur_start_time, cur_end_time))
    return time_list


