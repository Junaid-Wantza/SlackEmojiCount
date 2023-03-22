import matplotlib
matplotlib.use('TkAgg')

import requests as rq
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file

ROOT_URL = 'https://slack.com/api/'
TOKEN = os.environ.get('SLACK_API_TOKEN')
SCOPES = ['conversations.list', 'conversations.history', 'reactions.get']


def get_request_variables(ROOT_URL, SCOPES, TOKEN, scope, **kwargs):
    rq_url = f'{ROOT_URL}{SCOPES[scope]}'
    rq_headers = {
        'content-type': 'application/x-www-form-urlencoded',
        'Authorization': f'Bearer {TOKEN}'
    }
    rq_params = {key: value for key, value in kwargs.items()}

    return rq_url, rq_headers, rq_params


def get_response(ROOT_URL, SCOPES, TOKEN, scope, **kwargs):
    session = rq.Session()
    url, headers, params = get_request_variables(
        ROOT_URL, SCOPES, TOKEN, scope, **kwargs)
    res = session.get(url=url, headers=headers, params=params)
    return res


def get_messages(ROOT_URL, SCOPES, TOKEN):
    channel_res = get_response(
        ROOT_URL, SCOPES, TOKEN, 0, limit=1000, excluded_archive=True)
    channel_data = [{'id': i['id'],
                     'name': i['name'],
                     'created': i['created'],
                     'members': i['num_members'],
                     'is_group': i['is_group']} for i in channel_res.json()['channels']]

    for channel in channel_data:
        res = get_response(ROOT_URL, SCOPES, TOKEN, 1,
                           channel=channel['id'], limit=1000)
        for message in res.json()['messages']:
            yield message


def get_emoji_data(ROOT_URL, SCOPES, TOKEN):
    emj_data = [{'ts': msg['ts'],
                 'name': reaction['name'],
                 'count': reaction['count']}
                for msg in get_messages(ROOT_URL, SCOPES, TOKEN)
                if 'reactions' in msg
                for reaction in msg['reactions']]
    return emj_data


emj_data = get_emoji_data(ROOT_URL, SCOPES, TOKEN)
emj_df = pd.DataFrame(emj_data)
emj_counts = emj_df.groupby('name')['count'].sum().sort_values(
    ascending=False)


plt.bar(x=emj_counts.index[:30], height=emj_counts[:30])
plt.xticks(rotation=90)
plt.xlabel('Emoji Name')
plt.ylabel('Count')
plt.title('Top 30 Emojis Used in Slack Workspace')
plt.show()
