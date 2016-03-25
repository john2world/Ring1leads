import csv
import json
import requests
from integrations.storage import open_s3, s3_public_url

# monkey-patch suds to work with unicode data
from suds import client
original_location = client.SoapClient.location
def fixed_location(self):
    return original_location(self).encode('utf-8')
client.SoapClient.location = fixed_location

from sforce.partner import SforcePartnerClient


class SalesforceSOAP(object):
    def __init__(self, token):
        self.token = token
        profile = requests.post(token.id_url, data={'access_token': self.token.access_token})
        self.partner_url = profile.json()['urls']['partner'].replace('{version}', '35.0')
        self.client = SforcePartnerClient('integrations/salesforce/partner.wsdl')
        self.force_oauth_login(self.token.access_token, self.partner_url)
        self.merge_batches = []
        self.merge_queue = []
        self.log = open_s3(token.user.email + '-merge_log', 'wb')
        self.log_writer = csv.writer(self.log)
        self.log_writer.writerow(['Record group', 'Record ID', 'Master ID', 'Canonical'])
        self.merge_count = 0

    def refresh_token(self):
        self.token.refresh()
        self.force_oauth_login(self.token.access_token, self.partner_url)

    def force_oauth_login(self, access_token, soap_endpoint):
        self.client._setHeaders('login')
        header = self.client.generateHeader('SessionHeader')
        header.sessionId = access_token
        self.client.setSessionHeader(header)
        self.client._sessionId = access_token
        self.client._setEndpoint(soap_endpoint)

    def append_merge(self, merge_request):
        self.merge_queue.append(merge_request)
        if len(self.merge_queue) > 6:
            self.merge_batches.append(self.merge_queue)
            self.merge_queue = []

    def commit_merges(self):
        if self.merge_queue:
            self.merge_batches.append(self.merge_queue)
        self.merge_queue = []

        for batch in self.merge_batches:
            self.refresh_token()

            try:
                result = self.client.merge(batch)
            except Exception as e:
                print 'SF SOAP merge batch failed with message: {0}'.format(e.message)  # TODO: log this somewhere
                yield []
            else:
                yield result

    def merge_group(self, group, canonical, updateable):
        self.merge_count += 1
        master = self.client.generateObject('Lead')
        master.Id = group[0]['Id'].decode('utf-8')
        for key, value in canonical.viewitems():
            if value and key in updateable:
                value = value.decode('utf-8')
                setattr(master, key, value)
        self.log_writer.writerow([self.merge_count, group[0]['Id'], '', json.dumps(canonical)])
        for i in range(1, len(group), 2):
            merge_request = self.client.generateObject('MergeRequest')
            merge_request.masterRecord = master
            merge_request.recordToMergeIds = [group[i]['Id'].decode('utf-8')]
            self.log_writer.writerow([self.merge_count, group[i]['Id'], master.Id, json.dumps(canonical)])
            try:
                merge_request.recordToMergeIds.append(group[i + 1]['Id'].decode('utf-8'))
                self.log_writer.writerow([self.merge_count, group[i + 1]['Id'], master.Id, json.dumps(canonical)])
            except IndexError:
                pass
            self.append_merge(merge_request)

