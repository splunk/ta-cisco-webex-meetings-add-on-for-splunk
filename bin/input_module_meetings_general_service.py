
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


def validate_input(helper, definition):
    """Implement your own validation logic to validate the input stanza configurations"""

    live = definition.parameters.get('live', 1)
    interval = definition.parameters.get('interval', None)

    if int(interval) > 60:
        raise ValueError(
            "Interval should be 60 or less for general service session data, not {}.".format(interval))

    pass


def collect_events(helper, ew):
    """Implement your data collection logic here
    """

    opt_endpoints = helper.get_arg('endpoint')
    opt_interval = int(helper.get_arg('interval'))
    opt_live = helper.get_arg('live')

    params = {"opt_username": helper.get_global_setting("username"),
              "opt_password": helper.get_global_setting("password"),
              "opt_site_name": helper.get_global_setting("site_name"),
              "limit": 500,
              "timezone": "20",
              "password_type": authentication_type["Password Authentication"]}

    params.update({"opt_endpoint": "LstsummarySession"})

    timestamp_key = "timestamp_{}_{}_processing".format(
        helper.get_input_stanza_names(), params['opt_endpoint'])

    start_time = helper.get_check_point(timestamp_key)
    helper.log_debug("timestamp_value: {}".format(start_time))
    if start_time:
        start_time = (datetime.strptime(
            start_time, '%m/%d/%Y %H:%M:%S') + timedelta(seconds=1)).strftime('%m/%d/%Y %H:%M:%S')

    end_time = datetime.utcnow()

    if start_time is None:
        start_time = (end_time - timedelta(seconds=opt_interval)
                      ).strftime('%m/%d/%Y %H:%M:%S')
        helper.log_debug("type of start time: {}".format(type(start_time)))
        helper.log_debug("***start time***: {}".format(start_time))
        helper.save_check_point(timestamp_key, start_time)

    helper.log_debug("type of start time: {}".format(type(start_time)))
    helper.log_debug("---start time---: {}".format(start_time))

    end_time = end_time.strftime('%m/%d/%Y %H:%M:%S')
    helper.log_debug("start time: {}".format(start_time))
    helper.log_debug("end time: {}".format(end_time))

    #  Update Parameters
    params.update({"mode": "live"})
    params.update({"start_time": start_time})
    params.update({"end_time": end_time})
    params.update({"timestamp_key": timestamp_key})

    records = params['limit']
    offset = 1
    while (records == params['limit']):
        helper.log_debug("current_offset: {}".format(offset))
        params['offset'] = offset
        records = fetch_webex_logs(ew, helper, params)

        if records:
            offset += records
