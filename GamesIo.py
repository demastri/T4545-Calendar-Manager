from bs4 import BeautifulSoup
import requests
import LogDetail
from datetime import datetime
from ConfigData import config_data_factory


class GamesIo(object):

    def __init__(self, *args):
        if len(args) == 0:
            self.whitePlayer = None
            self.blackPlayer = None
            self.whiteTeam = None
            self.blackTeam = None
            self.status = None
            self.division = None
            self.game_time = None
            self.round = None
            self.board = None
            self.result = None
        if len(args) == 1:
            td_list = args[0]
            self.whitePlayer = td_list[4].text
            self.whiteTeam = td_list[3].text
            self.blackPlayer = td_list[6].text
            self.blackTeam = td_list[7].text
            self.division = td_list[0].text
            self.game_time = GamesIo.get_complete_game_time(td_list[2].text)
            self.round = td_list[1].text
            self.board = td_list[8].text
            self.result = GamesIo.get_game_result(td_list[5])

    def team_tag(self):
        return self.whiteTeam.strip()+"-"+self.blackTeam.strip()

    def player_tag(self):
        return self.whitePlayer.strip()+"-"+self.blackPlayer.strip()

    def game_key(self):
        return self.team_tag() + ": " + self.player_tag()

    """
        <td class="schedbc_nhb"><a href ="../pgnplayer/pgnplayer.php?ID=28412&amp;Board=3">1:0</a></td>
        <td class="schedbc_nhb">-</td>
    """

    @staticmethod
    def get_html_data(url):
        response = requests.get(url)

        # Resolve the response
        if response.status_code == 200:
            html_content = response.text
            return html_content

        LogDetail.LogDetail().print_log("log", "Error retrieving html data: " + str(response.status_code))
        return None

    @staticmethod
    def load_games(url):
        out_list = []
        games_html = GamesIo.get_html_data(url)
        game_soup = BeautifulSoup(games_html, 'html.parser')

        pairing_table = game_soup.find_all('table', {'class': 'sched'})
        pairings = pairing_table[0].find_all('tr')
        for tag in pairings:
            # read the elements of this row...
            pairing_attr = tag.find_all('td', recursive=False)
            if len(pairing_attr) == 0:
                continue
            new_game = GamesIo(pairing_attr)
            out_list.append(new_game)

        return out_list

    @staticmethod
    def get_game_result(link_cell):
        # extract result or link from cell
        # if it's a set result (or no result) return it

        if link_cell.contents[0] == link_cell.string:
            posted_result = link_cell.text
            if posted_result == "-":
                return "Game is scheduled\n"
            return "Game is completed with set result: "+posted_result+"\n"

        if "href" in link_cell.contents[0].attrs:
            # if it's a link, get the html from the link
            link = config_data_factory().pgn_site + (link_cell.contents[0].attrs["href"])[3:]
            pgn_page = GamesIo.get_html_data(link)
            soup = BeautifulSoup(pgn_page, 'html.parser')

            # it's just a <P> -- PGN Text -- </p> tag where the first 6 characters of the text are  "[Event"
            possible_pgn = soup.find_all('p')
            for tag in possible_pgn:
                if tag.text.strip()[:6] == "[Event":
                    return "Game is completed:\n" + tag.text
            LogDetail.LogDetail().print_log("log", "expected PGN data from<"+link+">")
            return "Game status is unknown\n"

        return "Game is in progress\n"

    @staticmethod
    def get_complete_game_time(disp_time):
        cur_time = datetime.now()
        cur_year = cur_time.year

        # note that the event string does NOT include a year...  Looks like:   Sat, Mar 16, 11:00
        event_time = datetime.strptime(str(cur_year) + " " + disp_time + " -0400", "%Y %a, %b %d, %H:%M %z")

        # be sure that if the event is in Jan and the current date is Dec, set it to NEXT year
        if cur_time.month == 12 and event_time.month == 1:
            event_time = event_time.replace(year=cur_year + 1)

        return event_time
