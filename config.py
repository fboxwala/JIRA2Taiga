# Config variables for transfer script, fill out with strings corresponding to your taiga/JIRA
# project

STATUS_MAP = {
    'Backlog': 'New',
    'Ready for Acceptance': 'Ready for test',
    'In Progress': 'In progress',
    'Blocked': 'In progress',
    'Done': 'Done'
    'JIRA Status': 'Tagia Status'
}

BLOCKED_STATUSES = ['Blocked']
CLOSED_STATUSES = ['Done']

TAIGA_USER = 'username'
TAIGA_PASSWORD = 'pword'

PROJECT_SLUG = 'username-project-name'

CSV_DUMP = 'dump.csv'
