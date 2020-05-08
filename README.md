# JIRA2Taiga

A small python script to help your team transition from JIRA Kanban to Taiga Kanban.

`transfer.py` will read JIRA issues from a JIRA dump CSV and post them as Taiga User Stories
using the Taiga API.

Disclaimer: JIRA and Taiga don’t really play nice, and this is evident in the stories that the script
generates. For example, Linked Issues and Sub-Tasks don’t translate easily - and I have simply listed
these in the description of each story.

## How to use this repo

Install pandas: `pip install pandas`

It’s a lot of work

### Setting up repos and dumps

    1) `git clone` this repo (or download the zip)
    1) Create a repo in Taiga for your project
    2) Set the correct members, admins, and status names
    3) Download an issue dump from JIRA and convert it to CSV
    4) Delete the first three rows (the first row left should start with ‘Key’)
    5) Save the file in the git repo

### Filling out the config file

There is a fun config file in this repo called config.py that you will need to fill in with your information.

    - STATUS_MAP: Fill this in as a map for how your JIRA issue statuses should translate into Taiga. 
    JIRA statuses are the Key, Taiga the value.
    - BLOCKED_STATUSES: This is a list of all the JIRA statuses that are applied to blocked stories
    - CLOSED_STATUSES: This is a list of all the JIRA statuses that are applied to closed stories
    - TAIGA_USER: Your Taiga username (should be member of the Taiga repo)
    - TAIGA_PASSWORD: Your Taiga password
    - PROJECT_SLUG: The slug of your project in Taiga (open your project in a browser, it is the part of the URL
    containing your username and project name)
    - CSV_DUMP: The name of your dump file

### Running the script

Make sure you have [python 3 installed](https://www.python.org/downloads/).

Run `python transfer.py`

Check Taiga and make sure your stories transferred okay
