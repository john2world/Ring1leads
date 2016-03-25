from collections import OrderedDict
import pytz
from django import forms
from django.db.models import Q
from django.utils.html import format_html
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from dateutil.parser import parse as dateutil_parse
from django.utils.translation import ugettext_lazy as _
from integrations.models import FileSource
from datetime import datetime
from time import mktime
import parsedatetime
from integrations.salesforce.utils import SalesforceQueryBuilder, InvalidSalesforceQueryCondition

from program_manager import choices
from program_manager.choices import UPDATE_POLICY_CHOICES, get_flattened_broadlook_rules
from program_manager.models import (FieldFilter, DupMatchRule, SurvivingRecordRule, SurvivingValueRule,
                                    LocationOptimizationRule, ContactsNormalizerRule, JunkRemovalSettings, Program)


num_operators = choices.NUM_OPERATORS + choices.SV_NUMBER_OPERATORS + choices.SR_NUMBER_OPTIONS
datetime_operators = choices.DATETIME_OPERATORS + choices.SV_AGE_OPERATORS + choices.SR_AGE_OPTIONS
text_operators = choices.TEXT_OPERATORS + choices.SV_TEXT_OPERATORS + choices.MATCH_OPERATORS
operator_map = {
    'string': text_operators,
    'textarea': text_operators,
    'boolean': choices.BOOL_OPERATORS,
    'int': num_operators,
    'double': num_operators,
    'date': datetime_operators,
    'datetime': datetime_operators,
    'binary': text_operators,
    'id': choices.TEXT_OPERATORS[:2],
    'reference': choices.TEXT_OPERATORS[:2],
    'currency': num_operators,
    'percent': num_operators,
    'phone': text_operators,
    'url': text_operators,
    'email': text_operators,
    'picklist': text_operators + choices.PICKLIST_OPERATORS,
    'multipicklist': text_operators + choices.PICKLIST_OPERATORS,
    'location': text_operators,
    'anyType': text_operators + num_operators + datetime_operators + choices.BOOL_OPERATORS
}

for key, value in operator_map.viewitems():
    # generic operators
    operator_map[key] = value + choices.SV_AGE_OPERATORS + choices.SR_AGE_OPTIONS

cal = parsedatetime.Calendar()
def natural_date_parse(string):
    try:
        date = dateutil_parse(string)
    except ValueError:
        time_struct, status = cal.parse(string)
        if not status:
            raise ValueError('Unable to parse date string.')
        date = datetime.fromtimestamp(mktime(time_struct))
    if not date.tzinfo:
        date = pytz.utc.localize(date)
    return date.isoformat()


class OperatorSelect(forms.Select):
    def __init__(self, *args, **kwargs):
        attrs = kwargs.get('attrs', {})
        if not 'class' in attrs:
            attrs['class'] = ''
        attrs['class'] += ' operator-select'
        kwargs['attrs'] = attrs
        super(OperatorSelect, self).__init__(*args, **kwargs)

    def render_option(self, selected_choices, option_value, option_label):
        if option_value is None:
            option_value = ''
        option_value = force_text(option_value)
        if option_value in selected_choices:
            selected_html = mark_safe(' selected="selected"')
            if not self.allow_multiple_selected:
                selected_choices.remove(option_value)
        else:
            selected_html = ''
        # generate list of css classes from the operator map
        css_classes = set()
        for field_type, operators in operator_map.viewitems():
            for op, __ in operators:
                if op == option_value:
                    css_classes.add('opfilter_' + field_type)
        return format_html('<option value="{}" class="{}" {}>{}</option>',
                           option_value,
                           ' '.join(css_classes),
                           selected_html,
                           force_text(option_label))


class FilterForm(forms.ModelForm):
    def __init__(self, program, *args, **kwargs):
        super(FilterForm, self).__init__(*args, **kwargs)
        for key, field in self.fields.viewitems():
            if not 'class' in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'
            else:
                field.widget.attrs['class'] += ' form-control'
        queryset = program.source.get_table('Lead').fields.all()
        self.fields['field'].queryset = queryset
        # remove empty option
        self.fields['field'].empty_label = None
        self.fields['field'].widget.choices = self.fields['field'].choices

    def clean(self):
        cleaned_data = super(FilterForm, self).clean()

        field = cleaned_data.get('field')
        operator = cleaned_data.get('operator')
        field_value = cleaned_data.get('field_value')

        try:
            SalesforceQueryBuilder.validate_field_filter(field, operator, field_value)
        except InvalidSalesforceQueryCondition as e:
            self.add_error('field_value', forms.ValidationError(_(e.message), code='invalid'))

        date_ops, date_ops_names = zip(*choices.DATETIME_OPERATORS)
        if operator in date_ops:
            self.cleaned_data['field_value'] = natural_date_parse(field_value)

        return cleaned_data

    class Meta:
        model = FieldFilter
        fields = ['field', 'operator', 'field_value']
        widgets = {
            'operator': OperatorSelect,
            'field': forms.Select(attrs={'class': 'field-select'}),
        }


