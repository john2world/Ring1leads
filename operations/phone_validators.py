import json
import urllib
import requests

from requests.auth import HTTPBasicAuth

from django.conf import settings


class ValidatorServiceError(Exception):
    pass

class PhoneValidator(object):
    '''
    Abstract class for phone number validators.
    '''

    def validate(self, number, extra=True, country='US'):
        '''
        Validates a phone number.

        param number: Phone number.
        param extra: Return extra information such as the carrier.
        param country: The default ISO country code for local phones.
        return: Dictionary with validation results.
                Keys: (bool) `valid`
                      (str) `country_code`
                      (str) `normalized_phone`
                      (str) `type` (`landline` or `mobile` or `voip`)
        '''

        raise ValidatorServiceError('Phone validation service not implemented.')

class TwilioValidator(PhoneValidator):

    def __init__(self):
        self.url = 'https://lookups.twilio.com/v1/PhoneNumbers/%s'
        if not settings.TWILIO_SID:
            raise ValidatorServiceError('TWILIO_SID not provided.')
        if not settings.TWILIO_TOKEN:
            raise ValidatorServiceError('TWILIO_TOKEN not provided.')
        self.auth = HTTPBasicAuth(settings.TWILIO_SID, settings.TWILIO_TOKEN)

    def validate(self, number, extra=True, country='US'):
        url = self.url % urllib.quote(str(number))
        params = {'Type': 'carrier' if extra else 'null',
                  'CountryCode': country}
        r = requests.get(url, params=params, auth=self.auth)
        result = {'valid': False,
                  'normalized_phone': None,
                  'country_code': None,
                  'carrier': None,
                  'type': None}
        if r.status_code == 404:
            return result
        if r.status_code == 403:
            raise ValidatorServiceError('The user with these credentials doesn\'t have access to the Twilio Lookup API.')
        elif r.status_code != 200:
            raise ValidatorServiceError('The Twilio phone validator service is not available at the moment.')
        data = r.json()
        result['valid'] = True
        result['normalized_phone'] = data['phone_number']
        result['country_code'] = data['country_code']
        if extra:
            result['carrier'] = data['carrier']['name']
            result['type'] = data['carrier']['type']
        return result
