""" Simple Python class to access the Tesla JSON API
https://github.com/gglockner/teslajson

The Tesla JSON API is described at:
http://docs.timdorr.apiary.io/

Example:

import teslajson
c = teslajson.Connection('youremail', 'yourpassword')
v = c.vehicles[0]
v.wake_up()
v.data_request('charge_state')
v.command('charge_start')


Modified by mephisto to get rid of access to a thirdparty

"""

try: # Python 3
    from urllib.parse import urlencode
    from urllib.request import Request, build_opener
    from urllib.request import ProxyHandler, HTTPBasicAuthHandler, HTTPHandler
except: # Python 2
    from urllib import urlencode
    from urllib2 import Request, build_opener
    from urllib2 import ProxyHandler, HTTPBasicAuthHandler, HTTPHandler
import json
import datetime
import calendar

from apiconfig import *

class Connection(object):
    """Connection to Tesla Motors API"""
    def __init__(self,
            email='',
            password='',
            access_token='',
            proxy_url = '',
            proxy_user = '',
            proxy_password = ''):

        """Initialize connection object

        Sets the vehicles field, a list of Vehicle objects
        associated with your account

        Required parameters:
        email: your login for teslamotors.com
        password: your password for teslamotors.com

        Optional parameters:
        access_token: API access token
        proxy_url: URL for proxy server
        proxy_user: username for proxy server
        proxy_password: password for proxy server
        """
        self.proxy_url = proxy_url
        self.proxy_user = proxy_user
        self.proxy_password = proxy_password
        current_client = a_api
        self.baseurl = a_baseurl
        self.api = a_api
        if access_token:
            self.__sethead(access_token)
        else:
            self.oauth = {
                "grant_type" : "password",
                "client_id" : a_id,
                "client_secret" : a_secret,
                "email" : email,
                "password" : password }
            self.expiration = 0 # force refresh
        self.vehicles = [Vehicle(v, self) for v in self.get('vehicles')['response']]

    def refresh_vehicle(self):
        self.vehicles = [Vehicle(v, self) for v in self.get('vehicles')['response']]

    def get(self, command):
        """Utility command to get data from API"""
        return self.post(command, None)

    def post(self, command, data={}):
        """Utility command to post data to API"""
        now = calendar.timegm(datetime.datetime.now().timetuple())
        if now > self.expiration:
            # auth = self.__open("/oauth/token", data=self.oauth)
            # auth['access_token'], auth['created_at'] + auth['expires_in'] - 86400
            self.__sethead('eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Im5ZdVZJWTJTN3gxVHRYM01KMC1QMDJad3pXQSJ9.eyJpc3MiOiJodHRwczovL2F1dGgudGVzbGEuY29tL29hdXRoMi92MyIsImF1ZCI6WyJodHRwczovL293bmVyLWFwaS50ZXNsYW1vdG9ycy5jb20vIiwiaHR0cHM6Ly9hdXRoLnRlc2xhLmNvbS9vYXV0aDIvdjMvdXNlcmluZm8iXSwiYXpwIjoib3duZXJhcGkiLCJzdWIiOiJlYThjMmE2My1iOTEyLTQyNDktYThhYy01Yjg2YjYyODU0NjAiLCJzY3AiOlsib3BlbmlkIiwiZW1haWwiLCJvZmZsaW5lX2FjY2VzcyJdLCJhbXIiOlsicHdkIl0sImV4cCI6MTY4ODMyNzY5OSwiaWF0IjoxNjg4Mjk4ODk5LCJvdV9jb2RlIjoiTkEiLCJhdXRoX3RpbWUiOjE2ODgyOTg4OTh9.sv-FGRLsC9tiSbGq_wFIVWvTbml146W4pyvUMbtvEc3K6i_DfyBD_eYwp8xtqgg_D0NmCJTz5lkFfWiI3WPk4zAdc9SekuvpZcEds73Hgkn7f7iD6lJ3iAzss_zTHvXV9Crew_iMjR9fHGUu2_FggmzlV5glKbQulHW5LQ40RblgoWaHYdS6IrG9ZIHBwd7m-NqQp9v-APDcnkvPyZybA2LKls8UVwwKHRnTHSZsq9JpQgEwLG-V8PWfkKoLf-pe2Z6AaK9dnKiFIcfvwEIco_DOvXfEaStPSwPfTuUXHsCasPqRjTTYAziHwNWcLriV7IesMkrJijenN-xGApP9KA')
        return self.__open("%s%s" % (self.api, command), headers=self.head, data=data)

    def __sethead(self, access_token, expiration=float('inf')):
        """Set HTTP header"""
        self.access_token = access_token
        self.expiration = expiration
        self.head = {"Authorization": "Bearer %s" % access_token}

    def __open(self, url, headers={}, data=None, baseurl=""):
        """Raw urlopen command"""
        if not baseurl:
            baseurl = self.baseurl
        req = Request("%s%s" % (baseurl, url), headers=headers)
        try:
            req.data = urlencode(data).encode('utf-8') # Python 3
        except:
            try:
                req.add_data(urlencode(data)) # Python 2
            except:
                pass

        # Proxy support
        if self.proxy_url:
            if self.proxy_user:
                proxy = ProxyHandler({'https': 'https://%s:%s@%s' % (self.proxy_user,
                                                                     self.proxy_password,
                                                                     self.proxy_url)})
                auth = HTTPBasicAuthHandler()
                opener = build_opener(proxy, auth, HTTPHandler)
            else:
                handler = ProxyHandler({'https': self.proxy_url})
                opener = build_opener(handler)
        else:
            opener = build_opener()
        resp = opener.open(req)
        charset = resp.info().get('charset', 'utf-8')
        content = resp.read().decode(charset)
        return json.loads(content)


class Vehicle(dict):
    """Vehicle class, subclassed from dictionary.

    There are 3 primary methods: wake_up, data_request and command.
    data_request and command both require a name to specify the data
    or command, respectively. These names can be found in the
    Tesla JSON API."""
    def __init__(self, data, connection):
        """Initialize vehicle class

        Called automatically by the Connection class
        """
        super(Vehicle, self).__init__(data)
        self.connection = connection

    def data_request(self, name):
        """Get vehicle data"""
        result = self.get('data_request/%s' % name)
        return result['response']

    def wake_up(self):
        """Wake the vehicle"""
        return self.post('wake_up')

    def command(self, name, data={}):
        """Run the command for the vehicle"""
        return self.post('command/%s' % name, data)

    def get(self, command):
        """Utility command to get data from API"""
        return self.connection.get('vehicles/%i/%s' % (self['id'], command))

    def post(self, command, data={}):
        """Utility command to post data to API"""
        return self.connection.post('vehicles/%i/%s' % (self['id'], command), data)
