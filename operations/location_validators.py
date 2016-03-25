import sys
import rollbar
from operations.exceptions import InsufficientCreditsError
from rl_proto2.settings import google_api_key

from pygeocoder import Geocoder
from pygeolib import GeocoderError, GeocoderResult


class ValidationException(Exception):
    pass

class LocationValidator(object):
    """
    Abstract class for location validations
    """

    def validate(self, location):
        raise ValidationException("Unknown Exception is occured.")

class CustomGeocodeResult(GeocoderResult):

    @property
    def valid_address(self):
        """
        Returns true if queried address is valid street address
        """
        return self.current_data['types'] in [[u'street_address'], [u'subpremise']]

class CustomGeocoder(Geocoder):
    def geocode(self, address, sensor='false', bounds='', region='', language=''):
        """
        Given a string address, return a dictionary of information about
        that location, including its latitude and longitude.
        :param address: Address of location to be geocoded.
        :type address: string
        :param sensor: ``'true'`` if the address is coming from, say, a GPS device.
        :type sensor: string
        :param bounds: The bounding box of the viewport within which to bias geocode results more prominently.
        :type bounds: string
        :param region: The region code, specified as a ccTLD ("top-level domain") two-character value for biasing
        :type region: string
        :param language: The language in which to return results.
        :type language: string
        :returns: `geocoder return value`_ dictionary
        :rtype: dict
        :raises GeocoderError: if there is something wrong with the query.
        For details on the input parameters, visit
        http://code.google.com/apis/maps/documentation/geocoding/#GeocodingRequests
        For details on the output, visit
        http://code.google.com/apis/maps/documentation/geocoding/#GeocodingResponses
        """

        params = {
            'address':  address,
            'sensor':   sensor,
            'bounds':   bounds,
            'region':   region,
            'language': language,
        }

        if self is not None:
            return CustomGeocodeResult(self.get_data(params=params))
        else:
            return CustomGeocodeResult(CustomGeocoder.get_data(params=params))


class GeocodeValidator(LocationValidator):

    def validate(self, location):
        if not location:
            raise ValueError("Location argument should be a non-empty dictionary")

        try:
            address = CustomGeocoder(google_api_key).geocode(', '.join('' if not value else value.encode('utf-8') for key, value in location.items()))
        except GeocoderError as e:
            if e.status == GeocoderError.G_GEO_OVER_QUERY_LIMIT:
                rollbar.report_exc_info(sys.exc_info(), extra_data={'API': 'Google Geocoding', 'message': e.message})
                raise InsufficientCreditsError(e.status)
            raise ValidationException("The address entered could not be geocoded. %s exception is occured." % e.message)

        return {
            'valid': address.valid_address,
            'valid_address': {
                'street': ''.join([(unicode(address.street_number) + ' ') if address.street_number else '',
                                   unicode(address.route) if address.route else '']),
                'unit': unicode(address.subpremise),
                'city': unicode(address.city),
                'state': unicode(address.state),
                'zipcode': unicode(address.postal_code),
                'country': unicode(address.country)
            }
        }
