from splunk.persistconn.application import PersistentServerConnectionApplication
import os
import sys
import json
import logging
import requests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "utils"))
import splunklib.client as client

if sys.version_info[0] < 3:
    py_version = "aob_py2"
else:
    py_version = "aob_py3"
sys.path.insert(0, os.path.sep.join([os.path.dirname(__file__), 'ta_cisco_webex_meetings_add_on_for_splunk', py_version]))
from solnlib import conf_manager
from solnlib.utils import is_true

SPLUNK_DEST_APP = 'ta-cisco-webex-meetings-add-on-for-splunk'


if sys.platform == "win32":
    import msvcrt
    # Binary mode is required for persistent mode on Windows.
    msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
    msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
    msvcrt.setmode(sys.stderr.fileno(), os.O_BINARY)

logfile = os.sep.join([os.environ['SPLUNK_HOME'], 'var',
                       'log', 'splunk', 'cisco_webex_meetings_oauth_handler.log'])
logging.basicConfig(filename=logfile, level=logging.DEBUG)
creds_file_name = os.sep.join([os.environ['SPLUNK_HOME'], 'var',
                               'log', 'splunk', 'cisco_webex_meetings_oauth_creds.txt'])


def flatten_query_params(params):
    # Query parameters are provided as a list of pairs and can be repeated, e.g.:
    #
    #   "query": [ ["arg1","val1"], ["arg2", "val2"], ["arg1", val2"] ]
    #
    # This function simply accepts only the first parameter and discards duplicates and is not intended to provide an
    # example of advanced argument handling.
    flattened = {}
    for i, j in params:
        flattened[i] = flattened.get(i) or j
    return flattened


def get_cred_from_password_storage(splunkService, realm, cred_name):
    logging.debug(
        "===================get password/storage for {}: {}================".format(realm, cred_name))
    storage_passwords = splunkService.storage_passwords
    try:
        returned_credential = [k for k in storage_passwords if k.content.get(
            'realm') == realm and k.content.get('username') == cred_name]
    except Exception as e:
        logging.info(
            "[-] Failed to get {}:{} from password storage. Error Message:  {}".format(realm, cred_name, repr(e)))
        raise e

    if len(returned_credential) == 0:
        return None

    else:
        returned_credential = returned_credential[0]
        return returned_credential.content.get('clear_password')

def delete_creds_from_password_storage(splunkService, realm, cred_name):
    if get_cred_from_password_storage(splunkService, realm, cred_name):
        try:
            splunkService.storage_passwords.delete(cred_name, realm)
            logging.debug(
                "=====Deleted old {}:{}=====".format(realm, cred_name))
        except Exception as e:
            logging.info(
                "[-] Failed to delete {}:{} from password storage. Error Message:  {}".format(realm, cred_name, repr(e)))
            raise e



def update_creds_from_password_storage(splunkService, realm, cred_name, cred_password):
    delete_creds_from_password_storage(splunkService, realm, cred_name)
    # save it
    try:
        new_credential = splunkService.storage_passwords.create(
            cred_password, cred_name, realm)
        logging.debug("=====Updated {}:{}=====".format(realm, cred_name))
    except Exception as e:
        logging.info(
            "[-] Failed to update {}:{} from password storage. Error Message:  {}".format(realm, cred_name, repr(e)))
        raise e



