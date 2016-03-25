STATUSES = (
    ('CREA', 'Creating'),
    ('PEND', 'Pending'),
    ('CANCEL', 'Cancelled'),
    ('RUN', 'Running'),
    ('PAUSE', 'Paused'),    # When a RealTime Program is inactive, use this
    ('ERROR', 'Error'),
    ('COMPL', 'Completed'),
    ('ACT', 'Active'),   # Only RealTimeProgram can have this status.
    ('ARCH', 'Archived')   # Only RealTimeProgram can have this status.
)

PROGRAM_SOURCES = (
    ('', 'None'),
    ('SALESFORCE', 'Salesforce'),
    ('MARKETO', 'Marketo'),
    ('TRADESHOWOREVENT', 'Tradeshow or Event'),
    ('WEBINAR', 'Webinar'),
    ('WEBSITE', 'Website'),
)

DAYS_OF_WEEK = (
    ('0', 'Monday'),
    ('1', 'Tuesday'),
    ('2', 'Wednesday'),
    ('3', 'Thursday'),
    ('4', 'Friday'),
    ('5', 'Saturday'),
    ('6', 'Sunday'),
)

JOB_STATUSES = (
    ('PENDING', 'Pending'),
    ('STARTED', 'Started'),
    ('RETRY', 'Retrying'),
    ('FAILURE', 'Failure'),
    ('SUCCESS', 'Success')
)

TEXT_EQUALS = 'IS'
TEXT_NOT_EQUALS = 'NOT'
TEXT_CONTAINS = 'CONTAINS'
TEXT_STARTS = 'STARTS'

TEXT_OPERATORS = (
    (TEXT_EQUALS, 'is'),
    (TEXT_NOT_EQUALS, 'is not'),
    (TEXT_CONTAINS, 'contains'),
    (TEXT_STARTS, 'starts with'),
)
NUM_EQUALS = '='
NUM_GREATER = '>'
NUM_LESS = '<'
NUM_OPERATORS = (
    (NUM_EQUALS, 'equals'),
    (NUM_GREATER, 'is greater than'),
    (NUM_LESS, 'is less than'),
)
DATETIME_EQUALS = 'DATE_EXACT'
DATETIME_AFTER = 'DATE_AFTER'
DATETIME_BEFORE = 'DATE_BEFORE'
DATETIME_OPERATORS = (
    (DATETIME_EQUALS, 'is'),
    (DATETIME_AFTER, 'is after'),
    (DATETIME_BEFORE, 'is before'),
)
BOOL_TRUE = 'TRUE'
BOOL_FALSE = 'FALSE'

BOOL_OPERATORS = (
    (BOOL_TRUE, 'True'),
    (BOOL_FALSE, 'False'),
)

MATCH_OPERATORS = (
    ('EXACT', 'is an exact match'),
    ('SIMILAR', 'is very similar'),
    ('LOOSE', 'is somewhat similar'),
)

PICKLIST_OPERATORS = (
    ('PICKLIST_HIERARCHY', 'prioritize'),
)

# Below are choices for SurvivingRecordRule
SR_AGE_OPTIONS = (
    ('NEWEST', 'is newest value'),
    ('OLDEST', 'is oldest value'),
)
SR_NUMBER_OPTIONS = (
    ('LOWEST_VALUE', 'is the lowest value'),
    ('HIGHEST_VALUE', 'is the highest value'),
)

# Below are choices for SurvivingValueRule; broken up into separate variables
# so that in the future, we can supply choices based on field types
SV_AGE_OPERATORS = (
    ('OLDEST', 'keep the oldest value'),
    ('NEWEST', 'keep the newest value'),
)
SV_NUMBER_OPERATORS = (
    ('NUMADD', 'add all values'),
    ('NUMAVG', 'take an average of all values'),
    ('NUMMAX', 'keep the highest value'),
    ('NUMMIN', 'keep the lowest value'),
)

SV_TEXT_OPERATORS = (
    ('CONCAT', 'concatenate all text'),
)

# List of operators that don't require arguments.
UNARY_OPERATORS = SR_NUMBER_OPTIONS + BOOL_OPERATORS + SV_NUMBER_OPERATORS + SV_AGE_OPERATORS + SR_AGE_OPTIONS + SV_TEXT_OPERATORS + PICKLIST_OPERATORS

