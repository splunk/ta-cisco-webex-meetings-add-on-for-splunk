from datetime import datetime, timedelta
import time
import requests
import sys
import splunklib.client as client
from utils.webex_common_functions import is_access_token_valid

SPLUNK_DEST_APP = 'ta-cisco-webex-meetings-add-on-for-splunk'


def get_access_token_by_refresh_token(helper, client_id, client_secret, refresh_token, redirect_uri):

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
        response = requests.request("POST", url, headers=headers, data=payload)
        helper.log_debug(
            "[-] GET Access Token from Refresh Token: response.status_code: {}".format(response.status_code))
        if response.status_code != 200:
            helper.log_info(
                "\t[-] Error happend to get Access Token from Refresh Token: {}".format(response.text))

        resp = response.json()
        helper.log_debug("resp.get('access_token') : {}".format(resp.get('access_token')))
        if resp.get('access_token'):
            access_token = resp['access_token']
            refresh_token = resp['refresh_token']
            expires_in = resp['expires_in']
            return access_token, refresh_token, expires_in
        
        # TODO Do I need to add else clause

    except Exception as e:
        helper.log_info(
            "[-] WebEx Request Failed to get Access Token from Refresh Token: {}".format(repr(e)))
        raise e


def delete_cred_from_password_storage(helper, session_key, realm, cred_name):
    splunk_dest_app = 'ta-cisco-webex-meetings-add-on-for-splunk'
    # splunkService = client.connect(host=splunk_server, port=8089,
    #                                username=splunk_admin, password=splunk_password, app=splunk_dest_app)
    splunkService = client.connect(token=session_key, app=SPLUNK_DEST_APP)
    # helper.log_debug("splunkService: {}".format(splunkService))
    splunkService.storage_passwords.delete(cred_name, realm)
    helper.log_debug(
        "===================deleted {} : {}================".format(realm, cred_name))


def get_cred_from_password_storage(helper, session_key, realm, cred_name):
    # splunkServer = 'localhost'
    # splunkAdmin = 'admin'
    # splunkPassword = 'changeme'
    # splunk_dest_app = 'ta-cisco-webex-meetings-add-on-for-splunk'

    helper.log_debug("===================get password/storage for {}: {}================".format(realm, cred_name))
    splunkService = client.connect(token=session_key, app=SPLUNK_DEST_APP)

    # splunkService = client.connect(host=splunk_server, port=8089,
    #                                username=splunk_admin, password=splunk_password, app=splunk_dest_app)
    # helper.log_debug("splunkService: {}".format(splunkService))

    storage_passwords = splunkService.storage_passwords
    # helper.log_debug("storage_passwords: {}".format(storage_passwords))
    try:
        returned_credential = [k for k in storage_passwords if k.content.get(
            'realm') == realm and k.content.get('username') == cred_name]
        helper.log_debug("returned_credential : {}".format(returned_credential))
    except Exception as e:
        helper.log_info(
            "[-] Failed to get {}:{} from password storage. Error Message:  {}".format(realm, cred_name, repr(e)))
        raise e
    
    if len(returned_credential) == 0:
        return None
        
    else:
        returned_credential = returned_credential[0]
        helper.log_debug(
            "returned_credential[0] : {}".format(returned_credential))
        # helper.log_debug(
        #     "returned_credential.content: {}".format(returned_credential.content))
        helper.log_debug("returned_credential.content.get('username'): {}".format(
            returned_credential.content.get('username')))
        helper.log_debug(
            "returned_credential.content.get('clear_password'): {}".format(returned_credential.content.get('clear_password')))
        return returned_credential.content.get('clear_password')
       

