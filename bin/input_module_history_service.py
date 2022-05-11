
# encoding = utf-8

import os
import sys
import time
import datetime
import requests

from datetime import date, timedelta
from datetime import datetime

from utils.webex_constant import authentication_type
from utils.webex_common_functions import fetch_webex_logs, get_slice_time
from utils.access_token_functions import update_access_token_with_validation


def validate_input(helper, definition):
    """Implement your own validation logic to validate the input stanza configurations"""

    start_time_start = definition.parameters.get('start_time_start', None)
    interval = definition.parameters.get('interval', None)
    paging_interval = definition.parameters.get('paging_interval', None)

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

    # validate paging interval
    if paging_interval:
        try:
            int(paging_interval)
        except ValueError:
            raise ValueError("Invalid Paging Interval format. Please enter an Integer.")


def collect_events(helper, ew):
    """Implement your data collection logic here"""

    opt_start_time_start = helper.get_arg('start_time_start')
    opt_endpoints = helper.get_arg('endpoints')
    opt_interval = int(helper.get_arg('interval'))
    opt_live = False
    opt_paging_interval = helper.get_arg('paging_interval')
    opt_paging_interval_unit = helper.get_arg('paging_interval_unit')

    proxy = helper.get_proxy()
    if proxy:
        if proxy.get('proxy_username', None) and proxy.get('proxy_password', None):
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

    # Historical Data
    for opt_endpoint in opt_endpoints:

        # Handle OAuth Situation
        # if password_type is NOT password, override password by access token
        helper.log_debug("[-] Endpoint: {}, password_type: {}".format(opt_endpoint, params['password_type']))
        if params['password_type'] != "password":
            params['opt_client_id'] = helper.get_global_setting("client_id")
            params['opt_client_secret'] = helper.get_global_setting(
                "client_secret")
            params['opt_refresh_token'] = helper.get_global_setting(
                "refresh_token")
            params['redirect_uri'] = helper.get_global_setting(
            "redirect_uri")

            update_access_token_with_validation(helper, params)

        # endtime is midnight of GMT - 3days
        enddt = datetime.utcnow().date() - timedelta(3)
        end_time = datetime.combine(
            enddt, datetime.max.time()).strftime('%m/%d/%Y %H:%M:%S')

        # create checkpoint key for timestamp
        timestamp_key = "timestamp_{}_{}_processing".format(
            helper.get_input_stanza_names(), opt_endpoint)

        start_time = helper.get_check_point(timestamp_key)
        if start_time is None:
            # if it's the 1st time, get the start_time from UI, and then save it in checkpoint
            start_time = opt_start_time_start
            helper.save_check_point(timestamp_key, start_time)
        else:
            # shift the start_time by 1 second
            start_time = (datetime.strptime(start_time, '%m/%d/%Y %H:%M:%S') +
                          timedelta(seconds=1)).strftime('%m/%d/%Y %H:%M:%S')

        helper.log_debug("[-] Endpoint: {}, Start time: {}".format(opt_endpoint, start_time))
        helper.log_debug("[-] Endpoint: {}, End time: {}".format(opt_endpoint, end_time))


        # Paging 
        # slice time range to day by day
        helper.log_debug("[-] Endpoint: {}, opt_paging_interval: {}".format(opt_endpoint, opt_paging_interval))
        helper.log_debug("[-] Endpoint: {}, opt_paging_interval_unit: {}".format(opt_endpoint, opt_paging_interval_unit))

        # get the paging interval from UI, o.w. set it to 1 day
        if opt_paging_interval and opt_paging_interval_unit:
            opt_paging_interval = int(opt_paging_interval)
            if "Sec" in opt_paging_interval_unit:
                steps = opt_paging_interval
            elif "Min" in opt_paging_interval_unit:
                steps = opt_paging_interval * 60
            elif "Hour" in opt_paging_interval_unit:
                steps = opt_paging_interval * 60 * 60
            elif "Day" in opt_paging_interval_unit:
                steps = opt_paging_interval * 60 * 60 * 24
            elif "Week" in opt_paging_interval_unit:
                steps = opt_paging_interval * 60 * 60 * 24 * 7
            elif "Year" in opt_paging_interval_unit:
                steps = opt_paging_interval * 60 * 60 * 24 * 365
            else:
                steps = opt_paging_interval
        else:
            steps = 60*60*24
        
        helper.log_debug("[-] Endpoint: {}, Paging steps: {}".format(opt_endpoint, steps))

        time_list = get_slice_time(start_time, end_time, steps, helper)
        request_cnt = 0
        for time in time_list:
            cur_start_time = time[0]           
            cur_end_time = time[1]
            #  Update Parameters
            params.update({"mode": "historical"})
            params.update({"opt_endpoint": opt_endpoint})
            params.update({"start_time": cur_start_time})
            params.update({"end_time": cur_end_time})
            params.update({"timestamp_key": timestamp_key})

            records = params['limit']
            offset = 1
            while (records == params['limit']):
                request_cnt += 1
                helper.log_debug("[-] Endpoint: {}, current_offset: {}".format(params['opt_endpoint'], offset))
                params['offset'] = offset
                helper.log_debug("[-] Endpoint: {}, {} Ingestion Interval: {}-{}, WebEx Request start time (Local time zone): {}".format(params['opt_endpoint'], request_cnt, cur_start_time, cur_end_time, datetime.now().strftime('%m/%d/%Y %H:%M:%S.%f')))
                records = fetch_webex_logs(ew, helper, params)
                helper.log_debug("[-] Endpoint: {}, {} Ingestion Interval: {}-{}, WebEx Request end time (Local time zone): {}".format(params['opt_endpoint'], request_cnt, cur_start_time, cur_end_time, datetime.now().strftime('%m/%d/%Y %H:%M:%S.%f')))
                helper.log_debug("[-] Endpoint: {}\t Offet:{}\tLimit: {}\tRecords Returned: {}".format(params['opt_endpoint'],
                    offset, params['limit'], records))
                if records:
                    offset += records
            

