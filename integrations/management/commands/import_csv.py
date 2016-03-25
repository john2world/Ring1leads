import os
from django.core.management.base import BaseCommand
from django.conf import settings
from integrations.salesforce.prepare import import_csv_to_sf


class Command(BaseCommand):
    help = 'Imports specified CSV file or folder to SF account associated with an email'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str)
        parser.add_argument('--file',
                            dest='file',
                            default=os.path.join(settings.BASE_DIR, 'temp/report_short_mod.csv'),
                            help='CSV file that you wish to import')
        parser.add_argument('--folder',
                            dest='folder',
                            default=None,
                            help='Folder containing CSV files you\'d like to import')  # bulk
        parser.add_argument('--object',
                            dest='object',
                            default='Lead',
                            help='SF object name (table name)')
        parser.add_argument('--count',
                            dest='count',
                            default=0,
                            type=int,
                            help='Number of rows to process')
        parser.add_argument('--repeat',
                            dest='repeat',
                            default=1,
                            type=int,
                            help='Designates how many times the file should be processed')

    def handle(self, *args, **options):
        import_csv_to_sf(options['file'], options['email'], sf_object_name=options['object'], count=options['count'],
                         repeat=options['repeat'])