class DedupeFormSet(forms.BaseModelFormSet):
    pass


class DedupeRuleForm(forms.ModelForm):
    def __init__(self, program, *args, **kwargs):
        super(DedupeRuleForm, self).__init__(*args, **kwargs)
        self.program = program
        for key, field in self.fields.viewitems():
            current_class = field.widget.attrs.get('class', '')
            new_class = (current_class + ' form-control form-wide').strip()
            if key == 'field':
                new_class += ' selectpicker'
                field.widget.attrs['data-live-search'] = 'true'
            field.widget.attrs['class'] = new_class
        queryset = self.program.source.get_table('Lead').fields.all()
        self.fields['field'].queryset = queryset
        # remove empty option
        self.fields['field'].empty_label = None
        self.fields['field'].widget.choices = self.fields['field'].choices

    def get_set(self):
        return self.Meta.model.objects.filter(program=self.program)

    def clean(self):
        cleaned_data = super(DedupeRuleForm, self).clean()
        if 'value' in cleaned_data and cleaned_data['rule'] in zip(*choices.DATETIME_OPERATORS)[0]:
            cleaned_data['value'] = natural_date_parse(cleaned_data['value'])
            self.add_error('value', forms.ValidationError(_('This operator requires a datetime value.'), code='invalid'))
        return cleaned_data

    def save(self, commit=True):
        instance = super(DedupeRuleForm, self).save(commit=False)
        instance.program = self.program
        if commit:
            instance.save()
        return instance


class DupMatchRuleForm(DedupeRuleForm):
    class Meta:
        model = DupMatchRule
        fields = ['field', 'rule']
        labels = {'field': '', 'rule': ''}


class SurvivingRecordRuleForm(DedupeRuleForm):
    class Meta:
        model = SurvivingRecordRule
        fields = ['field', 'rule', 'value']
        labels = {'field': '', 'rule': '', 'value': ''}
        widgets = {
            'value': forms.TextInput(attrs={'class': 'rule-value'}),
            'rule': OperatorSelect(attrs={'class': 'rule-operator'}),
            'field': forms.Select(attrs={'class': 'field-select'}),
        }

class DefaultSurvivingRecordRuleForm(DedupeRuleForm):
    priority = 1000

    def __init__(self, *args, **kwargs):
        super(DefaultSurvivingRecordRuleForm, self).__init__(*args, **kwargs);
        self.fields['field'].queryset = self.fields['field'].queryset.filter(Q(salesforcefield__name='LastModifiedDate') | Q(salesforcefield__name='CreatedDate'))
        self.fields['rule'].choices = choices.SR_AGE_OPTIONS

    def save(self, commit=True):
        item = super(DefaultSurvivingRecordRuleForm, self).save(commit=False)
        item.priority = DefaultSurvivingRecordRuleForm.priority
        if commit:
            item.save()
        return item

    class Meta:
        model = SurvivingRecordRule
        fields = ['field', 'rule', 'value']
        labels = {'field': '', 'rule': '', 'value': ''}
        widgets = {
            'field': forms.Select(attrs={'class': 'defaultsrr-field'}),
            'rule': forms.Select(attrs={'class': ''}),
            'value': forms.TextInput(attrs={'class': 'hidden'}),
        }


class SurvivingValueRuleForm(DedupeRuleForm):
    picklist_priorities = forms.CharField(widget=forms.Select(attrs={'class': 'picklist-priorities selectpicker'}), label='', required=False)

    class Meta:
        model = SurvivingValueRule
        fields = ['field', 'rule', 'value']
        labels = {'field': '', 'rule': '', 'value': '', 'picklist_priorities': ''}
        widgets = {
            'value': forms.TextInput(attrs={'class': 'rule-value'}),
            'rule': OperatorSelect(attrs={'class': 'rule-operator'}),
            'field': forms.Select(attrs={'class': 'field-select'})
        }

    def clean(self):
        cleaned_data = super(SurvivingValueRuleForm, self).clean()
        return cleaned_data


