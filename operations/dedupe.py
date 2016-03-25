import hashlib
from program_manager import choices
from dateutil.parser import parse as dateutil_parse

class Deduper(object):

    def __init__(self, dm_rules, sr_rules, sv_rules):
        self.dm_rules = dm_rules
        self.sr_rules = sr_rules
        self.sv_rules = sv_rules
        # these are the fields we'll use to match duplicates
        self.match_fields = []
        for dm in self.dm_rules:
            self.match_fields.append(dm.field.get_name())
        self.hashes = {}
        self.clusters = {}

    def digest_key_field(self, value):
        if not value:
            return None
        return hashlib.sha1(value.strip().lower()).digest()

    def feed_record(self, record):
        try:
            if record['IsConverted'] == 'true':
                # ignore converted leads
                return
        except KeyError:
            pass
        key = tuple((self.digest_key_field(record[f]) for f in self.match_fields))
        if None in key:
            return
        key = hashlib.sha1(''.join(key)).digest()
        if key in self.hashes:
            #print 'found duplicate: %s' % str(key)
            self.hashes[key].append(record['_id'])
            self.clusters[key] = self.hashes[key]
        else:
            self.hashes[key] = [record['_id']]

    def record_passes_sr_rule(self, cluster, record_index, rule):
        record = cluster[record_index]
        field = rule.field.get_name()
        value = record[field].lower()
        if rule.rule in ['LOWEST_VALUE', 'HIGHEST_VALUE']:
            try:
                value = float(value)
            except ValueError:
                return False
            if rule.rule == 'LOWEST_VALUE':
                other = min(cluster, key=lambda r: r[field])
            elif rule.rule == 'HIGHEST_VALUE':
                other = max(cluster, key=lambda r: r[field])
            return cluster.index(other) == record_index
        elif rule.rule in ['OLDEST', 'NEWEST']:
            def sort_key(record):
                return dateutil_parse(record[field])
            try:
                if rule.rule == 'OLDEST':
                    other = min(cluster, key=sort_key)
                elif rule.rule == 'NEWEST':
                    other = max(cluster, key=sort_key)
                if cluster.index(other) == record_index:
                    return True
                else:
                    return False
            except ValueError:
                return False
        elif rule.rule in ['TRUE', 'FALSE']:
            if rule.rule == 'TRUE':
                return rule.value == 'true'
            else:
                return rule.value == 'false'
        else:
            return self.compute_text_rule(rule, value)

    def compute_text_rule(self, rule, value):
        value = value.lower()
        rule.value = rule.value.lower()
        if rule.rule == choices.TEXT_EQUALS:
            return value == rule.value
        elif rule.rule == choices.TEXT_NOT_EQUALS:
            return value != rule.value
        elif rule.rule == choices.TEXT_CONTAINS:
            return rule.value in value
        elif rule.rule == choices.TEXT_STARTS:
            return value.startswith(rule.value)

    def get_canonical_field_value(self, cluster_data, field_id):
        canonical = cluster_data[0][field_id]
        for rule in reversed(self.sv_rules):
            if field_id != rule:
                continue
            if rule.rule in ['OLDEST', 'NEWEST']:
                if rule.rule == 'OLDEST':
                    return min(cluster_data, key=self.get_record_last_modified)[field_id]
                elif rule.rule == 'NEWEST':
                    return max(cluster_data, key=self.get_record_last_modified)[field_id]
            elif rule.rule in ['NUMADD', 'NUMAVG', 'NUMMAX', 'NUMMIN']:
                numbers = []
                for record in cluster_data:
                    try:
                        numbers.append(float(record[field_id]))
                    except ValueError:
                        continue
                if not numbers:
                    return canonical
                if rule.rule == 'NUMADD':
                    return sum(numbers)
                elif rule.rule == 'NUMAVG':
                    return sum(numbers) / float(len(numbers))
                elif rule.rule == 'NUMMAX':
                    return max(numbers)
                elif rule.rule == 'NUMMIN':
                    return min(numbers)
            elif rule.rule == 'CONCAT':
                return '\n\n'.join([f[field_id] for f in cluster_data if f[field_id]])
            else:
                for record in cluster_data:
                    value = record[field_id]
                    if self.compute_text_rule(rule, value):
                        return value
        return canonical

    def sort_cluster(self, cluster_data):
        def sort_key(record):
            return (tuple((self.record_passes_sr_rule(cluster_data,
                cluster_data.index(record), rule) for rule in self.sr_rules)) +
                (self.get_record_last_modified(record),))
        cluster_data = sorted(cluster_data, key=sort_key, reverse=True)
        return cluster_data

    def get_record_last_modified(self, record):
        last_modified = (record['CreatedDate'] or
                         record['LastModifiedDate'])
        return dateutil_parse(last_modified)

    def get_canonical(self, cluster_data):
        master = cluster_data[0]
        canonical = dict(master)
        # process sv rules
        for key, field in canonical.viewitems():
            if key.startswith('_'):
                continue
            canonical[key] = self.get_canonical_field_value(cluster_data, key)
        # update null fields
        for secondary in cluster_data[1:]:
            for key, value in secondary.viewitems():
                if key.startswith('_'):
                    continue
                if not canonical[key]:
                    canonical[key] = value
        return canonical

