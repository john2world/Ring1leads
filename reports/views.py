from django.views.generic.list import ListView
from django.views.generic import DetailView
from django.shortcuts import get_object_or_404

from accounts.views import LoginRequiredMixin

from program_manager.models import Program


class ReportListView(LoginRequiredMixin, ListView):
    model = Program
    context_object_name = 'programs'
    template_name = 'reports/list.html'

    def get_queryset(self, **kwargs):
        return Program.objects.for_user(self.request.user).with_reports()


class QualityScoreOverTimeView(LoginRequiredMixin, DetailView):
    model = Program
    context_object_name = 'program'
    template_name = 'reports/qot.html'

    def get_context_data(self, **kwargs):
        ctx = super(QualityScoreOverTimeView, self).get_context_data(**kwargs)
        ctx['report'] = self.object.qualityscorereport
        return ctx


class QualityScoreSnapshot(LoginRequiredMixin, DetailView):
    """ See a program quality score. If the `qscore` parameter is passed
        we use it. Otherwise we get the latest/current quality score.
    """
    context_object_name = 'program'
    template_name = 'reports/snapshot.html'

    def get_object(self):
        return get_object_or_404(
            Program, user=self.request.user, pk=self.request.GET.get('pk'))

    def get_context_data(self, **kwargs):
        ctx = super(QualityScoreSnapshot, self).get_context_data(**kwargs)
        ctx['qscore'] = self.get_qscore()

        return ctx

    def get_qscore(self):
        qscore = self.request.GET.get('qscore')
        if qscore and qscore.isdigit():
            return get_object_or_404(self.object.qualityscore_set, pk=qscore)
        return self.object.get_current_quality_score()
