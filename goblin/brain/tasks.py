from brain.agents.developer_one.developer_one import DeveloperOne
from celery import shared_task
from brain.helpers.linear_api import LinearApi
import numpy as np
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import tempfile


@shared_task
def check_tasks():
    print('testing')
    print('hello?')

# This is the main entrypoint for brain working on it's own. This task runs every minute and checks for any work that needs to be done
@shared_task
def ping_brain():
    agent_data = {
        # These are used as context
        "codebase_path": "~/dev/ftf",
        "documentation_url": "https://cityflavor.com/schema/swagger-ui/",
        "testing_commands": "python manage.py test",
        "additional_buffer": "",
        # This is the actual thing to build
        "prompt": "Build a modal on the portal home page that allows. ",
    }
    agent = DeveloperOne(agent_data)

    # Find Linear Tickets
    linear_api = LinearApi()
    issues = linear_api.get_issues(filters={
        "label": { "name": "Goblin" },
    })


    for issue in issues:
        ticket_name = issue["name"]
        ticket_description = issue["description"] 
        agent.run()

