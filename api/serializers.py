# -*- coding: utf-8 -*-
from rest_framework import serializers
from accounts.models import CustomUser
from program_manager.models import Program
from qscore.models import QualityScore
from reports.models import Report


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'email',)


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ('id', 'program', 'date_created', 'date_completed', 'date_completed_estimate', 'records',
                  'duplicate_groups', 'duplicate_records', 'normalized_records', 'junk_records')


class QualityScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = QualityScore
        fields = ('id', 'created', 'program', 'score', 'percent_valid_location', 'percent_valid_phone',
                  'percent_valid_email', 'percent_spam_email', 'percent_complete', 'avg_age',
                  'avg_since_last_modified',)


class ProgramSerializer(serializers.ModelSerializer):
    reports = ReportSerializer(many=True)
    latest_report = serializers.SerializerMethodField()
    current_quality_score = serializers.SerializerMethodField()
    quality_scores = QualityScoreSerializer(many=True)
    source_name = serializers.SerializerMethodField()

    def get_latest_report(self, program):
        if program.latest_report:
            return ReportSerializer(program.latest_report).data
        return {}

    def get_current_quality_score(self, program):
        qs = program.get_current_quality_score()

        if not qs:
            return {}

        return QualityScoreSerializer(qs).data

    def get_source_name(self, program):
        return program.source.__class__.__name__

    class Meta:
        model = Program
        fields = ('id', 'name', 'current_quality_score', 'last_run', 'status', 'reports', 'quality_scores',
                  'source_name', 'pre_backup_url', 'post_run_url', 'progress', 'tags', 'current_activity_description',
                  'latest_report',)
