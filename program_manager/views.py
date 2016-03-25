import os
import json
from api.serializers import ProgramSerializer
from integrations.salesforce.models import SalesforceSource
from integrations.salesforce.utils import InvalidSalesforceQueryCondition
import tasks
import choices

from django import forms
from django.db.models import Q
from django.db import transaction
from django.views.generic import View
from django.utils.functional import curry
from django.views.generic import ListView, DetailView, FormView, DeleteView
from django.template.response import TemplateResponse
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse, JsonResponse, HttpResponseForbidden, HttpResponseServerError
from django.views.decorators.csrf import csrf_exempt
from djcelery.models import PeriodicTask, CrontabSchedule

from accounts.views import LoginRequiredMixin
from utils import django_model_instance_to_dict

from program_manager.forms import FilterForm, DupMatchRuleForm, \
    SurvivingRecordRuleForm, SurvivingValueRuleForm, DedupeFormSet, \
    LocationOptimizationRuleForm, ContactsNormalizerRuleForm, \
    JunkRemovalSettingsForm, ProgramSettingsForm, FileSourceForm, \
    DefaultSurvivingRecordRuleForm, ProgramDataOriginForm, \
    ProgramScheduleForm, ProgramDataOriginForm

from program_manager.models import Program, FieldFilter, Job, SurvivingRecordRule


class ProgramListView(LoginRequiredMixin, ListView):
    model = Program
    template_name = 'program_manager/list.html'


class ProgramDashboardView(ProgramListView):
    template_name = 'program_manager/dash.html'


class ProgramDetailsView(LoginRequiredMixin, DetailView):
    model = Program
    context_object_name = 'program'
    template_name = 'program_manager/program_detail_view.html'

    def get_object(self, queryset=None):
        self.program = super(ProgramDetailsView, self).get_object(queryset)
        return self.program

    def get_context_data(self, **kwargs):
        context = super(ProgramDetailsView, self).get_context_data(**kwargs)
        context['form_data_origin'] = ProgramDataOriginForm(instance=self.program)
        context['form_program_schedule'] = ProgramScheduleForm(instance=self.program)
        return context


class ProgramAnalyseView(LoginRequiredMixin, View):
    def get(self, request, pk=None):
        if not request.is_ajax():
            return HttpResponseForbidden()

        program = get_object_or_404(Program, pk=pk, user=request.user)
        program.progress = 0
        program.save()

        program.begin(analyse_only=True)

        return JsonResponse(ProgramSerializer(program).data)


class ProgramOptimizeView(LoginRequiredMixin, View):
    def get(self, request, pk=None):
        if not request.is_ajax():
            return HttpResponseForbidden()

        program = get_object_or_404(Program, pk=pk, user=request.user)
        program.progress = 0
        program.save()

        program.begin(analyse_only=False)

        return JsonResponse(ProgramSerializer(program).data)


class ProgramPauseView(LoginRequiredMixin, View):
    def get(self, request, pk=None):
        if not request.is_ajax():
            return HttpResponseForbidden()

        program = get_object_or_404(Program, pk=pk, user=request.user)
        program.pause()

        return JsonResponse(ProgramSerializer(program).data)


class ProgramCancelView(LoginRequiredMixin, View):
    def get(self, request, pk=None):
        if not request.is_ajax():
            return HttpResponseForbidden()

        program = get_object_or_404(Program, pk=pk, user=request.user)
        program.cancel_current_job()
        program.status = 'CANCEL'
        program.save()

        return JsonResponse(ProgramSerializer(program).data)


class ProgramArchiveView(LoginRequiredMixin, View):
    def get(self, request, pk=None):
        if not request.is_ajax():
            return HttpResponseForbidden()

        program = get_object_or_404(Program, pk=pk, user=request.user)
        program.status = 'ARCH'
        program.save()

        return JsonResponse(ProgramSerializer(program).data)


class ProgramReactivateView(LoginRequiredMixin, View):
    def get(self, request, pk=None):
        if not request.is_ajax():
            return HttpResponseForbidden()

        program = get_object_or_404(Program, pk=pk, user=request.user, status='ARCH')

        if program.progress == 100:
            program.status = 'COMPL'
        elif program.progress == 0:
            program.status = 'CREA'
            print 0
        else:
            program.status = 'CANCEL'

        program.save()

        return JsonResponse(ProgramSerializer(program).data)


