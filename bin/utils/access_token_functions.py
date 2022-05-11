from datetime import datetime, timedelta
import time
import requests
import sys
import splunklib.client as client

SPLUNK_DEST_APP = 'ta-cisco-webex-meetings-add-on-for-splunk'


def get_access_token_by_refresh_token(helper, client_id, client_secret, refresh_token, redirect_uri, proxies):

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
    try:
        response = requests.request("POST", url, headers=headers, data=payload, proxies=proxies)
        helper.log_debug(
            "[-] GET Access Token from Refresh Token: response.status_code: {}".format(response.status_code))
        if response.status_code != 200:
            helper.log_info(
                "\t[-] Error happend to get Access Token from Refresh Token: {}".format(response.text))
        else:
            resp = response.json()
            if resp.get('access_token'):
                access_token = resp['access_token']
                refresh_token = resp['refresh_token']
                expires_in = resp['expires_in']
                return access_token, refresh_token, expires_in
    except Exception as e:
        helper.log_info(
            "[-] WebEx Request Failed to get Access Token from Refresh Token: {}".format(repr(e)))
        raise e


def get_cred_from_password_storage(helper, splunkService, realm, cred_name):
    helper.log_debug(
        "===================get password/storage for {}: {}================".format(realm, cred_name))
    storage_passwords = splunkService.storage_passwords
    try:
        returned_credential = [k for k in storage_passwords if k.content.get(
            'realm') == realm and k.content.get('username') == cred_name]
    except Exception as e:
        helper.log_info(
            "[-] Failed to get {}:{} from password storage. Error Message:  {}".format(realm, cred_name, repr(e)))
        raise e

    if len(returned_credential) == 0:
        return None

    else:
        returned_credential = returned_credential[0]
        return returned_credential.content.get('clear_password')


def update_cred_in_password_storage(helper, splunkService, realm, cred_name, cred_password):
    if get_cred_from_password_storage(helper, splunkService, realm, cred_name):
        try:
            splunkService.storage_passwords.delete(cred_name, realm)
            helper.log_debug(
                "=====Deleted old {}:{}=====".format(realm, cred_name))
        except Exception as e:
            helper.log_info(
                "[-] Failed to delete {}:{} from password storage. Error Message:  {}".format(realm, cred_name, repr(e)))
            raise e
    try:
        returned_credential = splunkService.storage_passwords.create(
            cred_password, cred_name, realm)
        helper.log_debug("=====Updated {}:{}=====".format(realm, cred_name))

    except Exception as e:
        helper.log_info(
            "[-] Failed to update {}:{} from password storage. Error Message:  {}".format(realm, cred_name, repr(e)))
        raise e


def update_access_token_with_validation(helper, params):
    redirect_uri = params['redirect_uri']
    helper.log_debug("redirect_uri : {}".format(redirect_uri))

    # get session key
    session_key = helper.context_meta['session_key']
    # create splunkService
    splunkService = client.connect(token=session_key, app=SPLUNK_DEST_APP)

    # set creds name save to password storage
    access_token_key = "access_token_processing"
    refresh_token_key = "refresh_token_processing"

    # set checkpoint key for expired time
    expiry_key = "expiry_key_for_access_token"

    # set realm
    realm = 'ta-cisco-webex-meetings-add-on-for-splunk'

    # get the access_token and refresh_token from password storage
    access_token = get_cred_from_password_storage(
        helper, splunkService, realm, access_token_key)
    refresh_token = get_cred_from_password_storage(
        helper, splunkService, realm, refresh_token_key)

    # First time / Update from UI -- There is no refresh token and access token in storage/passwords endpoint
    if access_token is None:
        # Check if the refresh token from UI is valid to avoid user enter a wrong refresh token
        first_time_access_token, first_time_refresh_token, expires_in = get_access_token_by_refresh_token(
            helper, params['opt_client_id'], params['opt_client_secret'], params['opt_refresh_token'], redirect_uri, params['proxies'])

        # save the valid refresh token and access token
        if first_time_access_token:
            # save access_token in password storage
            update_cred_in_password_storage(
                helper, splunkService, realm, access_token_key, first_time_access_token)
            # save refresh_token in password storage
            update_cred_in_password_storage(
                helper, splunkService, realm, refresh_token_key, first_time_refresh_token)

            # save checkpoint for access_token's expired_time
            now = datetime.utcnow()
            helper.log_debug("***now*** : {}".format(now))
            delta = int(expires_in) - 100
            expired_time = (now + timedelta(seconds=delta)
                            ).strftime('%m/%d/%Y %H:%M:%S')

            helper.log_debug("***expired_time*** : {}".format(expired_time))
            helper.save_check_point(expiry_key, expired_time)

            # use this valid first_time_access_token to avoid user enter a wrong access token
            params.update({"opt_password": first_time_access_token})
        else:
            helper.log_info(
                "[-] Error happend to Refresh Token Validation, Please check if you enter a correct Refresh Token/Client Id/Client Secret")
    else:
        # check if the access token is expired
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
                new_access_token, new_refresh_token, expires_in = get_access_token_by_refresh_token(helper,
                                                                                                    params['opt_client_id'], params['opt_client_secret'], refresh_token, redirect_uri, params['proxies'])

                # update access_token in password storage
                update_cred_in_password_storage(
                    helper, splunkService, realm, access_token_key, new_access_token)

                # update refresh_token in password storage
                update_cred_in_password_storage(
                    helper, splunkService, realm, refresh_token_key, new_refresh_token)

                # update access_token's expired_time checkpoint
                delta = int(expires_in) - 100
                new_expired_time = (
                    now + timedelta(seconds=delta)).strftime('%m/%d/%Y %H:%M:%S')
                helper.save_check_point(expiry_key, new_expired_time)

                # use the new access_token
                params.update({"opt_password": new_access_token})

