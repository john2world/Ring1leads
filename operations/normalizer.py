import json

from django.conf import settings
import requests


# http://normalizer.crmshield.com/ <- list of possible options


class ContactsNormalizer(object):
    selector = 'api2/normalizer/contacts'
    url_params = {
        'capp': 'CrmShield-Salesforce',
        'cver': '0.1.0',
        'cplat': 'Salesforce',
        'cdev': ''
    }

    contacts = []

    settings = {
        'JobTitle.Case': 'ProperCase',
        'JobTitle.CXO': 'Abbreviate',
        'JobTitle.DepartmentLiteral': 'Expand',
        'JobTitle.DepartmentNames': 'Expand',
        'JobTitle.Director': 'Expand',
        'JobTitle.Hyphens': 'RemoveSpace',
        'JobTitle.Manager': 'Expand',
        'JobTitle.ModifierPrefixes': 'Expand',
        'JobTitle.Order': 'DepartmentLast',
        'JobTitle.Periods': 'Add',
        'JobTitle.AndUsage': 'ConvertToAnd',
        'JobTitle.OfUsage': 'ConvertToComma',
        'JobTitle.VP': 'Expand',
        'URL.Protocol': 'Remove',
        'URL.TrailingSlash': 'Remove',
        'URL.WWW': 'Remove',
        'CompanyName.Case': 'ProperCase',
        'CompanyName.Periods': 'Remove',
        'CompanyName.Commas': 'Remove',
        'CompanyName.Hyphens': 'RemoveSpace',
        'CompanyName.LeadingArticles': 'MoveToEnd',
        'CompanyName.AndCompany': 'ConvertToAndCompany',
        'CompanyName.AndUsage': 'ConvertToAnd',
        'CompanyName.Suffixes': 'Abbreviate',
        'CompanyName.SuffixesGroup': 'Expand',
        'CompanyName.SuffixesCompany': 'Abbreviate',
        'CompanyName.AKA': 'Remove',
        'CompanyName.Parentheses': 'Remove',
        'CompanyName.Ordinals': 'Expand',
        'CompanyName.Whitespace': 'Compact',
        'Name.Case': 'ProperCase',
        'Name.PeriodsInitials': 'Remove',
        'Name.PeriodsPrefixes': 'Remove',
        'USPhone.Leading1': 'Remove',
        'USPhone.AreaCodeParentheses': 'Remove',
        'USPhone.AreaCodePadding': 'Remove',
        'USPhone.Separator': 'Dash',
        'StreetLine.Case': 'ProperCase',
        'StreetLine.StreetType': 'Abbreviate',
        'StreetLine.CompassDir': 'Abbreviate',
        'StreetLine.UnitDesignators': 'Abbreviate',
        'StreetLine.Periods': 'Remove',
        'City.Case': 'ProperCase',
        'City.Prefixes': 'Abbreviate',
        'City.Periods': 'Remove',
        'StateProvince.Case': 'Uppercase',
        'StateProvince.Format': 'Abbreviate'
    }

    def __init__(self, **kwargs):
        # configuration for sdl parameter
        if 'settings' in kwargs:
            self.settings = kwargs['settings']

        # arguments in url
        if 'url_params' in kwargs:
            url_params = kwargs['url_params']
            if url_params:
                for (key, value) in url_params:
                    self.url_params[key] = value

    def normalize(self, data):
        """
        :param data: Contact dictionary for normalizing
        :return: HTTP status code, normalized contacts
        """
        self.contacts = data
        # set body field
        BOUNDARY = "----MyFormBoundary12345"
        CRLF = "\r\n"

        L = []

        # build main body content
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="contacts"')
        L.append('Content-Type: application/json;')
        L.append('')
        L.append(json.dumps(self.contacts))

        # build sdl body for api
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="process"')
        L.append('Content-Type: application/vnd.broadlook.normalizer.scheme.sdl;')

        sdl_param = []
        for (k, v) in self.settings.iteritems():
            sdl_param.append("%s=%s" % (k,v))

        L.append('; '.join(sdl_param))
        L.append('--' + BOUNDARY + '--')
        L.append('')

        body = CRLF.join(L)

        content_type = "multipart/form-data; boundary=%s" % BOUNDARY

        # send http request to the api provider
        host = settings.NORMALIZER_API_HOST + self.selector
        headers = {'content-Type': content_type}
        res = requests.post(host, params=self.url_params, data=body, headers=headers)

        try:
            return res.status_code, res.json()
        except ValueError:  # TODO: investigate 'Invalid data type assigned to TJSONbase' API responses
            return res.status_code, {}
