
# encoding = utf-8

import os
import sys
import time
import datetime
import requests

from datetime import date, timedelta
from datetime import datetime

from utils.webex_constant import authentication_type
from utils.webex_common_functions import fetch_webex_logs
from utils.access_token_functions import update_access_token_with_validation


def validate_input(helper, definition):
    """Implement your own validation logic to validate the input stanza configurations"""

    live = definition.parameters.get('live', 1)
    interval = definition.parameters.get('interval', None)

    if int(interval) > 60:
        raise ValueError(
            "Interval should be 60 or less for general service session data, not {}.".format(interval))

    pass


def collect_events(helper, ew):
    """Implement your data collection logic here"""

    opt_endpoints = helper.get_arg('endpoint')
    opt_interval = int(helper.get_arg('interval'))
    opt_live = helper.get_arg('live')

    proxy = helper.get_proxy()
    if proxy:
        if proxy['proxy_username'] and proxy['proxy_password']:
            proxy_auth = "{}:{}".format(
                proxy['proxy_username'], proxy['proxy_password'])
            proxies = {
                "https": "{protocol}://{auth}@{host}:{port}/".format(protocol=proxy['proxy_type'], auth=proxy_auth, host=proxy['proxy_url'], port=proxy['proxy_port']),
                "http": "{protocol}://{auth}@{host}:{port}/".format(protocol=proxy['proxy_type'], auth=proxy_auth, host=proxy['proxy_url'], port=proxy['proxy_port'])
            }
        else:
            proxies = {
                "https": "{protocol}://{host}:{port}/".format(protocol=proxy['proxy_type'], host=proxy['proxy_url'], port=proxy['proxy_port']),
                "http": "{protocol}://{host}:{port}/".format(protocol=proxy['proxy_type'], host=proxy['proxy_url'], port=proxy['proxy_port'])
            }
    else:
        proxies = None

    params = {"opt_username": helper.get_global_setting("username"),
              "opt_password": helper.get_global_setting("password"),
              "opt_site_name": helper.get_global_setting("site_name"),
              "limit": 500,
              "timezone": "20",
              #   "password_type": authentication_type["Password Authentication"],
              "password_type": helper.get_global_setting("password_type"),
              "proxies": proxies}

    params.update({"opt_endpoint": "LstsummarySession"})

    # Handle OAuth Situation
    # if password_type is NOT password is override password by access token
    helper.log_debug("[-] Endpoint: {}, password_type: {}".format(params['opt_endpoint'], params['password_type']))
    if params['password_type'] != "password":
        params['opt_client_id'] = helper.get_global_setting("client_id")
        params['opt_client_secret'] = helper.get_global_setting(
            "client_secret")
        params['opt_refresh_token'] = helper.get_global_setting(
            "refresh_token")
        params['redirect_uri'] = helper.get_global_setting(
            "redirect_uri")      

        update_access_token_with_validation(helper, params)

    timestamp_key = "timestamp_{}_{}_processing".format(
        helper.get_input_stanza_names(), params['opt_endpoint'])

    # get the start_time form checkpoint
    start_time = helper.get_check_point(timestamp_key)
    if start_time:
        # shift the start_time by 1 sec
        start_time = (datetime.strptime(
            start_time, '%m/%d/%Y %H:%M:%S') + timedelta(seconds=1)).strftime('%m/%d/%Y %H:%M:%S')

    # set the end_time to be now
    end_time = datetime.utcnow()

    # if this is the 1st time, set the start time before endtime and save it in checkpoint
    if start_time is None:
        start_time = (end_time - timedelta(seconds=opt_interval)
                      ).strftime('%m/%d/%Y %H:%M:%S')
        helper.save_check_point(timestamp_key, start_time)

    end_time = end_time.strftime('%m/%d/%Y %H:%M:%S')
    helper.log_debug("[-] Endpoint: {}, start time: {}".format(params['opt_endpoint'], start_time))
    helper.log_debug("[-] Endpoint: {}, end time: {}".format(params['opt_endpoint'], end_time))

    #  Update Parameters
    params.update({"mode": "live"})
    params.update({"start_time": start_time})
    params.update({"end_time": end_time})
    params.update({"timestamp_key": timestamp_key})
        
    records = params['limit']
    offset = 1
    while (records == params['limit']):
        helper.log_debug("[-] Endpoint: {}, current_offset: {}".format(params['opt_endpoint'], offset))
        params['offset'] = offset
        records = fetch_webex_logs(ew, helper, params)

        if records:
            offset += records
