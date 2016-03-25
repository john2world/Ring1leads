from django.test import TestCase

from operations.location_validators import GeocodeValidator
from operations.phone_validators import TwilioValidator
from operations.phone_query import get_country_code
from operations.normalizer import ContactsNormalizer


class PhoneValidationTestCase(TestCase):
    def setUp(self):
        self.twilio = TwilioValidator()

    def test_twilio_valid_international_phone(self):
        result = self.twilio.validate('55-11-5525-6325')
        self.assertTrue(result['valid'])

    def test_twilio_country_code(self):
        result = self.twilio.validate('55-11-5525-6325')
        self.assertEqual(result['country_code'], 'BR')

    def test_twilio_empty_country_code(self):
        result = self.twilio.validate('55-11-5525-6325', country='')
        self.assertEqual(result['country_code'], 'BR')

    def test_twilio_carrier(self):
        result = self.twilio.validate('55-11-5525-6325', extra=True)
        self.assertEqual(result['carrier'], 'Vivo')
        self.assertEqual(result['type'], 'landline')

    def test_twilio_local_phone(self):
        result = self.twilio.validate('636412632')
        self.assertFalse(result['valid'])
        result = self.twilio.validate('636412632', country='ES')
        self.assertTrue(result['valid'])
        self.assertEqual(result['country_code'], 'ES')

    def test_twilio_invalid_phone(self):
        result = self.twilio.validate('55-11-5-5-25')
        self.assertFalse(result['valid'])

    def test_get_country_code(self):
        code = get_country_code('United States')
        self.assertEqual(code, 'US')
        code = get_country_code('Spain')
        self.assertEqual(code, 'ES')
        code = get_country_code('USA')
        self.assertEqual(code, 'US')
        code = get_country_code('Neverland')
        self.assertEqual(code, '')

        # def get_percent_valid_location(self):
        #     # TODO: check result isn't always the same with different datasets
        #     value = prepare.get_percent_valid_location(df, 10)
        #     self.assertGreaterEqual(value, 0)
        #     self.assertLowerEqual(value, 100.0)


class LocationValidationTestCase(TestCase):
    def setUp(self):
        self.client = GeocodeValidator()

    def test_validated_address(self):
        validation = self.client.validate({
            'street': '1600 Amphitheatre Pkwy',
            'city': 'Mountain View',
            'state': 'CA',
            'zipcode': '94043',
            'country': 'USA'
        })
        self.assertTrue(validation['valid'])

    def test_invalidated_street(self):
        validation = self.client.validate({
            'street': '160123 Amphitheatre Pkwy',
            'city': 'Mountain View',
            'state': 'CA',
            'zipcode': '94043',
            'country': 'USA'
        })
        self.assertFalse(validation['valid'])
        self.assertEqual('Amphitheatre Parkway', validation['valid_address']['street'])

    def test_invalidated_route(self):
        validation = self.client.validate({
            'street': '1600 abcdAmphitheatre Pkwy',
            'city': 'Mountain View',
            'state': 'CA',
            'zipcode': '94043',
            'country': 'USA'
        })
        self.assertTrue(validation['valid'])
        self.assertEqual('1600 Amphitheatre Parkway', validation['valid_address']['street'])

    def test_invalidated_city(self):
        validation = self.client.validate({
            'street': '1600 abcdAmphitheatre Pkwy',
            'city': 'Mountainab View',
            'state': 'CA',
            'zipcode': '94043',
            'country': 'USA'
        })
        self.assertTrue(validation['valid'])
        self.assertEqual('Mountain View', validation['valid_address']['city'])

    # def test_get_percent_valid_location(self):
    #     from integrations.salesforce.prepare import df
    #     from qscore.prepare import get_percent_valid_location
    #     percent = get_percent_valid_location(df, 6)
    #     self.assertGreaterEqual(percent, 0)

class ContactsNormalizerTestCase(TestCase):
    def setUp(self):
        print "\n\nstarting ContactNormalizer ... \n"
        self.normalizer = ContactsNormalizer(
            # settings={'JobTitle.Case': 'UpperCase'},
            # url_params = {}
        )

    def test_contacts_normalizer(self):
        data = [{
                    "_RecordID": ["abcde12345"],
                    "_Fields": ["standard"],
                    "AddressLine1": ["123 e main st"],
                    "City": ["milwaukee"],
                    "State": ["wi"],
                    "NamePrefix": ["dr"],
                    "FirstName": ["john"],
                    "MiddleName": ["s."],
                    "LastName": ["smith"],
                    "NameSuffix": ["sr"],
                    "JobTitle": ["director of mrktg"],
                    "CompanyName": ["broadlook inc."],
                    "Website": ["http://www.broadlook.com", "http://www.broadlook1.com", "http://www.broadlook2.com"],
                    "Phone": ["2627548080", "2627548081", "2627548082"]
                },
                {
                    "_RecordID": ["abcde12345"],
                    "_Fields": ["custom-mailing-address"],
                    "AddressLine1": ["125 north executive drive"],
                    "AddressLine2": ["SUITE 200"],
                    "City": ["brookfield"],
                    "State": ["wi"]
                }
            ]
        status_code, response = self.normalizer.normalize(data)

        print "Response from API provider \n %r" % response

        self.assertTrue(status_code is 200)

        print "\nended ContactNormalizer!!!\n"
