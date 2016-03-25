import csv
import dedupe
import logging
import distance
import unidecode
from django.core.management.base import BaseCommand, CommandError

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Train the dedupe weight models interactively.'

    def add_arguments(self, parser):
        #parser.add_argument('ppd', nargs='+', type=int)
        pass

    def preprocess_column(self, column):
        # TODO: improve with extraneous character removal
        if not column:
            return None
        return unidecode.unidecode(column.lower())

    def handle(self, *args, **options):
        logger.info('Starting dedupe training.')
        data = {}
        logger.info('Loading training data...')
        fields = [
            {'field': 'First Name', 'type': 'String'},
            {'field': 'Last Name', 'type': 'String'},
            {'field': 'Mobile', 'type': 'String'},
        ]
        with open('temp/report1445218513088.csv', 'rb') as training_file:
            reader = csv.DictReader(training_file)
            identifier = 1
            for row in reader:
                clean = [(k, self.preprocess_column(v)) for (k, v) in row.items()]
                clean = dict(clean)
                # remove empty records
                delete = False
                for field in fields:
                    if not clean[field['field']]:
                        delete = True
                        break
                if not delete:
                    data[identifier] = clean
                    identifier += 1
        logger.info('Loaded training data.')
        deduper = dedupe.Dedupe(fields)
        logger.info('Taking samples...')
        deduper.sample(data, 10000)
        logger.info('Automatic labeling started...')
        labeled = {'match': [], 'distinct': []}
        search_keys = [f['field'] for f in fields]
        for i in range(0, 200):
            for uncertain in deduper.uncertainPairs():
                total_distance = 0
                for key, value in uncertain[0].items():
                    if not key in search_keys:
                        continue
                    second = uncertain[1][key] or ''
                    total_distance += distance.levenshtein(value or '', second)
                print uncertain
                print 'distance:', total_distance
                if total_distance < 10:
                    labeled['match'].append(uncertain)
                else:
                    labeled['distinct'].append(uncertain)
        deduper.markPairs(labeled)
        #dedupe.consoleLabel(deduper)
        logger.info('Learning rules...')
        deduper.train()
        logger.info('Training finished.')
        with open('training.json', 'wb') as training_file:
            deduper.writeTraining(training_file)
        with open('settings.json', 'wb') as settings_file:
            deduper.writeSettings(settings_file)
        logger.info('Beggining blocking.')
        logger.info('Computing thresholds...')
        threshold = deduper.threshold(data, recall_weight=2)
        logger.info('Clustering...')
        clustered_dupes = deduper.match(data, threshold)
        logger.info('%s duplicate sets.' % len(clustered_dupes))
        with open('results_auto', 'wb') as output_file:
            output_file.write(repr(clustered_dupes))
        logger.info('Finished blocking.')
        logger.info('Finished dedupe training.')


    def manual_training(self, *args, **options):
        logger.info('Starting dedupe training.')
        data = {}
        logger.info('Loading training data...')
        fields = [
            {'field': 'First Name', 'type': 'String'},
            {'field': 'Last Name', 'type': 'String'},
            {'field': 'Mobile', 'type': 'String'},
        ]
        with open('temp/report1445218513088.csv', 'rb') as training_file:
            reader = csv.DictReader(training_file)
            identifier = 1
            for row in reader:
                clean = [(k, self.preprocess_column(v)) for (k, v) in row.items()]
                clean = dict(clean)
                # remove empty records
                delete = False
                for field in fields:
                    if not clean[field['field']]:
                        delete = True
                        break
                if not delete:
                    data[identifier] = clean
                    identifier += 1
        logger.info('Loaded training data.')
        deduper = dedupe.Dedupe(fields)
        logger.info('Taking samples...')
        deduper.sample(data, 10000)
        dedupe.consoleLabel(deduper)
        deduper.train()
        with open('training.json', 'wb') as training_file:
            deduper.writeTraining(training_file)
        with open('settings.json', 'wb') as settings_file:
            deduper.writeSettings(settings_file)
        logger.info('Beggining blocking.')
        logger.info('Computing thresholds...')
        threshold = deduper.threshold(data, recall_weight=2)
        logger.info('Clustering...')
        clustered_dupes = deduper.match(data, threshold)
        logger.info('%s duplicate sets.' % len(clustered_dupes))
        with open('results', 'wb') as output_file:
            output_file.write(repr(clustered_dupes))
        logger.info('Finished blocking.')
        logger.info('Finished dedupe training.')
