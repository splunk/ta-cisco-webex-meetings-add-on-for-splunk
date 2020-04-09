
# encoding = utf-8

import os
import sys
import time
import datetime
import requests
import xml.etree.ElementTree as ET
#from xml.etree import cElementTree as ElementTree
from io import StringIO
from collections import defaultdict
from xml.etree import cElementTree as ETree
import json


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

    # The following examples get the arguments of this input.
    # Note, for single instance mod input, args will be returned as a dict.
    # For multi instance mod input, args will be returned as a single value.
    opt_site_nmae = helper.get_arg('site_nmae')
    opt_username = helper.get_arg('username')
    opt_password = helper.get_arg('password')
    opt_start_time_start = helper.get_arg('start_time_start')
    opt_start_time_end = helper.get_arg('start_time_end')
    # In single instance mode, to get arguments of a particular input, use
    opt_site_nmae = helper.get_arg('site_nmae', stanza_name)
    opt_username = helper.get_arg('username', stanza_name)
    opt_password = helper.get_arg('password', stanza_name)
    opt_start_time_start = helper.get_arg('start_time_start', stanza_name)
    opt_start_time_end = helper.get_arg('start_time_end', stanza_name)

    # get input type
    helper.get_input_type()

    # The following examples get input stanzas.
    # get all detailed input stanzas
    helper.get_input_stanza()
    # get specific input stanza with stanza name
    helper.get_input_stanza(stanza_name)
    # get all stanza names
    helper.get_input_stanza_names()

    # The following examples get options from setup page configuration.
    # get the loglevel from the setup page
    loglevel = helper.get_log_level()
    # get proxy setting configuration
    proxy_settings = helper.get_proxy()
    # get account credentials as dictionary
    account = helper.get_user_credential_by_username("username")
    account = helper.get_user_credential_by_id("account id")
    # get global variable configuration
    global_userdefined_global_var = helper.get_global_setting(
        "userdefined_global_var")

    # The following examples show usage of logging related helper functions.
    # write to the log for this modular input using configured global log level or INFO as default
    helper.log("log message")
    # write to the log using specified log level
    helper.log_debug("log message")
    helper.log_info("log message")
    helper.log_warning("log message")
    helper.log_error("log message")
    helper.log_critical("log message")
    # set the log level for this modular input
    # (log_level can be "debug", "info", "warning", "error" or "critical", case insensitive)
    helper.set_log_level(log_level)

    # The following examples send rest requests to some endpoint.
    response = helper.send_http_request(url, method, parameters=None, payload=None,
                                        headers=None, cookies=None, verify=True, cert=None,
                                        timeout=None, use_proxy=True)
    # get the response headers
    r_headers = response.headers
    # get the response body as text
    r_text = response.text
    # get response body as json. If the body text is not a json string, raise a ValueError
    r_json = response.json()
    # get response cookies
    r_cookies = response.cookies
    # get redirect history
    historical_responses = response.history
    # get response status code
    r_status = response.status_code
    # check the response status, if the status is not sucessful, raise requests.HTTPError
    response.raise_for_status()

    # The following examples show usage of check pointing related helper functions.
    # save checkpoint
    helper.save_check_point(key, state)
    # delete checkpoint
    helper.delete_check_point(key)
    # get checkpoint
    state = helper.get_check_point(key)

    # To create a splunk event
    helper.new_event(data, time=None, host=None, index=None,
                     source=None, sourcetype=None, done=True, unbroken=True)
    """

    '''
    # The following example writes a random number as an event. (Multi Instance Mode)
    # Use this code template by default.
    import random
    data = str(random.randint(0,100))
    event = helper.new_event(source=helper.get_input_type(
    ), index=helper.get_output_index(), sourcetype=helper.get_sourcetype(), data=data)
    ew.write_event(event)
    '''

    '''
    # The following example writes a random number as an event for each input config. (Single Instance Mode)
    # For advanced users, if you want to create single instance mod input, please use this code template.
    # Also, you need to uncomment use_single_instance_mode() above.
    import random
    input_type = helper.get_input_type()
    for stanza_name in helper.get_input_stanza_names():
        data = str(random.randint(0,100))
        event = helper.new_event(source=input_type, index=helper.get_output_index(
            stanza_name), sourcetype=helper.get_sourcetype(stanza_name), data=data)
        ew.write_event(event)
    '''
    opt_site_nmae = helper.get_arg('site_nmae')
    opt_username = helper.get_arg('username')
    opt_password = helper.get_arg('password')
    opt_start_time_start = helper.get_arg('start_time_start')
    opt_start_time_end = helper.get_arg('start_time_end')

    if not opt_start_time_end:
        opt_start_time_end = "04/10/2050 10:30:34"

    offset = 1

    # create checkpoint key
    key = helper.get_input_stanza_names() + "_processing"

    offset = helper.get_check_point(key)
    if offset is None:
        offset = 1
    else:
        offset = int(offset)
    limit = 100
    records = limit
    while(records == limit):
        records = fetch_webex_logs(opt_username, opt_password, opt_site_nmae,
                                   opt_start_time_start, opt_start_time_end, offset, limit, ew, helper, key)
        if records:
            offset = offset + records


def fetch_webex_logs(opt_username, opt_password, opt_site_nmae,
                     opt_start_time_start, opt_start_time_end, offset, limit, ew, helper, key):

    url = "https://{}.webex.com/WBXService/XMLService".format(opt_site_nmae)

    headers = {
        'Content-Type': 'application/xml'
    }

    # Build Payload
    payload = xml_format(opt_username, opt_password, opt_site_nmae,
                         opt_start_time_start, opt_start_time_end, offset, limit)

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

        if "header" in ev:
            if "SUCCESS" in ev["header"]["response"]["result"]:
                conferences = ev["body"]["bodyContent"]["meetingUsageHistory"]

                if isinstance(conferences, list):
                    for event in conferences:
                        if "sessionKey" in event:
                            dump_it_in_index(event, ew, helper)
                else:
                    if "sessionKey" in conferences:
                        dump_it_in_index(conferences, ew, helper)

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


def dump_it_in_index(event, ew, helper):
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
                              index=None, source=None, sourcetype=helper.get_sourcetype(), done=True, unbroken=True)
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


def xml_format(username, password, site_name, start_time_start, start_time_end, offset, limit):
    payload = """<?xml version="1.0" encoding="UTF-8"?>
    <serv:message xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <header>
            <securityContext>
                <webExID>{0}</webExID>
                <password>{1}</password>
                <siteName>{2}</siteName>
            </securityContext>
        </header>
        <body>
            <bodyContent xsi:type=
                "java:com.webex.service.binding.history.LstmeetingusageHistory">
                <startTimeScope>
                    <sessionStartTimeStart>{3}</sessionStartTimeStart>
                    <sessionStartTimeEnd>{4}</sessionStartTimeEnd>
                </startTimeScope>
                <listControl>
                    <serv:startFrom>{5}</serv:startFrom>
                    <serv:maximumNum>{6}</serv:maximumNum>
                    <serv:listMethod>OR</serv:listMethod>
                </listControl>
                <order>
                    <orderBy>CONFNAME</orderBy>
                    <orderAD>ASC</orderAD>
                </order>
            </bodyContent>
        </body>
    </serv:message>""".format(username, password, site_name, start_time_start, start_time_end, offset, limit)
    return payload
