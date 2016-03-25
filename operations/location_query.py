from location_validators import GeocodeValidator, ValidationException

location_validator = GeocodeValidator()


def get_is_location_valid(location):
    """
    Verify if given location is valid or invalid
    :param location: address information as a dictionary
    :return: verify result as a dictionary
    """
    try:
        result = location_validator.validate(location)
    except ValidationException as e:
        return False

    return result['valid'] == True
