__author__ = 'edwinalvarado'

from integrations.salesforce.auth import get_dev_auth_for_bulk

auth = get_dev_auth_for_bulk()
query = """SELECT Id, Email FROM Lead"""
out = auth.process_SOQL_with_auth(query)