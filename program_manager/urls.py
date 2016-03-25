from django.conf.urls import url
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required

from program_manager import views


urlpatterns = [
    url(r'^$', views.ProgramListView.as_view(), name='program_list'),
    url(r'^dash/$', views.ProgramDashboardView.as_view(), name='program_dash'),
    url(r'^select_program_type/(?P<pk>[0-9]+)$', views.ProgramSelectType.as_view(), name='select_program_type_pk'),  # TODO: remove
    url(r'^analysis_select/$', login_required(TemplateView.as_view(template_name='program_manager/analysis_select.html')), name='analysis_select'),
    url(r'^analysis_confirm/$', login_required(TemplateView.as_view(template_name='program_manager/analysis_confirm.html')), name='analysis_confirm'),
    url(r'^batch_select/$', views.ProgramAddFiltersView.as_view(), name='batch_select'),
    url(r'^select_actions/(?P<pk>[0-9]+)$', views.ProgramSelectActionsView.as_view(), name='select_actions'),
    url(r'^fieldfilter/(?P<pk>[0-9]+)/delete', views.DeleteFieldFilterView.as_view(), name='delete_fieldfilter'),
    url(r'^import_select/$', views.CreateListImportProgramView.as_view(), name='import_select'),
    url(r'^import_program/(?P<pk>[0-9]+)/$', views.ListImportProgramView.as_view(), name='import_program_details'),
    url(r'^count_data/(?P<pk>[0-9]+)/$', views.count_data, name='count_data'),
    url(r'^download_database/$', views.DownloadDatabaseView.as_view(), name='download_database'),
    url(r'^job_status$', views.JobStatusView.as_view(), name='job_status'),
    url(r'^program_action/$', views.ProgramActionView.as_view(), name='program_action'),
    url(r'^program_set_tags/', views.program_set_tags, name='program_set_tags'),

    url(r'^program/details/(?P<pk>[-\w]+)/$', views.ProgramDetailsView.as_view(), name='program_details'),
    url(r'^program/(?P<pk>[0-9]+)/analyse/$', views.ProgramAnalyseView.as_view(), name='analyse_program'),
    url(r'^program/(?P<pk>[0-9]+)/optimize/$', views.ProgramOptimizeView.as_view(), name='optimize_program'),
    url(r'^program/(?P<pk>[0-9]+)/pause/$', views.ProgramPauseView.as_view(), name='pause_program'),
    url(r'^program/(?P<pk>[0-9]+)/cancel/$', views.ProgramCancelView.as_view(), name='cancel_program'),
    url(r'^program/(?P<pk>[0-9]+)/archive/$', views.ProgramArchiveView.as_view(), name='archive_program'),
    url(r'^program/(?P<pk>[0-9]+)/reactivate/$', views.ProgramReactivateView.as_view(), name='reactivate_program'),
    url(r'^program/(?P<pk>[0-9]+)/rename/$', views.ProgramSetNameView.as_view(), name='rename_program'),
    url(r'^program/(?P<pk>[0-9]+)/data_origin/$', views.program_set_data_origin, name='set_data_origin_program'),
    url(r'^program/(?P<pk>[0-9]+)/schedule/$', views.program_set_data_origin, name='set_program_schedule'),
]
