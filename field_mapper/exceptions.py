class FieldMapperException(Exception):
    pass


class NotFieldList(FieldMapperException):
    pass


class MissingFields(FieldMapperException):
    pass
