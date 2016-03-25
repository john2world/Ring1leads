import json
import requests
import settings
from simple_salesforce import (
    Salesforce,
    SalesforceExpiredSession,
    SalesforceRefusedRequest
)

from integrations import salesforce
from integrations.salesforce.utils import CustomSalesforceBulk
from accounts.models import CustomUser


class SalesforceExpiredRefreshToken(Exception):
    pass


def get_dev_auth():
    """
    Get developer authentication for testing purposes.
    """

    connection = Salesforce(
        username='josephmfusaro@gmail.com',
        password='johngalt12',
        security_token='lZly1jo8Lhsw9vS3i6KejvDfQ'
    )

    return connection


def get_prod_auth(oauth_token):
    """
    Establish connection with production instance of Salesforce.
    """

    connection = Salesforce(
        instance_url=oauth_token.instance_url,  # ex. 'https://na16.salesforce.com'
        session_id=oauth_token.access_token,
        sandbox=oauth_token.is_sandbox  # Boolean value
    )
    return connection


def get_salesforce_user_info(id_url, access_token):
    """
    The 'id' URL that accompanies the access token and instance URL is the
    gateway to Force.com's Identity Service. We send a GET request to the
    id URL, accompanied by an OAuth authorization HTTP header containing the
    access token, and receive some information about the user and org.
    """

    r = requests.get(id_url + '?access_token=' + access_token)
    user_info = json.loads(r.content)
    return user_info


def refresh_token(oauth_token):
    """
    Salesforce access tokens expire every 60 days. When a user request
    returns "SalesforceExpiredSession" we can use their refresh token to
    request a new access token.
    """

    payload = {
        'grant_type': 'refresh_token',
        'client_id': settings.CONSUMER_KEY,
        'client_secret': settings.CONSUMER_SECRET,
        'refresh_token': oauth_token.refresh_token
    }

    # Post payload to Salesforce Oauth server
    r = requests.post(
        oauth_token.instance_url + '/services/oauth2/token',
        headers={
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        data=payload
    )
    # Decode the JSON response from Salesforce Oauth server
    decoded = json.loads(r.content)
    if 'error' in decoded:
        print decoded
        oauth_token.active = False
        oauth_token.save()
        raise SalesforceExpiredRefreshToken
    else:
        oauth_token.active = True
        oauth_token.access_token = decoded['access_token']
        oauth_token.instance_url = decoded['instance_url']
    oauth_token.save()


def get_refreshed_token(oauth_token, user_id):
    refresh_token(oauth_token)  # Refresh info
    oauth_token = salesforce.models.OauthToken.objects.get(user=user_id)  # Get updated token
    auth = get_prod_auth(oauth_token)  # Reconnect

    return auth


def get_dev_auth_for_bulk(email):
    """
    Get developer authentication for bulk.
    """
    user = CustomUser.objects.get(email=email)

    token = salesforce.models.OauthToken.objects.get(user=user)
    token.refresh()

    connection = get_prod_auth_for_bulk(token)

    # connection = CustomSalesforceBulk(
    # username=salesforce_dev_keys['username'],
    #     password=salesforce_dev_keys['password'],
    #     token=salesforce_dev_keys['token'],
    #     client_id=salesforce_dev_keys['client_id'],  #Consumer Key
    #     client_secret=salesforce_dev_keys['client_secret']  #Consumer Secret
    #     )

    # auth_info = salesforce.models.OauthToken.objects.get(user='00530000001rbG0AAI')
    # connection = get_prod_auth_for_bulk(auth_info)

    return connection


def get_prod_auth_for_bulk(oauth_token):
    """
    Establish connection with production instance of Salesforce.
    """

    connection = CustomSalesforceBulk(
        host=oauth_token.instance_url,
        sessionId=oauth_token.access_token
    )

    return connection