def update_cred_in_password_storage(helper, session_key, realm, cred_name, cred_password):
    # splunk_dest_app = 'ta-cisco-webex-meetings-add-on-for-splunk'

    splunkService = client.connect(token=session_key, app=SPLUNK_DEST_APP)
    # splunkService = client.connect(host=splunk_server, port=8089,
    #                                username=splunk_admin, password=splunk_password, app=splunk_dest_app)
    # helper.log_debug("splunkService: {}".format(splunkService))

    if get_cred_from_password_storage(helper, session_key, realm, cred_name):
        try:
            splunkService.storage_passwords.delete(cred_name, realm)
            helper.log_debug("=====Deleted old {}:{}=====".format(realm, cred_name))
        except Exception as e:
            helper.log_info(
                "[-] Failed to delete {}:{} from password storage. Error Message:  {}".format(realm, cred_name, repr(e)))
            raise e
    try:
        returned_credential = splunkService.storage_passwords.create(
            cred_password, cred_name, realm)
        helper.log_debug("=====Updated {}:{}=====".format(realm, cred_name))
        helper.log_debug("after returned_credential.content.get('username'): {}".format(
            returned_credential.content.get('username')))
        helper.log_debug(
            "after returned_credential.content.get('clear_password'): {}".format(returned_credential.content.get('clear_password')))
        # helper.log_debug(
        #     "after returned_credential.content: {}".format(returned_credential.content))
    except Exception as e:
        helper.log_info(
            "[-] Failed to update {}:{} from password storage. Error Message:  {}".format(realm, cred_name, repr(e)))
        raise e



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
        new_access_token, new_refresh_token, expires_in = get_access_token_by_refresh_token(helper,
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
    
    # get session key
    session_key = helper.context_meta['session_key']
    helper.log_debug(
        "Session key ------- {}".format(session_key))

    # set creds name save to password storage
    access_token_key = "access_token_processing"
    refresh_token_key = "refresh_token_processing"

    # set checkpoint key for expired time
    expiry_key = "expiry_key_for_access_token"

    # set realm
    realm = 'ta-cisco-webex-meetings-add-on-for-splunk'


    # get the access_token and refresh_token from password storage
    access_token = get_cred_from_password_storage(
        helper, session_key, realm, access_token_key)
    refresh_token = get_cred_from_password_storage(
        helper, session_key, realm, refresh_token_key)

    # TODO MUST delete later
    helper.log_debug("access_token : {}".format(access_token))
    helper.log_debug("refresh_token : {}".format(refresh_token))

    # First time
    if access_token is None:      
        # save access_token in password storage
        update_cred_in_password_storage(
            helper, session_key, realm, access_token_key, params['opt_password'])
        # save refresh_token in password storage
        update_cred_in_password_storage(
            helper, session_key, realm, refresh_token_key, params['opt_refresh_token'])
        

        # save checkpoint for access_token's expired_time
        now = datetime.utcnow()
        helper.log_debug("***now*** : {}".format(now))
        expired_time = (now + timedelta(seconds=7000)
                        ).strftime('%m/%d/%Y %H:%M:%S')

        helper.log_debug("***expired_time*** : {}".format(expired_time))
        helper.save_check_point(expiry_key, expired_time)
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
                    params['opt_client_id'], params['opt_client_secret'], refresh_token, redirect_uri)

                # update access_token in password storage
                update_cred_in_password_storage(
                    helper, session_key, realm, access_token_key, new_access_token)

                # update refresh_token in password storage
                update_cred_in_password_storage(
                    helper, session_key, realm, refresh_token_key, new_refresh_token)

                # update access_token's expired_time checkpoint
                delta = int(expires_in) - 100
                new_expired_time = (
                    now + timedelta(seconds=delta)).strftime('%m/%d/%Y %H:%M:%S')
                helper.save_check_point(expiry_key, new_expired_time)

                # use the new access_token
                params.update({"opt_password": new_access_token})
    # delete the access_token and refresh_token from password storage

    # delete_cred_from_password_storage(
    #     helper, session_key, realm, access_token_key)

    # delete_cred_from_password_storage(
    #     helper, session_key, realm, refresh_token_key)


# def update_access_token_with_validation(helper, params):
#     get_access_token(helper)
#     # set the redirect_uri
#     redirect_uri = "http://{}:8000/en-US/splunkd/__raw/services/cisco-webex-meetings-oauth".format(
#         params['hostname'])
#     helper.log_debug("redirect_uri : {}".format(redirect_uri))

#     access_token_key = "access_token_processing"
#     refresh_token_key = "refresh_token_processing"

#     get the access_token form checkpoint
#     access_token = helper.get_check_point(access_token_key)
#     refresh_token = helper.get_check_point(refresh_token_key)

#     # First time
#     if access_token is None:
#         # save checkpoint for access_token
#         access_token = params['opt_password']
#         helper.save_check_point(access_token_key, access_token)
#         # save refresh_token
#         helper.save_check_point(refresh_token_key, params['opt_refresh_token'])

#         # save checkpoint for access_token's expired_time
#         expiry_key = "expiry_key_for_{}".format(access_token)
#         now = datetime.utcnow()
#         helper.log_debug("***now*** : {}".format(now))
#         expired_time = (now + timedelta(seconds=7000)
#                         ).strftime('%m/%d/%Y %H:%M:%S')

#         helper.log_debug("***expired_time*** : {}".format(expired_time))
#         helper.save_check_point(expiry_key, expired_time)
#     else:
#         # check if the access token is expired
#         expiry_key = "expiry_key_for_{}".format(access_token)
#         expired_time = helper.get_check_point(expiry_key)

#         if expired_time:
#             expired_time = datetime.strptime(expired_time, '%m/%d/%Y %H:%M:%S')
#             now = datetime.utcnow()
#             helper.log_debug("___now___ : {}".format(now))
#             helper.log_debug("___expired_time___ : {}".format(expired_time))
#             # if it's not expired, use it directly
#             if now < expired_time:
#                 helper.log_debug("================NOT EXPIRED==============")
#                 params.update({"opt_password": access_token})
#             # o.w get a new access token using refresh token
#             else:
#                 # update access_token
#                 helper.log_debug(
#                     "################# EXPIRED ##################")
#                 new_access_token, new_refresh_token, expires_in = get_access_token_by_refresh_token(helper,
#                     params['opt_client_id'], params['opt_client_secret'], refresh_token, redirect_uri)

#                 # update access_token checkpoint
#                 helper.save_check_point(access_token_key, new_access_token)

#                 # update refresh_token checkpoint
#                 helper.save_check_point(refresh_token_key, new_refresh_token)

#                 # update access_token's expired_time checkpoint
#                 delta = int(expires_in) - 100

#                 helper.delete_check_point(expiry_key)

#                 new_expiry_key = "expiry_key_for_{}".format(new_access_token)
#                 new_expired_time = (
#                     now + timedelta(seconds=delta)).strftime('%m/%d/%Y %H:%M:%S')
#                 helper.save_check_point(new_expiry_key, new_expired_time)

#                 params.update({"opt_password": new_access_token})
