from django.contrib import admin

from .models import (
    Program, TableFilter, FieldFilter, SurvivingRecordRule,
    SurvivingValueRule, DupMatchRule, Job
    )
from qscore.models import QualityScore


class QualityScoreInline(admin.TabularInline):
    model = QualityScore
    extra = 0


class TableFilterInline(admin.TabularInline):
    model = TableFilter
    extra = 0


class FieldFilterInline(admin.TabularInline):
    model = FieldFilter
    raw_id_fields = ('field',)
    extra = 0


class DupMatchRuleInline(admin.TabularInline):
    model = DupMatchRule
    readonly_fields = ('priority', 'batch_program', 'field', 'rule')
    extra = 0


class SurvivingRecordRuleInline(admin.TabularInline):
    model = SurvivingRecordRule
    readonly_fields = ('priority', 'batch_program', 'field', 'rule', 'value')
    extra = 0


class SurvivingValueRuleInline(admin.TabularInline):
    model = SurvivingValueRule
    readonly_fields = ('priority', 'batch_program', 'field', 'rule', 'value')
    extra = 0


class JobAdmin(admin.ModelAdmin):
    model = Job
    list_display = ('name', 'task_id', 'status', 'program')
    list_display_links = ('program',)
    list_filter = ('status',)


admin.site.register(Program)
admin.site.register(Job, JobAdmin)
# unregister djcelery
import djcelery
admin.site.unregister(djcelery.models.TaskState)
admin.site.unregister(djcelery.models.WorkerState)
#admin.site.unregister(djcelery.models.IntervalSchedule)
#admin.site.unregister(djcelery.models.CrontabSchedule)
#admin.site.unregister(djcelery.models.PeriodicTask)
