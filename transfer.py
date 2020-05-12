import csv
import requests
import json
from time import sleep

import config as c


data = {
    'type': 'normal',
    'username': c.TAIGA_USER,
    'password': c.TAIGA_PASSWORD
        }

headers = {
    'Content-Type': 'application/json',
    'x-disable-pagination': 'True'
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

# deactivate posts
# requests.post = lambda url, **kwargs: print(f'{url}\n{"*"*150}\n{kwargs["data"]}')

def format_story(row):

    tags = row['Labels']
    tags = tags.replace(',', '')
    tags = tags.split()

    status = status_map[row['Status']]
    if row['Issue Type'] in c.CUSTOM_USERTYPE_TAGS:
        tags.append(row['Issue Type'])

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

    points  = row[c.JIRA_POINTS_COLUMN]

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



def format_epic(row):

    tags = row['Labels']
    tags = tags.replace(',', '')
    tags = tags.split()

    status = status_map[row['Status']]

    subject = row['Project key'] + ': ' + row['Summary']

    description = row['Description']
    assignee = row['Assignee']
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
                   'Related Stories: ' + related)

    blocked = False
    closed = False

    if row['Status'] in c.BLOCKED_STATUSES:
        blocked = True

    if row['Status'] in c.CLOSED_STATUSES:
        closed = True

    postdict = {
        "assigned_to": c.USER_MAP[assignee],
        "blocked_note": "",
        "description": description,
        "is_blocked": blocked,
        "is_closed": closed,
        "color": "",
        "project": project_id,
        "subject": subject,
        "tags": tags,
        "watchers": []
    }

    return postdict


def associate_to_stories(row):
    epic_subject = row['Project key'] + ': ' + row['Summary']
    subtasks = df[df['Parent'] == float(row['Issue id'])]

    # Get all epics in project
    url = f'https://api.taiga.io/api/v1/epics?project={project_id}'
    r = requests.get(url, headers=headers)
    temp = pd.DataFrame(r.json())
    # Select current epic id
    epic_id = temp['id'].where(temp['subject'] == epic_subject).dropna().apply(int).tolist()[0]

    for _, story in subtasks.iterrows():
        subject = story['Project key'] + ': ' + story['Summary']

        # Get all user stories in project
        url = f'https://api.taiga.io/api/v1/userstories?project={project_id}'
        r = requests.get(url, headers=headers)
        temp = pd.DataFrame(r.json())
        # Select only ids of children of current epic
        child_ids = temp['id'].where(temp['subject'] == subject).dropna().apply(int).tolist()

        url = f'https://api.taiga.io/api/v1/epics/{epic_id}/related_userstories'

        # Iterate for each child_id and make the request
        for x in child_ids:
            print('.', end="", flush=True)
            data = {
                "epic": epic_id,
                "user_story": x
            }
            data = json.dumps(data)
            sent = False
            while not sent:
                r = requests.post(url, headers=headers, data=data)
                sent = True
                if r.status_code not in [201, 400]:
                    sent = False
                    print(r.status_code)
                    print(r.content)
                    if r.status_code == 429:
                        wait = 1.1*int(r.headers['X-Throttle-Wait-Seconds'])+20
                        print(f'sleep({wait})')
                        sleep(wait)
            sleep(2)



print('Posting stories and epics to Taiga (this could take a while)', flush=True)
with open(c.CSV_DUMP) as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        parsed = False
        sent = False
        print('.', end="", flush=True)
        if row['Issue Type'] in c.STORY_ISSUE_TYPE:
            url = 'https://api.taiga.io/api/v1/userstories'
            data = format_story(row)
            parsed = True
        elif row['Issue Type'] in c.EPIC_ISSUE_TYPE:
            url = 'https://api.taiga.io/api/v1/epics'
            data = format_epic(row)
            parsed = True
        if parsed:
            data = json.dumps(data)
            while not sent:
                r = requests.post(url, headers=headers, data=data)
                sent = True
                if r.status_code not in [201]:
                    sent = False
                    print(r.status_code)
                    print(r.content)
                    if r.status_code == 429:
                        wait = 1.1*int(r.headers['X-Throttle-Wait-Seconds'])+20
                        print(f'sleep({wait})')
                        sleep(wait)
            sleep(2)

print(' ')

print('Associating epics to stories in Taiga (this could take a while)', flush=True)
with open(c.CSV_DUMP) as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        if row['Issue Type'] in c.EPIC_ISSUE_TYPE:
            associate_to_stories(row)


print(' ')