class CiscoWebexMeetingsOauthHandler(PersistentServerConnectionApplication):
    def __init__(self, _command_line, _command_arg):
        super(PersistentServerConnectionApplication, self).__init__()

    # Handle a syncronous from splunkd.
    def handle(self, in_string):
        """
        Called for a simple synchronous request.
        @param in_string: request data passed in
        @rtype: string or dict
        @return: String to return in response.  If a dict was passed in,
                 it will automatically be JSON encoded before being returned.
        """

        request = json.loads(in_string)
        logging.debug('type of request: {}'.format(type(request)))

        method = request['method']
        logging.debug('method: {}'.format(method))

        # get session_key & creaet splunkService
        session_key = request['session']['authtoken']
        splunkService = client.connect(token=session_key, app=SPLUNK_DEST_APP)

        logging.debug('[-] getting proxy...')
        proxies = self.getProxyDetails(session_key, splunkService)

        realm = 'ta-cisco-webex-meetings-add-on-for-splunk'
        creds_key = "creds_key"
        if method == "POST":
            try:
                form_params = flatten_query_params(request['form'])
                logging.debug(
                    'type of form_params: {}'.format(type(form_params)))
              
                redirect_uri = form_params.get("redirect_uri", None)
                client_id = form_params.get("client_id", None)
                client_secret = form_params.get(
                    "client_secret", None)

                creds_data = {
                    "redirect_uri": redirect_uri,
                    "client_id": client_id,
                    "client_secret": client_secret,
                }
                # save to storage/password endpoint               
                update_creds_from_password_storage(splunkService, realm, creds_key, json.dumps(creds_data))
                logging.debug("Save to storage/password endpoint")
            except Exception as e:
                logging.debug("err: {}".format(e))
                pass
            return {'payload': request, 'status': 200}
        elif method == "GET":
            # Get the creds from storage/password endpoint
            logging.debug("======Getting date from storage/password endpoint ...======")
            creds_dict = get_cred_from_password_storage(splunkService, realm, creds_key)
            
            if creds_dict:
                try:
                    creds_dict = json.loads(creds_dict)
                    redirect_uri = creds_dict.get("redirect_uri", None)
                    client_id = creds_dict.get("client_id", None)
                    client_secret = creds_dict.get(
                        "client_secret", None)

                    # get the code from request
                    query_params = flatten_query_params(request['query'])
                    code = query_params['code']
                    logging.debug("redirect_uri -- {}".format(redirect_uri))

                    url = "https://api.webex.com/v1/oauth2/token"

                    payload = {'grant_type': 'authorization_code',
                               'client_id': client_id,
                               'client_secret': client_secret,
                               'code': code,
                               'redirect_uri': redirect_uri,
                               'code_verifier': 'abc'
                               }
                    headers = {
                        'accept': 'application/json',
                        'Content-Type': 'application/x-www-form-urlencoded'
                    }

                    response = requests.request(
                        "POST", url, headers=headers, data=payload, proxies=proxies)

                    logging.debug(
                        "response code -- {}".format(response.status_code))

                    status_code = response.status_code

                    resp = response.json()

                    if status_code != 200:
                        return {'payload': response.text, 'status': 200}

                    if resp['access_token'] and resp['refresh_token']:
                        result = '''
                        <div style='width:510px;'>
                            <h1>Permissions Granted!</h1>
                        </div>
                        <div style='word-break: break-all;'>
                            <h3>Please Copy the Access Token and Refresh Token</h3>
                            <br>
                            <h4>Access Token</h4>
                            <p>{access_token}</p>
                            <br>
                            <h4>Refresh Token</h4>
                            <p>{refresh_token}</p>
                        </div>
                        ''' .format(access_token=resp['access_token'], refresh_token=resp['refresh_token'])

                except Exception as e:
                    logging.debug("Payload error: {}".format(e))
                try:
                    os.system("rm -f {}".format(creds_file_name))
                except Exception as e:
                    logging.debug('os.system error: {}'.format(
                        e))
                
                # TODO delete the creds inside the password storage if it is there.              
                try: 
                
                    logging.debug("======Delete old Creds if exist======")    
                    
                    access_token_key = "access_token_processing"
                    refresh_token_key = "refresh_token_processing"

                    # delete if exist 
                    delete_creds_from_password_storage(splunkService, realm, access_token_key)
                    delete_creds_from_password_storage(splunkService, realm, refresh_token_key)
                    logging.debug("======Done======")
                except Exception as e:
                    logging.debug('Error happend when updated creds in storage/password endpoint. \n Error message: {}'.format(
                        e))

                return {'payload': result, 'status': 200}

    def handleStream(self, in_string):
        """
        For future use
        """
        raise NotImplementedError(
            "PersistentServerConnectionApplication.handleStream")

    def done(self):
        """
        Virtual method which can be optionally overridden to receive a
        callback after the request completes.
        """
        pass

    def getProxyDetails(self, session_key, splunkService):
        try:
            # Create confmanger object for the app with realm
            realm = "__REST_CREDENTIAL__#ta-cisco-webex-meetings-add-on-for-splunk#configs/conf-ta_cisco_webex_meetings_add_on_for_splunk_settings"
            cfm = conf_manager.ConfManager(session_key, SPLUNK_DEST_APP, realm=realm)
            # Get Conf object of apps settings
            conf = cfm.get_conf('ta_cisco_webex_meetings_add_on_for_splunk_settings')
            # Get proxy stanza from the settings
            proxy = conf.get("proxy", True)

            if not proxy or not is_true(proxy.get('proxy_enabled')):
                logging.info('[-] Proxy is not enabled')
                return None

            if proxy['proxy_username'] and proxy['proxy_password']:
                proxy_password_dict = json.loads(get_cred_from_password_storage(splunkService, realm, 'proxy``splunk_cred_sep``1'))
                clear_proxy_password = proxy_password_dict['proxy_password']

                proxy_auth = "{}:{}".format(
                    proxy['proxy_username'], clear_proxy_password)
                proxies = {
                    "https": "{protocol}://{auth}@{host}:{port}/".format(protocol=proxy['proxy_type'], auth=proxy_auth, host=proxy['proxy_url'], port=proxy['proxy_port']),
                    "http": "{protocol}://{auth}@{host}:{port}/".format(protocol=proxy['proxy_type'], auth=proxy_auth, host=proxy['proxy_url'], port=proxy['proxy_port'])
                }
            else:
                proxies = {
                    "https": "{protocol}://{host}:{port}/".format(protocol=proxy['proxy_type'], host=proxy['proxy_url'], port=proxy['proxy_port']),
                    "http": "{protocol}://{host}:{port}/".format(protocol=proxy['proxy_type'], host=proxy['proxy_url'], port=proxy['proxy_port'])
                }

            return proxies
        except Exception as e:
            logging.error('[-] Error happened while getting proxy details: {}'.format(str(e)))