UPDATE_POLICY_CHOICES = (
    ('OVERWRITE', 'Overwrite'),
    ('UPDATE_IF_BLANK', 'Update if blank'),
    ('DO_NOT_UPDATE', 'Don\'t update'),
)


BROADLOOK_NORMALIZER_FIELDS = [
    {
        'label': 'Company Names',
        'name': 'CompanyName',
        'rules': [
            {
                'label': 'Case',
                'name': 'Case',
                'choices': [
                    ('ProperCase', 'Convert to proper case'),
                    ('None', 'Do nothing'),
                    ('Uppercase', 'Convert to uppercase'),
                    ('Lowercase', 'Convert to lowercase'),
                ]
            },
            {
                'label': 'Periods',
                'name': 'Periods',
                'choices': [
                    ('Add', 'Add'),
                    ('None', 'Do nothing'),
                    ('Remove', 'Remove'),
                ]
            },
            {
                'label': 'Commas',
                'name': 'Commas',
                'choices': [
                    ('SingleSpaceAfter', 'Single space after'),
                    ('None', 'Do nothing'),
                    ('Remove', 'Remove'),
                ]
            },
            {
                'label': 'Hyphens',
                'name': 'Hyphens',
                'choices': [
                    ('PadWithSpace', 'Pad with space'),
                    ('None', 'Do nothing'),
                    ('RemoveSpace', 'Remove surrounding space'),
                    ('Remove', 'Remove'),
                ]
            },
            {
                'label': 'Leading "The"',
                'name': 'LeadingArticles',
                'choices': [
                    ('MoveToBegin', 'Move to beginning'),
                    ('None', 'Do nothing'),
                    ('Remove', 'Remove'),
                    ('MoveToEnd', 'Move to end'),
                ]
            },
            {
                'label': 'Phrase: "and Company"',
                'name': 'AndCompany',
                'choices': [
                    ('ConvertToAndCo', 'Convert to "& Co"'),
                    ('None', 'Do nothing'),
                    ('ConvertToAndCompany', 'Convert to "& Company"'),
                ]
            },
            {
                'label': 'Phrase: "and"',
                'name': 'AndUsage',
                'choices': [
                    ('ConvertToAnd', 'Convert to "and"'),
                    ('None', 'Do nothing'),
                    ('ConvertToAmpersand', 'Convert to "&"'),
                ]
            },
            {
                'label': 'Prefixes',
                'name': 'Prefixes',
                'choices': [
                    ('Abbreviate', 'Abbreviate'),
                    ('None', 'Do nothing'),
                    ('Expand', 'Expand'),
                ]
            },
            {
                'label': 'Suffixes (Inc.)',
                'name': 'Suffixes',
                'choices': [
                    ('Abbreviate', 'Abbreviate'),
                    ('None', 'Do nothing'),
                    ('Expand', 'Expand'),
                ]
            },
            {
                'label': 'Suffixes (Co.)',
                'name': 'SuffixesCompany',
                'choices': [
                    ('Abbreviate', 'Abbreviate'),
                    ('None', 'Do nothing'),
                    ('Expand', 'Expand'),
                ]
            },
            {
                'label': 'Suffixes (Corp.)',
                'name': 'SuffixesCorp',
                'choices': [
                    ('Abbreviate', 'Abbreviate'),
                    ('None', 'Do nothing'),
                    ('Expand', 'Expand'),
                ]
            },
            {
                'label': 'Suffixes (Ltd.)',
                'name': 'SuffixesLtd',
                'choices': [
                    ('None', 'Do nothing'),
                    ('Abbreviate', 'Abbreviate'),
                    ('Expand', 'Expand'),
                ]
            },
            {
                'label': 'Suffixes (Int\'l.)',
                'name': 'SuffixesIntl',
                'choices': [
                    ('None', 'Do nothing'),
                    ('Abbreviate', 'Abbreviate'),
                    ('Expand', 'Expand'),
                ]
            },
            {
                'label': 'Phrase: "aka"',
                'name': 'AKA',
                'choices': [
                    ('Parenthesize', 'Parenthesize'),
                    ('None', 'Do nothing'),
                    ('Remove', 'Remove'),
                ]
            },
            {
                'label': 'Parentheses',
                'name': 'Parentheses',
                'choices': [
                    ('None', 'Do nothing'),
                    ('Remove', 'Remove'),
                    ('RemoveDelimiters', 'Remove delimiters'),
                    ('InsertAKA', 'Insert aka'),
                ]
            },
            {
                'label': 'Ordinals',
                'name': 'Ordinals',
                'choices': [
                    ('None', 'Do nothing'),
                    ('Abbreviate', 'Abbreviate'),
                    ('Expand', 'Expand'),
                ]
            },
            {
                'label': 'Numbers',
                'name': 'Numbers',
                'choices': [
                    ('None', 'Do nothing'),
                    ('SpellOut', 'Spell out'),
                ]
            },
            {
                'label': 'Initials',
                'name': 'Initials',
                'choices': [
                    ('AddPeriods', 'Add periods'),
                    ('None', 'Do nothing'),
                    ('SpaceOnly', 'Space only'),
                    ('Compact', 'Compact'),
                ]
            },
            {
                'label': 'Whitespace',
                'name': 'Whitespace',
                'choices': [
                    ('Compact', 'Compact'),
                    ('None', 'Do nothing'),
                ]
            },
        ]
    },
    {
        'label': 'Names',
        'name': 'Name',
        'rules': [
            {
                'label': 'Case',
                'name': 'Case',
                'choices': [
                    ('ProperCase', 'Convert to proper case'),
                    ('None', 'Do nothing'),
                    ('Uppercase', 'Convert to uppercase'),
                    ('Lowercase', 'Convert to lowercase'),
                ]
            },
            {
                'label': 'First name',
                'name': 'FirstName',
                'choices': [
                    ('None', 'Do nothing'),
                    ('ConvertToInitial', 'Convert to initial'),
                ]
            },
            {
                'label': 'Middle name',
                'name': 'MiddleName',
                'choices': [
                    ('ConvertToInitial', 'Convert to initial'),
                    ('None', 'Do nothing'),
                    ('Remove', 'Remove'),
                ]
            },
            {
                'label': 'Prefixes',
                'name': 'Prefixes',
                'choices': [
                    ('None', 'Do nothing'),
                    ('Remove', 'Remove'),
                ]
            },
            {
                'label': 'Suffixes',
                'name': 'Suffixes',
                'choices': [
                    ('None', 'Do nothing'),
                    ('Remove', 'Remove'),
                ]
            },
            {
                'label': 'Periods (initials)',
                'name': 'PeriodsInitials',
                'choices': [
                    ('Add', 'Add'),
                    ('None', 'Do nothing'),
                    ('Remove', 'Remove'),
                ]
            },
            {
                'label': 'Periods (prefixes)',
                'name': 'PeriodsPrefixes',
                'choices': [
                    ('Add', 'Add'),
                    ('None', 'Do nothing'),
                    ('Remove', 'Remove'),
                ]
            },
            {
                'label': 'Hyphens',
                'name': 'Hyphens',
                'choices': [
                    ('None', 'Do nothing'),
                    ('Remove', 'Remove'),
                ]
            },
        ]
    },
    {
        'label': 'URLs',
        'name': 'URL',
        'rules': [
            {
                'label': 'Path portion',
                'name': 'PathPortion',
                'choices': [
                    ('None', 'Do nothing'),
                    ('Truncate', 'Truncate'),
                ]
            },
            {
                'label': 'Protocol',
                'name': 'Protocol',
                'choices': [
                    ('None', 'Do nothing'),
                    ('Remove', 'Remove'),
                    ('Add', 'Add'),
                ]
            },
            {
                'label': 'Trailing slash',
                'name': 'TrailingSlash',
                'choices': [
                    ('None', 'Do nothing'),
                    ('Remove', 'Remove'),
                    ('Add', 'Add'),
                ]
            },
            {
                'label': 'www',
                'name': 'WWW',
                'choices': [
                    ('None', 'Do nothing'),
                    ('Remove', 'Remove'),
                    ('Add', 'Add'),
                ]
            },
        ]
    },
    {
        'label': 'Street lines',
        'name': 'StreetLine',
        'rules': [
            {
                'label': 'Case',
                'name': 'Case',
                'choices': [
                    ('ProperCase', 'Convert to proper case'),
                    ('None', 'Do nothing'),
                    ('Uppercase', 'Convert to uppercase'),
                    ('Lowercase', 'Convert to lowercase'),
                ]
            },
            {
                'label': 'Multiple lines',
                'name': 'Multiple',
                'choices': [
                    ('CombineOnSingleLine', 'Combine on single line'),
                    ('None', 'Do nothing'),
                    ('DiscardSecondLine', 'Discard second line'),
                ]
            },
            {
                'label': 'Street type',
                'name': 'StreetType',
                'choices': [
                    ('Abbreviate', 'Abbreviate'),
                    ('None', 'Do nothing'),
                    ('Expand', 'Expand'),
                ]
            },
            {
                'label': 'Compass directions',
                'name': 'CompassDir',
                'choices': [
                    ('Abbreviate', 'Abbreviate'),
                    ('None', 'Do nothing'),
                    ('Expand', 'Expand'),
                ]
            },
            {
                'label': 'Unit designators',
                'name': 'UnitDesignators',
                'choices': [
                    ('Expand', 'Expand'),
                    ('None', 'Do nothing'),
                    ('Abbreviate', 'Abbreviate'),
                ]
            },
            {
                'label': 'Periods',
                'name': 'Periods',
                'choices': [
                    ('Add', 'Add'),
                    ('None', 'Do nothing'),
                    ('Remove', 'Remove'),
                ]
            },
        ]
    },
    {
        'label': 'Cities',
        'name': 'City',
        'rules': [
            {
                'label': 'Case',
                'name': 'Case',
                'choices': [
                    ('ProperCase', 'Convert to proper case'),
                    ('None', 'Do nothing'),
                    ('Uppercase', 'Convert to uppercase'),
                    ('Lowercase', 'Convert to lowercase'),
                ]
            },
            {
                'label': 'Prefixes',
                'name': 'Prefixes',
                'choices': [
                    ('Abbreviate', 'Abbreviate'),
                    ('None', 'Do nothing'),
                    ('Expand', 'Expand'),
                ]
            },
            {
                'label': 'Periods',
                'name': 'Periods',
                'choices': [
                    ('Add', 'Add'),
                    ('None', 'Do nothing'),
                    ('Remove', 'Remove'),
                ]
            },
        ]
    },
    {
        'label': 'States and provinces',
        'name': 'StateProvince',
        'rules': [
            {
                'label': 'Case',
                'name': 'Case',
                'choices': [
                    ('Uppercase', 'Convert to uppercase'),
                    ('None', 'Do nothing'),
                    ('Lowercase', 'Convert to lowercase'),
                    ('ProperCase', 'Convert to proper case'),
                ]
            },
            {
                'label': 'Format',
                'name': 'Format',
                'choices': [
                    ('Abbreviate', 'Abbreviate'),
                    ('None', 'Do nothing'),
                    ('Expand', 'Expand'),
                ]
            },
        ]
    },
    {
        'label': 'Phones (US)',
        'name': 'USPhone',
        'rules': [
            {
                'label': 'Leading 1',
                'name': 'Leading1',
                'choices': [
                    ('None', 'Do nothing'),
                    ('Remove', 'Remove'),
                    ('Add', 'Add'),
                    ('ConvertToPlusOne', 'Convert to +1'),
                ]
            },
            {
                'label': 'Area code parentheses',
                'name': 'AreaCodeParentheses',
                'choices': [
                    ('None', 'Do nothing'),
                    ('Remove', 'Remove'),
                    ('Add', 'Add'),
                ]
            },
            {
                'label': 'Area code padding',
                'name': 'AreaCodePadding',
                'choices': [
                    ('None', 'Do nothing'),
                    ('Remove', 'Remove'),
                    ('Add', 'Add'),
                ]
            },
            {
                'label': 'Separator',
                'name': 'Separator',
                'choices': [
                    ('None', 'Do nothing'),
                    ('Dash', '-'),
                    ('Dot', '.'),
                    ('Space', 'Space'),
                ]
            },
        ]
    },
    {
        'label': 'Job titles',
        'name': 'JobTitle',
        'rules': [
            {
                'label': 'Case',
                'name': 'Case',
                'choices': [
                    ('ProperCase', 'Convert to proper case'),
                    ('None', 'Do nothing'),
                    ('Uppercase', 'Convert to uppercase'),
                    ('Lowercase', 'Convert to lowercase'),
                ]
            },
            {
                'label': 'Periods',
                'name': 'Periods',
                'choices': [
                    ('Add', 'Add'),
                    ('None', 'Do nothing'),
                    ('Remove', 'Remove'),
                ]
            },
            {
                'label': 'Commas',
                'name': 'Commas',
                'choices': [
                    ('None', 'Do nothing'),
                    ('Remove', 'Remove'),
                ]
            },
            {
                'label': 'Department (word)',
                'name': 'DepartmentLiteral',
                'choices': [
                    ('Expand', 'Expand'),
                    ('None', 'Do nothing'),
                    ('Abbreviate', 'Abbreviate'),
                ]
            },
            {
                'label': 'Department names',
                'name': 'DepartmentNames',
                'choices': [
                    ('Expand', 'Expand'),
                    ('None', 'Do nothing'),
                    ('Abbreviate', 'Abbreviate'),
                ]
            },
            {
                'label': 'Department order',
                'name': 'Order',
                'choices': [
                    ('DepartmentLast', 'Department last'),
                    ('None', 'Do nothing'),
                    ('DepartmentFirst', 'Department first'),
                ]
            },
            {
                'label': 'CXO titles',
                'name': 'CXO',
                'choices': [
                    ('Abbreviate', 'Abbreviate'),
                    ('None', 'Do nothing'),
                    ('Expand', 'Expand'),
                ]
            },
            {
                'label': 'VP titles',
                'name': 'VP',
                'choices': [
                    ('Expand', 'Expand'),
                    ('None', 'Do nothing'),
                    ('Abbreviate', 'Abbreviate'),
                ]
            },
            {
                'label': 'Director titles',
                'name': 'Director',
                'choices': [
                    ('Expand', 'Expand'),
                    ('None', 'Do nothing'),
                    ('Abbreviate', 'Abbreviate'),
                ]
            },
            {
                'label': 'Manager titles',
                'name': 'Manager',
                'choices': [
                    ('Expand', 'Expand'),
                    ('None', 'Do nothing'),
                    ('Abbreviate', 'Abbreviate'),
                ]
            },
            {
                'label': 'Modifier prefixes',
                'name': 'ModifierPrefixes',
                'choices': [
                    ('Expand', 'Expand'),
                    ('None', 'Do nothing'),
                    ('Abbreviate', 'Abbreviate'),
                ]
            },
            {
                'label': 'Modifier suffixes',
                'name': 'ModifierSuffixes',
                'choices': [
                    ('None', 'Do nothing'),
                    ('Remove', 'Remove'),
                ]
            },
            {
                'label': 'Phrase: "of"',
                'name': 'OfUsage',
                'choices': [
                    ('ConvertToComma', 'Convert to comma'),
                    ('None', 'Do nothing'),
                    ('ConvertToHyphen', 'Convert to hyphen'),
                    ('Remove', 'Remove'),
                ]
            },
            {
                'label': 'Phrase: "and"',
                'name': 'AndUsage',
                'choices': [
                    ('ConvertToAnd', 'Convert to "and"'),
                    ('None', 'Do nothing'),
                    ('ConvertToAmpersand', 'Convert to "&"'),
                ]
            },
            {
                'label': 'Hyphens',
                'name': 'Hyphens',
                'choices': [
                    ('RemoveSpace', 'Remove surrounding space'),
                    ('None', 'Do nothing'),
                    ('PadWithSpace', 'Pad with space'),
                    ('Remove', 'Remove'),
                ]
            },
        ]
    },
]


def get_flattened_broadlook_rules():
    flattened = []

    for broadlook_field in BROADLOOK_NORMALIZER_FIELDS:
        field_dict = {
            'field_name': broadlook_field['name'],
            'field_label': broadlook_field['label'],
        }

        for rule_dict in broadlook_field['rules']:
            flattened_item = {
                'rule_name': rule_dict['name'],
                'rule_label': rule_dict['label'],
                'choices': rule_dict['choices']
            }
            flattened_item.update(field_dict)
            flattened.append(flattened_item)

    return flattened
