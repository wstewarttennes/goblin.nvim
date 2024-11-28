
# Jestor is the inJestor of all data for the brain. 


# This main function `'jestor` will start pulling all data based on the provided start and end dates
from brain.jestor.lib.fireflies import FirefliesApi


def jestor(start_date, end_date):


    # Get Fireflies meeting transcriptions
    fireflies_api = FirefliesApi()
    filter = {
        "start_date": start_date,
        "end_date": end_date
    }
    fireflies_meetings = fireflies_api.get_meetings(filter)


