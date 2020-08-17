from splunk.persistconn.application import PersistentServerConnectionApplication
import os
import sys
import json
import logging
import requests

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


def write_to_file(message):
    f = open(creds_file_name, "w")
    f.write(message)
    f.close()


def read_file():
    f = open(creds_file_name, "r")
    message = f.read()
    f.close()
    return message


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
        # logging.debug('type of in_string: {}'.format(type(in_string)))
        # logging.debug('in_string: {}'.format(in_string))
        method = request['method'].encode('utf8')
        # logging.debug('method: {}'.format(method))

        if method == "POST":
            try:
                form_params = flatten_query_params(request['form'])
                logging.debug(
                    'type of form_params: {}'.format(type(form_params)))
                # logging.debug('form_params: {}'.format(form_params))
                client_id = form_params.get("client_id", None).encode('utf8')
                client_secret = form_params.get(
                    "client_secret", None).encode('utf8')

                creds_data = {
                    "client_id": client_id,
                    "client_secret": client_secret
                }
                write_to_file(json.dumps(creds_data))
            except Exception as e:
                logging.debug("err: {}".format(e))
                pass
            return {'payload': request, 'status': 200}
        elif method == "GET":
            # read the creds from log
            creds_dict = read_file()

            if creds_dict:
                creds_dict = json.loads(creds_dict)
                client_id = creds_dict.get("client_id", None).encode('utf8')
                client_secret = creds_dict.get(
                    "client_secret", None).encode('utf8')

                # get the code from request
                query_params = flatten_query_params(request['query'])
                logging.debug('query_params: {}'.format(query_params))
                code = query_params['code']
                code = code.encode('utf8')

                redirect_uri = "http://localhost:8000/en-US/splunkd/__raw/services/cisco-webex-meetings-oauth"
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
                    "POST", url, headers=headers, data=payload)

                logging.debug(
                    "response code-- {}".format(response.status_code))

                status_code = response.status_code

                logging.debug('==============================')
                resp = response.json()

                if status_code != 200:
                    return {'payload': response.text.encode('utf8'), 'status': 200}

                logging.debug('==============================')
                if resp['access_token'] and resp['refresh_token']:
                    result = {
                        "access_token": resp['access_token'].encode('utf8'),
                        "refresh_token": resp['refresh_token'].encode('utf8')
                    }

                logging.debug('type of result: {}'.format(type(result)))
                logging.debug('type of access_token: {}'.format(
                    type(result["access_token"])))
                try:
                    os.system("rm -f {}".format(creds_file_name))
                except Exception as e:
                    logging.debug('os.system error: {}'.format(
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
