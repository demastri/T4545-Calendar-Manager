from bs4 import BeautifulSoup
import requests
import LogDetail

class Games_IO(object):

    BASE_URL = "http://team4545league.org/"

    def __init__(self):
        return

    """
        <td class="schedbc_nhb"><a href ="../pgnplayer/pgnplayer.php?ID=28412&amp;Board=3">1:0</a></td>
        <td class="schedbc_nhb">-</td>
    """

    @staticmethod
    def get_games_data(url):
        response = requests.get(url)

        # Resolve the response
        if response.status_code == 200:
            html_content = response.text
        else:
            LogDetail.LogDetail().print_log("log", "Error retrieving game data: " + str(response.status_code))

        return html_content

    @staticmethod
    def getPGNOrResultFromCell(linkCell):
        # extract result or link from cell
        # if it's a set result (or no result) return it

        if linkCell.contents[0] == linkCell.string:
            result = linkCell.text
            if result == "-":
                result = "";
            return result

        # if it's a link, get the html from the link
        link = Games_IO.BASE_URL + (linkCell.contents[0].attrs["href"])[3:]
        pgn_page = Games_IO.get_games_data(link)
        soup = BeautifulSoup(pgn_page, 'html.parser')

        # it's just a <P> -- PGN Text -- </p> tag where the first 6 characters of the text are  "[Event"
        possible_pgn = soup.find_all('p')
        for tag in possible_pgn:
            if tag.text.strip()[:6] == "[Event":
                return tag.text

        LogDetail.LogDetail().print_log("log", "expected PGN data from<"+link+">")
        return ""
