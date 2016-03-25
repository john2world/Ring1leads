from django.views.generic import FormView
from django.utils.functional import cached_property
from django.shortcuts import redirect
from django.http import Http404

from program_manager.models import Program

from . import utils
from . import forms


class MapFieldsView(FormView):
    form_class = forms.MapFieldsForm
    template_name = 'field_mapper/map_fields.html'

    def dispatch(self, *args, **kwargs):
        program = self.program

        if program.status != 'CREA':
            return redirect(program.get_absolute_url())

        all_fields, missing_fields = utils.validate_csv(program.csv_file.file,
                                                        program, ret=True)

        if not missing_fields:
            return redirect('/')

        self.missing_fields = missing_fields
        self.all_fields = all_fields

        return super(MapFieldsView, self).dispatch(*args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(MapFieldsView, self).get_form_kwargs()
        kwargs.update({
            'program': self.program,
            'all_fields': self.all_fields,
            'missing_fields': self.missing_fields,
        })

        return kwargs

    def form_valid(self, form):
        form.save()

        # rewind csv_file
        self.program.csv_file.seek(0)

        self.program.begin()

        return redirect(self.program.get_absolute_url())

    @cached_property
    def program(self):
        try:
            program = Program.objects.get(pk=self.kwargs.get('pk'))
        except Program.DoesNotExist:
            raise Http404

        return program
