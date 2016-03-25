import os
from kickbox.error.client_error import ClientError
import requests
import json
import kickbox

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email as django_email_validator
import sys
import rollbar
from operations.exceptions import InsufficientCreditsError
from operations.notifications import (
    EmailAdminsNotificationSender,
    KickboxAPIInsuffinetBalanceNotification
    )


class MailgunEmailValidator(object):
    API_URL = 'https://api.mailgun.net/v3/address/validate'

    def __call__(self, value):
        response = requests.get(
            self.API_URL,
            auth=("api", settings.MAILGUN_PUBLIC_KEY),
            params={"address": value}
        )
        resp_data = json.loads(response.text)
        if resp_data.get('is_valid'):
            return True
        else:
            raise ValidationError('Mailgun: Invalid email')

mailgun_email_validator = MailgunEmailValidator()


class FullContactEmailValidator(object):
    API_URL = 'https://api.fullcontact.com/v2/person.json'

    def __call__(self, value):

        params = {
            'apiKey': settings.FULLCONTACT_API_KEY,
            'email': value
        }
        response = requests.get(self.API_URL, params=params)
        resp_data = json.loads(response.text)
        if resp_data.get('status') == 404:
            raise ValidationError(resp_data.get('message'))
        return True

fullcontact_email_validator = FullContactEmailValidator()


class KickboxEmailValidator(object):

    def __call__(self, value):
        client = kickbox.Client(settings.KICKBOX_API_KEY)
        kickbox_client = client.kickbox()

        try:
            response = kickbox_client.verify(value)
        except ClientError as e:
            if e.code == 403 and e.message == 'Insufficient balance':
                rollbar.report_exc_info(sys.exc_info(), extra_data={'API': 'Kickbox', 'message': e.message})
                # send notification
                notification = KickboxAPIInsuffinetBalanceNotification()
                EmailAdminsNotificationSender(notification=notification).notify()
                # and raise ValidationError to mark data as not valid
                raise InsufficientCreditsError('Kickbox: insufficient balance')
            raise ValidationError('Kickbox: %s' % e.message)
        except Exception as e:
            raise ValidationError('Kickbox: %s' % e.message)
        else:
            if response.body['result'] in ('risky', 'undeliverable'):
                raise ValidationError('Kickbox: email risky or undeliverable')
            elif response.body['role']:
                raise ValidationError('Kickbox: email is a role email')
            elif response.body['free']:
                raise ValidationError('Kickbox: email address uses free email service')
            elif response.body['disposable']:
                raise ValidationError('Kickbox: email address uses a disposable domain')
            elif response.body['result'] == 'unknown':
                reason = response.body['reason']
                if reason == 'no_connect':
                    raise ValidationError('Kickbox: unable to connect to the SMTP server')
                else:
                    raise ValidationError('Kickbox: declined for reason "%s"' % reason)

        return True

kickbox_email_validator = KickboxEmailValidator()


class SpamDomainEmailValidator(object):

    def __init__(self):
        self.spam_domains = []

    def _read_spam_domain(self):
        file_path = os.path.join(
            settings.BASE_DIR, 'rl_proto2/custom_libs/spam_domains.txt'
            )
        try:
            f = open(file_path)
        except Exception as e:
            return []
        else:
            return f.read().split('\n')
        finally:
            f.close()

    def __call__(self, value):
        domain = value.split('@')[-1]
        if not self.spam_domains:
            self.spam_domains = self._read_spam_domain()
        if not domain or domain in self.spam_domains:
            raise ValidationError('Invalid domain')

        return True

spam_domain_email_validator = SpamDomainEmailValidator()


class BadWordStringValidator(object):
    EXTRA_BADWORDS = [
        'fake', 'test'
    ]

    def __init__(self):
        self.badwords = []

    def _read_badwords(self):
        file_path = os.path.join(
            settings.BASE_DIR, 'rl_proto2/custom_libs/badwords.txt'
            )
        try:
            f = open(file_path)
        except Exception as e:
            print('BadWordValidator._read_bad_words():', e)
            return []
        else:
            return f.read().split('\n')
        finally:
            f.close()

    def __call__(self, value):
        if not self.badwords:
            self.badwords = self._read_badwords()
            self.badwords.extend(self.EXTRA_BADWORDS)

        value_to_check = value.lower().strip()
        for word in value_to_check.split():
            if word in self.badwords:
                raise ValidationError('Data contains bad words')

        return True

badword_string_validator = BadWordStringValidator()


class BadWordDictValidator(object):
    """
    Validates all 'string' values of passed dict object with
    BadWordStringValidator
    """
    def __init__(self):
        self.validator = BadWordStringValidator()

    def __call__(self, di):
        for key, value in di.iteritems():
            if isinstance(value, basestring):
                self.validator(value)
        return True


badword_dict_validator = BadWordDictValidator()


class BlacklistEmailValidator(object):
    def __init__(self):
        self.blacklist = []

    def _read_blacklist(self):
        file_path = os.path.join(
            settings.BASE_DIR, 'rl_proto2/custom_libs/blacklist.txt'
            )
        try:
            f = open(file_path)
        except Exception as e:
            return []
        else:
            return f.read().split('\n')
        finally:
            f.close()

    def __call__(self, value):
        if not self.blacklist:
            self.blacklist = self._read_blacklist()

        if value in self.blacklist:
            raise ValidationError('%s email is blacklisted' % value)

        return True


blacklist_email_validator = BlacklistEmailValidator()


# Chained validators #

class BaseChainedValidator(object):
    validators = []

    def __init__(self, data=None):
        self.is_dirty = False  # not validated yet
        self._data = data
        self._is_valid = None
        self._errors = []

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        self._data = value
        self.is_dirty = False

    @property
    def errors(self):
        return self._errors

    def validate(self):
        """
        Custom validation logic goes here.
        Return True if data is valid, otherwise False
        If custom validation is not required just return True.
        """
        return True

    def run_validators(self):
        for validator in self.validators:
            try:
                validator(self.data)
            except ValidationError as e:
                self.errors.append(unicode(e.message))
                # prevent further validation
                break
            except InsufficientCreditsError:  # process other validators if this one has insufficient credits
                continue
        return False if self.errors else True

    def clean(self):
        if self.run_validators() and self.validate():
            self._is_valid = True
        else:
            self._is_valid = False
        self.is_dirty = True

    def is_valid(self):
        if not self.is_dirty:
            self.clean()
        return self._is_valid


class DjangoEmailChainedValidator(BaseChainedValidator):
    """
    Validates email using Django email validator
    """
    validators = [django_email_validator]


class MailgunEmailChainedValidator(BaseChainedValidator):
    """
    Validates email using Django email validator and Mailgun email validator
    """
    validators = [django_email_validator, mailgun_email_validator]


class FullContactChainedValidator(BaseChainedValidator):
    """
    Validates email using Django email validator, then Mailgun email validator
    and then check email in FullContact API
    """
    validators = [
        django_email_validator,
        mailgun_email_validator,
        fullcontact_email_validator
        ]


class SpamDomainEmailChainedValidator(BaseChainedValidator):
    validators = [
        django_email_validator,
        spam_domain_email_validator,
        blacklist_email_validator
        ]


class KickboxChainedValidator(BaseChainedValidator):
    validators = [
        django_email_validator,
        spam_domain_email_validator,
        # kickbox_email_validator
        ]


class SpamContentDictChainedValidator(BaseChainedValidator):
    """
    'data' param should be a dict or a pandas.Series instance
    """
    validators = [badword_dict_validator]