class LocationOptimizationRuleForm(forms.Form):
    def __init__(self, program, *args, **kwargs):
        super(LocationOptimizationRuleForm, self).__init__(*args, **kwargs)
        self.program = program

        # <- mapping step will be added after FieldMapper is ready
        mapped_field_names = ['Street', 'City', 'State', 'PostalCode', 'Country']
        field_qs = self.program.source.get_table('Lead').fields.filter(salesforcefield__name__in=mapped_field_names)
        self.mapped_fields = list(field_qs)

        for field in self.mapped_fields:
            self.fields[field.name] = forms.ChoiceField(choices=UPDATE_POLICY_CHOICES, label=field.label,
                                                        widget=forms.Select(attrs={'class': 'form-control'}))

    def save(self):
        if not self.is_valid():
            return

        LocationOptimizationRule.objects.filter(program=self.program).delete()

        new_rules = []
        for mapped_field in self.mapped_fields:
            new_rule = LocationOptimizationRule(priority=1, field=mapped_field,
                                                rule=self.cleaned_data[mapped_field.name], program=self.program)
            new_rules.append(new_rule)

        LocationOptimizationRule.objects.bulk_create(new_rules)


class ContactsNormalizerRuleForm(forms.Form):
    TEMP_MAPPING = {  # TODO: this mapping is TEMP, it works only for SF's Lead table, we need a mapping solution
        'Company': 'CompanyName',
        'City': 'City',
        'Street': 'StreetLine',
        'State': 'StateProvince',
        'Phone': 'USPhone',
        'Website': 'URL',
        'Title': 'JobTitle'
    }

    def __init__(self, program, *args, **kwargs):
        super(ContactsNormalizerRuleForm, self).__init__(*args, **kwargs)
        self.program = program

        field_qs = self.program.source.get_table('Lead').fields.filter(salesforcefield__name__in=self.TEMP_MAPPING.keys())
        self.schema_fields = list(field_qs)

        field_ordering = []
        for rule_dict in get_flattened_broadlook_rules():
            form_field_label = '{0}: {1}'.format(rule_dict['field_label'], rule_dict['rule_label'])
            form_field_name = '{0}.{1}'.format(rule_dict['field_name'], rule_dict['rule_name'])

            field_ordering.append(form_field_name)

            self.fields[form_field_name] = forms.ChoiceField(choices=rule_dict['choices'], label=form_field_label,
                                                             widget=forms.Select(attrs={'class': 'form-control'}))

        self.fields = OrderedDict(
            (k, self.fields[k])
            for k in field_ordering
        )

    def save(self):
        if not self.is_valid():
            return

        ContactsNormalizerRule.objects.filter(program=self.program).delete()

        new_rules = []
        for rule_dict in get_flattened_broadlook_rules():
            rule_name = rule_dict['rule_name']
            field_name = rule_dict['field_name']

            for schema_field in self.schema_fields:
                if self.TEMP_MAPPING.get(schema_field.get_name()) == field_name:
                    form_field_name = '{0}.{1}'.format(rule_dict['field_name'], rule_dict['rule_name'])
                    new_rule = ContactsNormalizerRule(priority=1, field=schema_field, broadlook_field_name=field_name,
                                                      broadlook_rule_name=rule_name, program=self.program,
                                                      rule=self.cleaned_data[form_field_name])
                    new_rules.append(new_rule)
                    break

        ContactsNormalizerRule.objects.bulk_create(new_rules)


class ProgramSettingsForm(forms.ModelForm):
    class Meta:
        model = Program
        fields = ['dedupe', 'location_optimization', 'contacts_normalization', 'junk_removal']
        labels = {
            'dedupe': 'Dedupe',
            'location_optimization': '',
            'contacts_normalization': '',
            'junk_removal': ''
        }


class ProgramNameForm(forms.ModelForm):
    run_now = forms.BooleanField(initial=True, label='Run after saving', required=False)

    class Meta:
        model = Program
        fields = ['name']
        labels = {'name': 'Program name'}

    def save(self, commit=True):
        program = super(ProgramNameForm, self).save(commit=False)
        run_now_value = self.cleaned_data.get('run_now')
        program.status = 'RUN' if self.cleaned_data.get('run_now') else 'PAUSE'
        program.save()

        if run_now_value:
            program.begin()

        return program


class ProgramTagsForm(forms.ModelForm):
    class Meta:
        model = Program
        fields = ['tags']
        labels = {'tags': ''}


class FileSourceForm(forms.ModelForm):
    class Meta:
        model = FileSource
        fields = ('file',)


class JunkRemovalSettingsForm(forms.ModelForm):
    class Meta:
        model = JunkRemovalSettings
        fields = ('delete_spam_records',)


class ProgramDataOriginForm(forms.ModelForm):
    class Meta:
        model = Program
        fields = ['data_origin']
        labels = {'data_origin': ''}
        widgets = {
            'data_origin': forms.Select(attrs={'class': 'data-origin-select'})
        }

class ProgramScheduleForm(forms.ModelForm):
    schedule_hour = forms.TimeField(input_formats=(('%I:%M%p'),))
    class Meta:
        model = Program
        fields = ['schedule_day', 'schedule_hour', 'schedule_enabled']
        labels = {'schedule_day': '', 'schedule_hour': '', 'schedule_enabled': ''}
