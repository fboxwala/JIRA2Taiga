import csv
import requests
import json

import config as c


data = {
    'type': 'normal',
    'username': c.TAIGA_USER,
    'password': c.TAIGA_PASSWORD
        }

headers = {
    'Content-Type': 'application/json'
        }

url = 'https://api.taiga.io/api/v1/auth'

data = json.dumps(data)
r = requests.post(url, headers=headers, data=data)
r = r.json()
auth = r['auth_token']

headers['Authorization'] = 'Bearer ' + auth

url = 'https://api.taiga.io/api/v1/projects/by_slug?slug=' + c.PROJECT_SLUG

r = requests.get(url, headers=headers)

print('Retrieving auth token...', flush=True)

r = r.json()

status_list = r['us_statuses']

status_ids = {}

for taiga_status in status_list:
    status_ids[taiga_status['name']] = taiga_status['id']

status_map = {}

for jira, taiga in c.STATUS_MAP.items():
    status_map[jira] = status_ids[taiga]

project_id = status_list[0]['project_id']
import pandas as pd
df = pd.read_csv(c.CSV_DUMP)


def format_story(row):

    tags = row['Labels']
    tags = tags.replace(',', '')
    tags = tags.split()

    status = status_map[row['Status']]

    subject = row['Project key'] + ': ' + row['Summary']

    description = row['Description']
    assignee = row['Assignee']
    subtasks = df[df['Parent'] == float(row['Issue id'])]['Summary'].tolist()
    subtasks = '\n'.join(subtasks)
    reporter = row['Reporter']
    related = row['Outward issue link (Relates)']
    watchers = row['Watchers']

    description = ('Description: ' +
                   description +
                   '\n'
                   '\n'
                   'Reporter: ' + reporter +
                   '\n'
                   'Watchers: ' + watchers +
                   '\n'
                   'Sub-Tasks: ' + subtasks +
                   '\n'
                   'Related Stories: ' + related)

    blocked = False
    closed = False

    points  = row['Custom field (Story point estimate)']

    if row['Status'] in c.BLOCKED_STATUSES:
        blocked = True

    if row['Status'] in c.CLOSED_STATUSES:
        closed = True

    postdict = {
        "assigned_to": c.USER_MAP[assignee],
        "backlog_order": 2,
        "blocked_note": "",
        "client_requirement": False,
        "description": description,
        "is_blocked": blocked,
        "is_closed": closed,
        "kanban_order": 37,
        "milestone": None,
        "points": {c.JIRA_PERMISSION: c.POINT_MAP[points]},
        "project": project_id,
        "sprint_order": 2,
        "status": status,
        "subject": subject,
        "tags": tags,
        "team_requirement": False,
        "watchers": []
    }

    return postdict



print('Posting stories to Taiga (this could take a while)', flush=True)
with open(c.CSV_DUMP) as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        print('.', end="", flush=True)
        if row['Issue Type'] in c.STORY_ISSUE_TYPE:
            url = 'https://api.taiga.io/api/v1/userstories'
            data = format_story(row)
        elif row['Issue Type'] in c.EPIC_ISSUE_TYPE:
            pass
        data = json.dumps(data)
        r = requests.post(url, headers=headers, data=data)

print(' ')
