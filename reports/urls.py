from django.conf.urls import url

from reports.views import (
    ReportListView,
    QualityScoreOverTimeView,
    QualityScoreSnapshot
    )

urlpatterns = [
    url(r'^$', ReportListView.as_view(), name='reports'),
    url(r'^qot/(?P<pk>[^/]+)/$', QualityScoreOverTimeView.as_view(),
        name='report_qot'),
    url(r'^snapshot/$', QualityScoreSnapshot.as_view(),
        name='report_snapshot'),
]
