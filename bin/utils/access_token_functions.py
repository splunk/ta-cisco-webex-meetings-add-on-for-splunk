import requests
import time
from datetime import datetime, timedelta


def get_access_token_by_refresh_token(client_id, client_secret, refresh_token, redirect_uri):

    url = "https://api.webex.com/v1/oauth2/token"

    payload = {'grant_type': 'refresh_token',
               'client_id': client_id,
               'client_secret': client_secret,
               'refresh_token': refresh_token,
               'redirect_uri': redirect_uri,
               'code_verifier': 'abc'
               }

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    resp = response.json()
    access_token = resp['access_token']
    refresh_token = resp['refresh_token']
    expires_in = resp['expires_in']
    return access_token, refresh_token, expires_in


def update_access_token(helper, params):
    # set the redirect_uri
    redirect_uri = "http://{}:8000/en-US/splunkd/__raw/services/cisco-webex-meetings-oauth".format(
        params['hostname'])
    helper.log_debug("redirect_uri : {}".format(redirect_uri))

    refresh_token_key = "refresh_token_processing"

    # get the refresh_token form checkpoint
    refresh_token = helper.get_check_point(refresh_token_key)

    # first time get the refresh_token and access_token from UI
    if refresh_token is None:
        # save checkpoint for refresh_token
        helper.save_check_point(refresh_token_key, params['opt_refresh_token'])
    else:
        new_access_token, new_refresh_token, expires_in = get_access_token_by_refresh_token(
            params['opt_client_id'], params['opt_client_secret'], refresh_token, redirect_uri)
        # update access_token
        params.update({"opt_password": new_access_token})
        # update checkpoint for refresh_token
        helper.save_check_point(refresh_token_key, new_refresh_token)


def update_access_token_with_validation(helper, params):
    # set the redirect_uri
    redirect_uri = "http://{}:8000/en-US/splunkd/__raw/services/cisco-webex-meetings-oauth".format(
        params['hostname'])
    helper.log_debug("redirect_uri : {}".format(redirect_uri))

    access_token_key = "access_token_processing"
    refresh_token_key = "refresh_token_processing"

    # get the access_token form checkpoint
    access_token = helper.get_check_point(access_token_key)
    refresh_token = helper.get_check_point(refresh_token_key)

    # First time
    if access_token is None:
        # save checkpoint for access_token
        access_token = params['opt_password']
        helper.save_check_point(access_token_key, access_token)
        # save refresh_token
        helper.save_check_point(refresh_token_key, params['opt_refresh_token'])

        # save checkpoint for access_token's expired_time
        expiry_key = "expiry_key_for_{}".format(access_token)
        now = datetime.utcnow()
        helper.log_debug("***now*** : {}".format(now))
        expired_time = (now + timedelta(seconds=7000)
                        ).strftime('%m/%d/%Y %H:%M:%S')

        helper.log_debug("***expired_time*** : {}".format(expired_time))
        helper.save_check_point(expiry_key, expired_time)
    else:
        # check if the access token is expired
        expiry_key = "expiry_key_for_{}".format(access_token)
        expired_time = helper.get_check_point(expiry_key)

        if expired_time:
            expired_time = datetime.strptime(expired_time, '%m/%d/%Y %H:%M:%S')
            now = datetime.utcnow()
            helper.log_debug("___now___ : {}".format(now))
            helper.log_debug("___expired_time___ : {}".format(expired_time))
            # if it's not expired, use it directly
            if now < expired_time:
                helper.log_debug("================NOT EXPIRED==============")
                params.update({"opt_password": access_token})
            # o.w get a new access token using refresh token
            else:
                # update access_token
                helper.log_debug(
                    "################# EXPIRED ##################")
                new_access_token, new_refresh_token, expires_in = get_access_token_by_refresh_token(
                    params['opt_client_id'], params['opt_client_secret'], refresh_token, redirect_uri)

                # update access_token checkpoint
                helper.save_check_point(access_token_key, new_access_token)

                # update refresh_token checkpoint
                helper.save_check_point(refresh_token_key, new_refresh_token)

                # update access_token's expired_time checkpoint
                delta = int(expires_in) - 100

                helper.delete_check_point(expiry_key)

                new_expiry_key = "expiry_key_for_{}".format(new_access_token)
                new_expired_time = (
                    now + timedelta(seconds=delta)).strftime('%m/%d/%Y %H:%M:%S')
                helper.save_check_point(new_expiry_key, new_expired_time)

                params.update({"opt_password": new_access_token})
