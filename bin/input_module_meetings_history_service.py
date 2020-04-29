
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
from datetime import date, timedelta
from datetime import datetime

from webex_constant import authentication_type
from webex_common_functions import fetch_webex_logs


def validate_input(helper, definition):
    """Implement your own validation logic to validate the input stanza configurations"""

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
    pass


def collect_events(helper, ew):
    """Implement your data collection logic here
    """

    opt_start_time_start = helper.get_arg('start_time_start')
    opt_endpoints = helper.get_arg('endpoints')
    opt_interval = int(helper.get_arg('interval'))
    opt_live = False

    params = {"opt_username": helper.get_global_setting("username"),
              "opt_password": helper.get_global_setting("password"),
              "opt_site_name": helper.get_global_setting("site_name"),
              "limit": 500,
              "timezone": "20",
              "password_type": authentication_type["Password Authentication"]}

    # Historical Data
    helper.log_debug("Historical Data")
    for opt_endpoint in opt_endpoints:
        helper.log_debug("[-] \t At {}".format(opt_endpoint))

        # endtime is midnight of GMT - 3days
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
            start_time = (datetime.strptime(
                start_time, '%m/%d/%Y %H:%M:%S') + timedelta(seconds=1)).strftime('%m/%d/%Y %H:%M:%S')

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
