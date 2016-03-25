from simple_salesforce import Salesforce


def record_count(authentication, tables, conditions=None):
    """ Get a record count for some table(s) with optional filters """

    query = """
        SELECT COUNT()
        FROM {tables}
        WHERE {conditions}
        """.format(tables=tables, conditions=conditions)
    # Execute the request via API and get a count
    count = authentication.query(query)

    return count['totalSize']