class ProgramSetNameView(LoginRequiredMixin, View):
    def get(self, request, pk=None):
        if not request.is_ajax():
            return HttpResponseForbidden()

        program = get_object_or_404(Program, pk=pk, user=request.user)

        name = request.GET.get('name', None)
        if name:
            program.name = name
            program.save()

        return JsonResponse(ProgramSerializer(program).data)


class ProgramSelectType(LoginRequiredMixin, View):
    """
    Create a new program and select its type.
    """
    template_name = 'program_manager/select_program_type.html'

    def get(self, request, pk=None):
        program = get_object_or_404(Program, pk=pk, user=request.user)
        context = {'program': program}
        return TemplateResponse(request, self.template_name, context=context)


class DownloadDatabaseView(LoginRequiredMixin, View):

    def get(self, request):
        try:
            token = request.user.oauthtokens.all()[0]
            sf_source, created = SalesforceSource.objects.get_or_create(user=request.user, token=token)
        except IndexError:
            return HttpResponseForbidden()

        program = Program.objects.create(user=request.user, source=sf_source)
        job = program.start_job(tasks.download_schema, program.pk)

        return JsonResponse({'job_pk': job.pk, 'program_pk': program.pk})


class ProgramAddFiltersView(LoginRequiredMixin, FormView):
    """
    Allow the user to select a data source, table and add filters.
    """

    template_name = 'program_manager/batch_select.html'
    form_class = FilterForm

    def dispatch(self, request, *args, **kwargs):
        pk = request.GET.get('pk')
        self.program = get_object_or_404(Program, pk=pk, user=self.request.user)
        return super(ProgramAddFiltersView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        field_filter = form.save(commit=False)
        field_filter.program = self.program
        field_filter.save()
        return super(ProgramAddFiltersView, self).form_valid(form)

    def get_form_kwargs(self):
        kwargs = super(ProgramAddFiltersView, self).get_form_kwargs()
        kwargs['program'] = self.program
        return kwargs

    def get_context_data(self, **kwargs):
        type_table = self.program.source.get_table('Lead').get_field_types()
        unary_operators, _ = zip(*choices.UNARY_OPERATORS)
        kwargs['type_table'] = json.dumps(type_table)
        kwargs['unary_operators'] = json.dumps(unary_operators)
        kwargs['program'] = self.program
        kwargs['field_filters'] = self.program.get_field_filters()
        return super(ProgramAddFiltersView, self).get_context_data(**kwargs)

    def get_success_url(self):
        pk = self.request.GET.get('pk', '')
        return '{}?pk={}'.format(reverse('batch_select'), pk)


class ProgramSelectActionsView(LoginRequiredMixin, View):
    """
    Allow the user to select actions and dedupe rules.
    """
    template_name = 'program_manager/select_actions.html'

    def dispatch(self, request, *args, **kwargs):
        self.program = get_object_or_404(Program, pk=self.kwargs['pk'], user=self.request.user)

        unary_operators, _ = zip(*choices.UNARY_OPERATORS)
        ctx = {
            'program': self.program,
            'open_modal': False,
            'unary_operators': json.dumps(unary_operators)
        }
        self.dedupe_formset_form_classes = {
            'dupmatchrule': DupMatchRuleForm,
            'survivingrecordrule': SurvivingRecordRuleForm,
            'survivingvaluerule': SurvivingValueRuleForm
        }

        location_optimization_rule_form = LocationOptimizationRuleForm(
            self.program, data=request.POST or None,
            prefix='location_optimization_rule_form')
        contacts_normalizer_rule_form = ContactsNormalizerRuleForm(
            self.program, data=request.POST or None,
            prefix='contacts_normalizer_rules_form')
        junk_removal_settings_form = JunkRemovalSettingsForm(
            request.POST or None, instance=self.program.junk_removal_settings,
            prefix='junk_removal_settings_form')
        try:
            default_rule = self.program.survivingrecordrule_set.get(priority=DefaultSurvivingRecordRuleForm.priority)
        except SurvivingRecordRule.DoesNotExist:
            default_rule = None
        default_srr_form = DefaultSurvivingRecordRuleForm(
                self.program, data=request.POST or None, instance=default_rule,
                prefix='default_surviving_record_rule_form')

        type_table = self.program.source.get_table('Lead').get_field_types()
        ctx['type_table'] = json.dumps(type_table)
        ctx['location_optimization_rule_form'] = location_optimization_rule_form  # noqa
        ctx['contacts_normalizer_rule_form'] = contacts_normalizer_rule_form
        ctx['junk_removal_settings_form'] = junk_removal_settings_form
        ctx['default_surviving_record_rule_form'] = default_srr_form

        self.forms = [
            location_optimization_rule_form,
            contacts_normalizer_rule_form,
            junk_removal_settings_form,
            default_srr_form,
        ]

        # dedupe rules formsets
        for name, fclass in self.dedupe_formset_form_classes.viewitems():
            model = fclass.Meta.model
            formset_class = forms.modelformset_factory(
                model, form=fclass, formset=DedupeFormSet, extra=0,
                can_delete=True, can_order=True)
            formset_class.form = staticmethod(curry(fclass, program=self.program))
            queryset = model.objects.filter(program=self.program).exclude(priority=DefaultSurvivingRecordRuleForm.priority)
            formset = formset_class(data=request.POST or None,
                                    queryset=queryset, prefix=name)
            self.forms.append(formset)
            ctx['%s_formset' % name] = formset

        # program settings
        settings_form = ProgramSettingsForm(
            data=request.POST or None, instance=self.program,
            prefix='programsettings')

        self.forms.append(settings_form)
        ctx['settings_form'] = settings_form
        # self.context['open_modal'] = reduce(lambda a, b: a or b,
        # map(lambda f: f.errors, reduce(lambda a, b: a or b, self.forms)))
        ctx['open_modal'] = False
        ctx['picklist_table'] = json.dumps(
            self.program.source.get_table('Lead').get_picklist_table())

        self.context = ctx

        return super(ProgramSelectActionsView, self).dispatch(request, *args, **kwargs)

    def get(self, request, pk=None):
        return TemplateResponse(request, self.template_name,
                                context=self.context)

    def post(self, request, pk=None):
        for form in self.forms:
            if form.is_valid():
                if isinstance(form, forms.BaseFormSet):
                    # handle formsets separately
                    priority = 0
                    instances = form.save(commit=False)  # noqa
                    subforms = list(form)
                    subforms.sort(key=lambda f: f.cleaned_data['ORDER'])
                    for subform in subforms:
                        model = subform.instance
                        if (model not in form.deleted_objects and
                                not subform.cleaned_data.get('DELETE')):
                            model.priority = priority
                            model.save()
                            priority += 1
                    for model in form.deleted_objects:
                        model.delete()
                else:
                    # save modelforms directly
                    form.save()
                print form.prefix + ' is valid, saved'
            else:
                print 'INVALID %s ' % form.prefix
        if 'continue' in request.POST:
            return redirect('program_details', pk=self.program.pk)
        elif 'autorun' in request.POST:
            return redirect(reverse('program_details', kwargs={'pk':self.program.pk}) + '#run')
        else:
            return redirect('select_actions', pk=self.program.pk)


class DeleteFieldFilterView(DeleteView):
    model = FieldFilter

    def get(self, request, *args, **kwargs):
        raise Http404

    def get_queryset(self):
        user = self.request.user
        return super(DeleteFieldFilterView, self).get_queryset().filter(
            program__user=user)

    def get_success_url(self):
        pk = self.object.program.pk
        return '{}?pk={}'.format(reverse('batch_select'), pk)


class CreateListImportProgramView(LoginRequiredMixin, FormView):
    form_class = FileSourceForm
    template_name = 'program_manager/import_select.html'

    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        # Had to make this view csrf-exempt,
        # because of the forceIframeTransport
        return super(CreateListImportProgramView, self).dispatch(
            *args, **kwargs)

    def form_valid(self, form):
        file_source = form.save(commit=False)
        file_source.user = self.request.user
        file_source.save()

        list_program = Program.objects.create(name=os.path.basename(file_source.file.name), source=file_source,
                                              status='CREA', user=self.request.user)

        # try:
        #     # run validation
        #     fm_utils.validate_csv(file_source.file, list_program)
        # except fm_exceptions.MissingFields:
        #     return JsonResponse({
        #         'program_pk': list_program.pk,
        #         'redirect_url': reverse('field_mapper:map_fields', args=[list_program.pk])
        #     })

        # run program
        # list_program.begin()

        return JsonResponse({
            'program_pk': list_program.pk,
            'redirect_url': reverse('program_details', kwargs={'pk': list_program.id})
        })


class JobStatusView(LoginRequiredMixin, View):

    def get(self, request):
        pk = request.GET.get('pk')
        if not pk or not pk.isdigit():
            pk = None
        job = get_object_or_404(Job, program__user=request.user, pk=pk)
        job.update_from_task()
        return JsonResponse(django_model_instance_to_dict(job, depth=0))


class ListImportProgramView(LoginRequiredMixin, DetailView):
    template_name = 'program_manager/list_import_program.html'

    def get_queryset(self):
        return Program.objects.filter(user=self.request.user)


class ProgramActionView(LoginRequiredMixin, View):
    def get(self, request):
        self.request = request

        action = 'action_{}'.format(request.GET.get('action', ''))

        if hasattr(self, action):
            return getattr(self, action)()

        return self.ok_response()

    def ok_response(self):
        if not self.request.is_ajax():
            return self.redirect_response()
        return JsonResponse({'status': 'OK'})

    def error_response(self):
        if not self.request.is_ajax():
            return self.redirect_response()
        return JsonResponse({'status': 'ERR'})

    def redirect_response(self):
        return redirect('program_list')

    def action_cancel(self):
        pk = self.request.GET.get('pk')

        try:
            program = Program.objects.get(Q(pk=pk, user=self.request.user),
                                          Q(status='RUN') | Q(status='PEND'))
            program.cancel_current_job()
            program.status = 'CANCEL'
            program.save()
        except Program.DoesNotExist:
            return self.error_response()

        return self.ok_response()

    def action_retry(self):
        pk = self.request.GET.get('pk')

        try:
            program = Program.objects.get(
                Q(pk=pk, user=self.request.user),
                status__in=['ERROR', 'COMPL', 'CANCEL', 'PAUSE']
            )
            program.begin()
        except Program.DoesNotExist:
            return self.error_response()

        return self.ok_response()

    def action_archive(self):
        pk = self.request.GET.get('pk')

        try:
            program = Program.objects.get(pk=pk, user=self.request.user)
        except Program.DoesNotExist:
            return self.error_response()

        program.status = 'ARCH'
        program.save()

        return self.ok_response()


@login_required
def count_data(request, pk):
    if not request.is_ajax():
        return redirect('/')

    # params for data source
    program = get_object_or_404(Program, pk=pk, user=request.user)

    try:
        count = program.count_records
    except (Exception, InvalidSalesforceQueryCondition) as e:
        return HttpResponseServerError(json.dumps(e.message))

    return JsonResponse({'count': count})


@login_required
@transaction.atomic
def program_set_tags(request):
    try:
        pk = int(request.GET.get('pk', None))
    except (TypeError, ValueError):
        raise Http404
    tags = request.GET.get('tags', '')
    program = get_object_or_404(Program, pk=pk, user=request.user)
    program.tags = tags
    program.save()
    return HttpResponse()


@login_required
@transaction.atomic
def program_set_data_origin(request, pk):
    program = get_object_or_404(Program, pk=pk, user=request.user)
    form = ProgramDataOriginForm(request.GET, instance=program)
    try:
        form.save()
    except ValueError:
        return HttpResponseForbidden()
    return HttpResponse()


@login_required
@transaction.atomic
def program_set_data_origin(request, pk):
    program = get_object_or_404(Program, pk=pk, user=request.user)
    form = ProgramScheduleForm(request.GET, instance=program)
    try:
        form.save()
    except ValueError:
        print form.errors
        return HttpResponseForbidden(form.errors)
    # use the djcelery to register the program as a periodic task
    crontab = CrontabSchedule.objects.create(
            day_of_week=program.schedule_day,
            hour=program.schedule_hour.hour,
            minute=program.schedule_hour.minute)
    # FIXME FIXME FIXME: disable recurring on delete program or disabled toggle
    PeriodicTask.objects.create(
            task='program_manager.tasks.run_scheduled_program',
            name='Scheduled %s (pk %s)' % (program.name, program.pk),
            crontab=crontab,
            args=json.dumps([program.pk]))
    return HttpResponse()

