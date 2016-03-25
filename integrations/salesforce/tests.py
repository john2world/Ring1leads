# import copy
from django.test import TestCase
from integrations.salesforce.auth import get_dev_auth


class SalesforceSchemaTestCase(TestCase):

    def setUp(self):
        self.sauth = get_dev_auth()

    def test_create_field_from_description(self):
        """
        table = SalesforceTable.objects.create(name='Lead')
        lead_schema = self.sauth.Lead.describe()
        for field in lead_schema['fields']:
            field_model = table.fields.create_from_description(copy.deepcopy(field))
            for key, value in field.viewitems():
                if key != 'picklistValues':
                    self.assertEqual(value, getattr(field_model, key))
                else:
                    for picklist_value in field['picklistValues']:
                        pkv = field_model.picklistValues.get(**picklist_value)
        """
        pass
