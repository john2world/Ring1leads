CONSUMER_KEY = '3MVG9fMtCkV6eLhcLN21Pu0dMph8eLKABqS_BRDsKDPspdOAA3j0nkknQp9qbgJjTP7cWGdSrZHSlNwj8xdVq'
CONSUMER_SECRET = '1534287628036972415'
# REDIRECT_URI = 'https://dq2.ringlead.com/oauth/salesforce/'
REDIRECT_URI = 'https://ringlead-dqp-001.herokuapp.com/oauth/salesforce/'

SALESFORCE_PROD_AUTH_URL='https://login.salesforce.com/services/oauth2/authorize?response_type=code&client_id=' + CONSUMER_KEY + '&redirect_uri=' + REDIRECT_URI + '&display=popup'
SALESFORCE_SANDBOX_AUTH_URL='https://test.salesforce.com/services/oauth2/authorize?response_type=code&client_id=' + CONSUMER_KEY + '&redirect_uri=' + REDIRECT_URI + '&display=popup&state=is_sandbox'

salesforce_dev_keys = {
    'username': 'hanma10@ca.com',
    'password': '',
    'token': '00D290000000Qm8!AQgAQEKi4S5C0rZBIYwXl87myu8QypG.VZ_q9vMsHop2JsruUDnnQAhFJsRRWpqnLT_zX1PaPRxH6ALI.R4rpEfHBInvoz8Z',
    'client_id': '3MVG9fMtCkV6eLhcLN21Pu0dMph8eLKABqS_BRDsKDPspdOAA3j0nkknQp9qbgJjTP7cWGdSrZHSlNwj8xdVq',
    'client_secret': '1534287628036972415',
    'redirect_uri': 'https://login.salesforce.com/services/oauth2/callback'
}

try:
    from local_settings import *
except ImportError:
    pass
