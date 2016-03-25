from django import forms

from .models import MappedField


class MapFieldsForm(forms.Form):
    def __init__(self, program, all_fields, missing_fields, *args, **kwargs):
        super(MapFieldsForm, self).__init__(*args, **kwargs)

        choices = [('', '(leave it blank)')]
        choices.extend(zip(all_fields, all_fields))

        for mfield in missing_fields:
            self.fields[mfield] = forms.ChoiceField(choices=choices,
                                                    required=False)

        self.program = program

    def save(self):
        program = self.program
        bulk = []

        for to_field, from_field in self.cleaned_data.items():
            if not from_field:
                continue  # leave it blank

            bulk.append(MappedField(
                program=program, from_field=from_field, to_field=to_field))

        MappedField.objects.bulk_create(bulk)
