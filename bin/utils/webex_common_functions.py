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

        # get start time of this event and convert it to epoch time
        this_event_start_time = event[start_time_map[opt_endpoint]]
        helper.log_debug(
            "\t Event start time: {}".format(this_event_start_time))
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
            helper.log_debug(
                "\t\t\t [--] {} < {}".format(this_event_time, start_time))

            if this_event_time < start_time:
                helper.log_debug("\t\t\t [--] RETURN - Duplicate")
                return

        ev = helper.new_event(json.dumps(event), time="%.3f" % int(this_event_start_time), host=None,
                              index=None, source=None, sourcetype=sourcetype_map[opt_endpoint], done=True, unbroken=True)
        ew.write_event(ev)

        # update the checkpoint for timestamp
        timestamp = helper.get_check_point(timestamp_key)
        timestamp = datetime.strptime(timestamp, '%m/%d/%Y %H:%M:%S')
        timestamp = max(timestamp, this_event_time).strftime(
            '%m/%d/%Y %H:%M:%S')
        helper.log_debug("\t\t[-]time: timestamp: {}".format(timestamp))
        helper.save_check_point(timestamp_key, timestamp)

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


def is_access_token_valid(helper, params):
    params['offset'] = 1
    url = "https://{}.webex.com/WBXService/XMLService".format(
        params['opt_site_name'])

    headers = {
        'Content-Type': 'application/xml'
    }

    # Build Payload
    payload = xml_format(params)

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
        # response_key = tag_map[params['opt_endpoint']]
        helper.log_debug("===ev=== : {}".format(ev))

        if "header" in ev:
            if "SUCCESS" in ev["header"]["response"]["result"]:
                return True
            elif "WebEx access token is invalid" in ev["header"]["response"]["reason"]:
                return False
        #         conferences = ev["body"]["bodyContent"][response_key]
        #         helper.log_debug("Start to dump data")
        #         if isinstance(conferences, list):
        #             for event in conferences:
        #                 if mode is "live" and "actualStartTime" in event:
        #                     dump_in_index(event, ew, helper,
        #                                   params['opt_endpoint'], params['timestamp_key'], params)
        #                 elif mode is "historical":
        #                     # Historical
        #                     dump_in_index(event, ew, helper,
        #                                   params['opt_endpoint'], params['timestamp_key'], params)
        #         else:
        #             if mode is "live" and "actualStartTime" in conferences:
        #                 dump_in_index(conferences, ew, helper,
        #                               params['opt_endpoint'], params['timestamp_key'], params)

        #             elif mode is "historical":
        #                 # Historical
        #                 dump_in_index(conferences, ew, helper,
        #                               params['opt_endpoint'], params['timestamp_key'], params)

        #         # Record Meta Data
        #         matchingRecords = ev["body"]["bodyContent"]['matchingRecords']
        #         if "returned" in matchingRecords:
        #             records = int(matchingRecords['returned'])
        #             helper.log_debug(
        #                 "[-] Returned Records: {}".format(repr(records)))
        #             return records
        #         else:
        #             helper.log_debug(
        #                 "[-] WebEx Empty records: {}".format(repr(records)))
        #     elif "no record found" in ev["header"]["response"]["reason"]:
        #         helper.log_debug("[-] WebEx Empty records: 0")
        #         helper.log_debug(
        #             "[-] WebEx Response: {}".format(repr(ev["header"]["response"]["reason"])))
        #         return 0
        #     else:
        #         helper.log_debug(
        #             "[-] WebEx Response: {}".format(repr(ev["header"]["response"]["reason"])))
        # else:
        #     helper.log_info("Condition not match for : {}".format(repr(ev)))

    except Exception as e:
        helper.log_info(
            "[-] WebEx Request Failed (Check URL and Given Error): {}".format(repr(e)))
        raise e
