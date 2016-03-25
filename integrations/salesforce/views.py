import json
from django.shortcuts import redirect

import requests
import rollbar
from django.views.generic import RedirectView, View
from django.contrib import messages
from django.core.urlresolvers import reverse_lazy

from accounts.views import LoginRequiredMixin
from integrations.salesforce import settings
from integrations.salesforce.auth import get_salesforce_user_info
from integrations.salesforce.models import OauthToken, SalesforceSource
from program_manager.models import Program


class SalesforceOauthRedirectView(LoginRequiredMixin, RedirectView):
    query_string = False

    def get_redirect_url(self):
        is_sandbox = False
        requesting_user = self.request.user

        try:
            ret_state = str(self.request.GET.get('state'))
            if ret_state == "is_sandbox":
                is_sandbox = True
            else:
                pass
        except:
            pass

        try:
            sfdc_code = str(self.request.GET.get('code'))
            print 'sandbox mode: %s' % is_sandbox

            if is_sandbox == True:
                oauth_token_url = "https://test.salesforce.com/services/oauth2/token"
            else:
                oauth_token_url = "https://login.salesforce.com/services/oauth2/token"
            # construct payload template
            payload = {
                'grant_type': 'authorization_code',
                'client_id': settings.CONSUMER_KEY,
                'client_secret': settings.CONSUMER_SECRET,
                'code': sfdc_code,
                'redirect_uri': settings.REDIRECT_URI
            }
            try:
                # Post payload to Salesforce Oauth server and get user
                # token in response.
                r = requests.post(
                    oauth_token_url,
                    headers={
                        "Content-Type":"application/x-www-form-urlencoded"
                    },
                    data=payload
                )
                # Decode the JSON response from Salesforce Oauth server
                decoded = json.loads(r.content)
                print decoded

                # Store tokens & Salesforce user info to database
                try:
                    creds = OauthToken.objects.get(user=requesting_user)
                except OauthToken.DoesNotExist:
                    creds = OauthToken()
                    creds.user = requesting_user
                try:
                    creds.access_token = decoded['access_token']
                    creds.id_url = decoded['id']
                    creds.refresh_token = decoded['refresh_token']
                    # creds.id_token = decoded['id_token']
                    creds.instance_url = decoded['instance_url']

                    try:
                        # Get Salesforce user info
                        user_info = get_salesforce_user_info(
                            # 'id' is a URL like https:login.salesforce.com/id/{org_id}/{user_id}
                            id_url=decoded['id'],
                            access_token=decoded['access_token']
                            )
                        creds.salesforce_user_id = user_info['user_id']
                        creds.salesforce_organization_id = user_info['organization_id']
                    except:
                        rollbar.report_exc_info()
                        pass
                    # mark OauthToken as active and save to database
                    creds.active = True

                    if is_sandbox is True:
                        creds.is_sandbox = True
                    else:
                        creds.is_sandbox = False

                    creds.save()

                    messages.add_message(
                        self.request,
                        messages.SUCCESS,
                        ('Successfully connected your Salesforce account')
                    )

                except BaseException as e:
                    # raise e
                    rollbar.report_exc_info()
                    messages.add_message(
                    self.request,
                    messages.WARNING,
                        ('Error connecting with Salesforce.  \
                          Our support team has been notified and \
                          will contact you shortly to help resolve \
                          this issue.  Hold tight! ')
                    )
                    # return reverse_lazy('providers:provider_list')
                    pass

                except KeyError as e:
                    rollbar.report_exc_info()
                    #logger.error("%s: %s" % (e.__class__, e.args))
                    messages.add_message(
                    self.request,
                    messages.WARNING,
                        ('Error retrieving your Salesforce access token. \
                          Our support team has been notified and \
                          will contact you shortly to help resolve \
                          this issue.  Hold tight! ')
                    )
                    # return reverse_lazy('providers:provider_list')
                    pass

            except BaseException as e:
                rollbar.report_exc_info()
                # raise e # Print error to the console
                # or, to print to the error logs
                # logger.error("%s: %s" % (e.__class__, e.args))
                messages.add_message(
                    self.request,
                    messages.WARNING,
                        ('Could not obtain Oauth_token from Salesforce API. \
                        Salesforce may unavailable.  Try again in a few \
                        minutes and contact support if the problem persists.'
                        )
                )
                # return reverse_lazy('providers:provider_list')
                pass

        except BaseException as e:
            # Print error to console
            rollbar.report_exc_info()
            # logger.error("%s: %s" % (e.__class__, e.args))
            messages.add_message(
                self.request,
                messages.WARNING,
                ('There was a problem authenticating with \
                 Salesforce.  Be sure to enter your Salesforce \
                 username and password before attempting to authorize your\
                 account.  Contact our support team if you need some help. \
                 [Error 003]'
                )
            )
            pass

        return reverse_lazy('accounts:connections')


class DeleteSalesforceConnectionView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        try:
            sf_source = SalesforceSource.objects.get(user=request.user)
        except SalesforceSource.DoesNotExist:
            pass
        else:
            program_qs = Program.objects.filter(source__user=request.user, source=sf_source)
            for program in program_qs.filter(status__in=['RUN', 'PEND']):
                program.cancel_current_job()
            program_qs.delete()

            sf_source.delete_tables()
            sf_source.delete()

        OauthToken.objects.filter(user=request.user).delete()

        return redirect('accounts:connections')
