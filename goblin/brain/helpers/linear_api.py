import json
import requests
import os

class LinearQueryException(Exception):
    pass

class LinearApi:
    def __init__(self, LINEAR_API_KEY=''):
        self.set_url('https://api.linear.app/graphql')
        self.set_api_key(os.environ.get("LINEAR_API_KEY", ""))
        self.headers = {
            "Authorization" : self.LINEAR_API_KEY
        }
        pass

    def set_url(self, url):
        self.graphql_url = url

    def set_api_key(self, LINEAR_API_KEY):
        self.LINEAR_API_KEY = LINEAR_API_KEY

    def query_grapql(self, query):
        r = requests.post(self.graphql_url, json={
            "query": query
        }, headers=self.headers)

        response = json.loads(r.content)

        if 'errors' in response:
            raise LinearQueryException(response["errors"])

        return response

    def query_basic_resource(self, resource=''):
        resource_response = self.query_grapql(
            """
                query Resource {"""+resource+"""{nodes{id,name}}}
            """
        )

        return resource_response["data"][resource]["nodes"]

    def create_issue(self, title, description='', project_id='', state_id='', team_id=''):
        create_response = self.query_grapql(
            """
            mutation IssueCreate {{
              issueCreate(
                input: {{
                    title: "{title}"
                    description: "{description}"
                    projectId: "{project_id}"
                    stateId: "{state_id}"
                    teamId: "{team_id}"
                }}
              ) {{
                success
                issue {{
                  id
                  title
                }}
              }}
            }}
            """.format(title=title, description=description, project_id=project_id, team_id=team_id, state_id=state_id)
        )
        return create_response['data']['issueCreate']

    def get_issues(self, filters=None):
        """
        Fetch Linear tickets using GraphQL with arbitrary filters.

        :param filters: A dictionary of filters to apply, e.g., {"state": "open", "priority": 1}
        :return: JSON response from the Linear API
        """

        # Basic GraphQL query structure
        query = """
        query($filters: IssueFilter) {
        issues(filter: $filters) {
            nodes {
            id
            title
            description
            state {
                name
            }
            priority
            createdAt
            }
        }
        }
        """

        # Prepare variables for the GraphQL query
        variables = {
            "filters": filters or {}
        }

        # Make the POST request to the GraphQL API
        response = requests.post(self.graphql_url, json={"query": query, "variables": variables}, headers=self.headers)

        # Check for a successful response
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Query failed to run by returning code of {response.status_code}. {response.text}")
    
    def teams(self):
        return self.query_basic_resource('teams')

    def states(self):
        return self.query_basic_resource('workflowStates')

    def projects(self):
        return self.query_basic_resource('projects')

