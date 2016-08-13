#!/usr/bin/env python

import os
import sys
import json
# from datetime import datetime

import django
from django.utils import timezone
from django.utils.text import slugify

sys.path.append("..")
os.environ['DJANGO_SETTINGS_MODULE'] = 'website.settings'
django.setup()

sys_file = '../systems/fixtures/systems.json'
sys_ver_file = '../systems/fixtures/system_versions.json'
svfo_file = '../systems/fixtures/system_version_feature_options.json'

####### Create a map of field:name:pk for setting foreign keys and many to many
####### pk = Primary Key

fixtures_dir = '../systems/fixtures/'
fixtures = os.listdir(fixtures_dir)
fixtures = [fixtures_dir + x for x in fixtures]

for filename in [sys_file, sys_ver_file, svfo_file]:
    try:
        fixtures.remove(filename)
    except:
        # File not there
        pass

pk_map = {}

for fixture in fixtures:
    with open(fixture, 'r') as fd:
        data = json.loads(fd.read())
        for datum in data:
            model = datum['model']
            if model == 'systems.FeatureOption':
                field = 'feature_options-' + str(datum['fields']['feature'])
                entries = pk_map.get(field, {})
                entries[datum['fields']['value']] = datum['pk']
                pk_map[field] = entries
            elif model == 'systems.Feature':
                field = 'feature'
                entries = pk_map.get(field, {})
                entries[datum['fields']['label']] = datum['pk']
                pk_map[field] = entries
            elif model == 'systems.License':
                field = 'license'
                entries = pk_map.get(field, {})
                entries[datum['fields']['name']] = datum['pk']
                pk_map[field] = entries
            elif model == 'systems.OperatingSystem':
                field = 'oses'
                entries = pk_map.get(field, {})
                entries[datum['fields']['name']] = datum['pk']
                pk_map[field] = entries
            elif model == 'systems.ProgrammingLanguage':
                field = 'written_in'
                entries = pk_map.get(field, {})
                entries[datum['fields']['name']] = datum['pk']
                pk_map[field] = entries
            else:
                print 'Skipping ' + model + ' with pk:', datum['pk']

print '\n\npk_map\n\n'
print json.dumps(pk_map, indent=4)
print '\n\n'

def map_to_pk(fields, field, values, key, filename):
    """
    Map names in values under a field to pk's. Append to existing fields in the fixture.
    ex. fields = { ... license: [1, 2] ... } field = 'license', values = ['MIT'], filename = foo.json
    result = [1, 2, 8]
    """
    result = fields.get(field, [])
    value = list(values)
    for value in values:
        try:
            result.append(pk_map[field][value])
        except KeyError:
            print 'No model under ' + field + ' exactly matches "' + value + '" from "' + key +  '" in ' + filename
    return result

# Maps names of fields in json files to system_version fields
system_map = {
    'Name': 'name',
    'Description': 'description',
    'Email': 'creator',
    'Developer': 'developer',
    'History': 'history',
    'License': 'license',
    'Website': 'website',
    'Programming Language': 'written_in',
    'Operating Systems': 'oses',
    # TODO Not formatted correctly in the json files
    # 'Project Type': 'project_type',
    # 'Start Date': 'start_year',
    # 'End Date': 'end_year',
    # 'Derived From': 'derived_from'
}

files = os.listdir('spring2016')

systems = [] # models.System
system_versions = [] # models.SystemVersion
svfo = [] # models.SystemVersionFeatureOptions

# Read json files and make fixtures out of them
pk = 1
for filename in files:
    with open('spring2016/' + filename, 'r') as infile:
        try:
            data = json.loads(infile.read())
        except Exception as error:
            print 'Could not read ', filename, error
            continue

        sys_fixture = {
            'pk': pk,
            'model': 'systems.System',
            'fields': {
                'name': data['Name'],
                'slug': slugify(data['Name']),
                'created': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        }

        fields = {}

        for key, value in system_map.iteritems():
            try:
                if not isinstance(data[key], list):
                    fields[value] = data[key]
            except KeyError as error:
                print 'Could not find ' + str(error) + ' key in ' + filename

        for key, value in data.iteritems():
            if 'Citation' in key:
                # Citations not yet handled
                continue
            elif ' Description' in key:
                field = 'description_' + key[:-12].replace(' ', '').lower()
                fields[field] = value
            elif ' Options' in key:
                field = 'support_' + key[:-8].replace(' ', '').lower()
                if len(value) > 0 and value[0] != 'Not Supported' and value[0] != 'N/A':
                    # Is supported
                    fields[field] = True
                    field = 'feature_options-' + str(pk_map['feature'][key[:-8]])

                    for fo in map_to_pk(fields, field, value, key, filename):
                        svfo.append({
                            'pk': len(svfo) + 1,
                            'model': 'systems.SystemVersionFeatureOption',
                            'fields': {
                                'system_version': pk,
                                'feature_option': fo,
                            }
                        })

                elif value[0] == 'Not Supported':
                    fields[field] = False
                else:
                    fields[field] = None
            elif isinstance(value, list):
                # Some type of list, use the pk_map
                field = system_map.get(key, None)
                if field != None:
                    fields[field] = map_to_pk(fields, field, value, key, filename)
            elif system_map.get(key, None) is None or fields.get(system_map[key], None) is None:
                # Not a list and not in system_map
                print 'Could not map ' +  key + ' in ' + filename + ' to any models'

        fields['system'] = pk
        fields['created'] = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        sys_ver_fixture = {
            'pk': pk,
            'model': 'systems.SystemVersion',
            'fields': fields
        }
        systems.append(sys_fixture)
        system_versions.append(sys_ver_fixture)

    pk = pk + 1

# Write the fixtures to a file
with open(sys_file, 'w') as outfile1, open(sys_ver_file, 'w') as outfile2, open(svfo_file, 'w') as outfile3:
    mycmp = lambda x,y: cmp(x['pk'], y['pk'])

    systems.sort(cmp=mycmp)
    outfile1.write(json.dumps(systems, indent=4))

    system_versions.sort(cmp=mycmp)
    outfile2.write(json.dumps(system_versions, indent=4))

    svfo.sort(cmp=mycmp)
    outfile3.write(json.dumps(svfo, indent=4))