import requests


class Games_IO(object):
    def __init__(self):
        return

    def get_games_data(self, url):
        response = requests.get(url)

        # Resolve the response
        if response.status_code == 200:
            html_content = response.text
        else:
            print("log", "Error retrieving game data: "+ str(response.status_code))

        return html_content

