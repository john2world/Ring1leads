import pycountry
from django.template.defaultfilters import slugify


country_cache = {}


def get_country_code(country_name):
    """
    Return the ISO country code from an official or colloquial country name.
    """
    # TODO: better country parsing with something like geodict or a nlp dataset
    if not country_cache:
        for country in pycountry.countries:
            country_cache[country.alpha3.lower()] = country.alpha2
            country_cache[country.alpha2.lower()] = country.alpha2
            country_cache[slugify(country.name)] = country.alpha2
            if hasattr(country, 'official_name'):
                country_cache[slugify(country.official_name)] = country.alpha2
    try:
        country_code = country_cache[slugify(country_name)]
    except KeyError:
        country_code = ''
    return country_code
