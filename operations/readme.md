# Operations

## Overview

## Contacts Normalizer

The Normalizer/Contacts method takes contact information and a normaliztion scheme, and returns normalized contact information.

Reference guide [here](http://apidocs.broadlook.com/home/broadlook-parsing-web-service-api-v2#P2_2)


Please refer operations/normalizer.py.

#### Usage:

```python

    contacts = [{
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
            
    normalizer = ContactsNormalizer()
    
    status_code, normalized_contacts = normalizer.normalize(contacts)
    
```

#### Details:
Users can overwrite normalizer configuration by setting "settings" argument. If user did not set this argument, it will use default configuration.
Here is a sample setting configuration.

```python

    normalizer = ContactsNormalizer(
    
        settings={'JobTitle.Case': 'UpperCase'}
        
    )

```

#### Notes:

contacts parameter must be a list of dictionary.
