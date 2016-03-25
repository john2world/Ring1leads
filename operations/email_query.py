from operations.email_validators import (
    KickboxChainedValidator,
    SpamContentDictChainedValidator,
    SpamDomainEmailChainedValidator
)


def get_is_email_valid(email, whitelist=None):
    email_whitelist = whitelist or []

    if email in email_whitelist:
        return True

    return KickboxChainedValidator(data=email).is_valid()


def get_is_spam_record(df_record, email):
    """
    record can be dict or pandas.Series instance
    """
    is_spam = False
    email_is_spam = False
    content_is_spam = False
    spam_score = 0
    message = ''

    if isinstance(email, basestring):
        spam_email_validator = SpamDomainEmailChainedValidator(email)
        if not spam_email_validator.is_valid():
            is_spam = True
            email_is_spam = True
            spam_score += 60
            message += ', '.join(spam_email_validator.errors)

    spam_content_validator = SpamContentDictChainedValidator(df_record)
    if not spam_content_validator.is_valid():
        is_spam = True
        content_is_spam = True
        spam_score += 40
        message += ', '.join(spam_content_validator.errors)

    if not message:
        message = 'Valid'

    return {
        'spam': is_spam,
        'email_is_spam': email_is_spam,
        'content_is_spam': content_is_spam,
        'spam_score': spam_score,
        'message': message
    }
