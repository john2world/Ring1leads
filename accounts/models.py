from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.core.validators import RegexValidator
from django.db import models


class CustomUserManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, mobile_number, password=None):
        """
        Creates and saves a User with the given email, first_name, last_name,
        mobile_number, and password.
        """
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email),
            first_name=first_name,
            last_name=last_name,
            # mobile_number=mobile_number,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, mobile_number, password):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        user = self.create_user(email, first_name=first_name, last_name=last_name, mobile_number=mobile_number,
                                password=password)
        user.is_admin = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class CustomUser(AbstractBaseUser):
    first_name = models.CharField(max_length=256, null=True, blank=True)
    last_name = models.CharField(max_length=256, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    email = models.EmailField(
        max_length=255,
        unique=True,
        error_messages={
            'required': 'Email is required.',
            'unique': 'This email has already been registered.'
            }
        )
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: \
            '+999999999'. Up to 15 digits allowed."
        )
    mobile_number = models.CharField(
        unique=True,
        validators=[phone_regex],
        null=True,
        blank=True,
        max_length=20,
        error_messages={
            'required': 'Mobile number is required.',
            'unique': 'This number has already been registered.'
            }
        )

    # is_first_login triggers introduction messages when a new user registers
    is_first_login = models.BooleanField(default=True)

    # Required definitions for custom user model
    objects = CustomUserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'mobile_number']

    def __unicode__(self):
        return self.email

    def get_full_name(self):
        # The user is identified by their email address
        return self.email

    def get_short_name(self):
        # The user is identified by their email address
        return self.email

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin


class Organization(models.Model):
    users = models.ManyToManyField(CustomUser)
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=200, null=True, blank=True)
    city = models.CharField(max_length=200, null=True, blank=True)
    state = models.CharField(max_length=10, null=True, blank=True)
    postal_code = models.CharField(max_length=10, null=True, blank=True)
    country = models.CharField(max_length=10, null=True, blank=True)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: \
            '+999999999'. Up to 15 digits allowed."
        )
    website = models.URLField(null=True, blank=True)
    phone = models.CharField(
        validators=[phone_regex], null=True, blank=True, max_length=20
        )

    def __unicode__(self):
        return self.name
