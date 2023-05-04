import asyncio
import aiohttp
import os
from pathlib import Path

voobly_api_key = ""

async def single_req(url, session):
    print(url)
    async with session.get(url, ssl=False) as response:
        try:
            response = await response.text()
            # first line in a voobly response always contains the names of the data
            # and is not needed
            response = response.splitlines()[1:]
        except asyncio.TimeoutError:
            print('Timeout')
            await asyncio.sleep(1)
            response = await single_req(url, session)
        except Exception as e:
            print(f'Request failed with exception {e}')
            exit()
    return response

class player:
    def __init__(self, playerString, team) -> None:
        # name, god and color are extracted from data located in trigtemp file
        self.name, self.god, self.color = self.get_NameGodColor_from_playerString(playerString)
        self.team = team
        # the rest need to be extracted from ladderList or be fetched from voobly
        self.rating = None
        self.wins = None
        self.losses = None
        self.winRatio = None
        self.streak = None
        self.rank = None

    def get_NameGodColor_from_playerString(self, playerString):
        split_playerString = playerString.split('>')
        color_stringsList = split_playerString[0].split(',')
        nameGod_stringsList = split_playerString[1].split(' ')
        name = nameGod_stringsList[0]
        god = nameGod_stringsList[1].strip('(').strip(')')
        color = [float(x) for x in color_stringsList]
        return name, god, color

    # gets the player's voobly data
    async def get_vooblyData(self, ladderList, ladderID, session):
        # first search the ladderList for the player
        self.get_vooblyData_from_ladderList(ladderList)
        # if the player is found in ladderList(meaning rank <= 120) then all
        # voobly data(rating etc) are extracted from there
        if self.rank != '>120':
            return
        # if the player is not found(rank > 120) then the voobly data
        # need to be fetched seperately 
        await self.fetch_vooblyData(ladderID, session)

    # searches the ladderList, and if the player is found in it,
    # extracts the voobly data
    def get_vooblyData_from_ladderList(self, ladderList):
        # if a player's name contains the clan
        # search the ladderdist, ignoring the clan
        if ']' in self.name:
            nameWithoutClan = self.name.split(']')[1]
        else:
            nameWithoutClan = self.name
        for entry in ladderList:
            if f"{nameWithoutClan}," in entry:
                self.rank, self.rating, self.wins, self.losses, self.streak, self.winRatio = self.extract_vooblyData(entry)
                return
        self.rank = '>120'

    # fetches player's voobly data
    async def fetch_vooblyData(self, ladderID, session):
        # first find uid from name
        uid_url = f"http://www.voobly.com/api/finduser/{self.name}?key={voobly_api_key}"
        uid_resp = await single_req(uid_url, session)
        uid = uid_resp[0].split(',')[0]
        # use uid to find rating
        rating_url = f"https://www.voobly.com/api/ladder/{ladderID}?key={voobly_api_key}&uid={uid}"
        rating_resp = await single_req(rating_url, session)
        split_resp = rating_resp[0]

        _, self.rating, self.wins, self.losses, self.streak, self.winRatio = self.extract_vooblyData(split_resp)

    # extracts voobly data from a voobly response or a ladderList entry
    def extract_vooblyData(self, voobly_response):
        split_voobly_response = voobly_response.split(',')
        rank = split_voobly_response[0]
        rating = split_voobly_response[3]
        wins = int(split_voobly_response[4])
        losses = int(split_voobly_response[5])
        streak = int(split_voobly_response[6])
        winRatio = round(wins/(wins + losses) * 100, 2)
        return rank, rating, wins, losses, streak, winRatio

    # prints player's data
    def print(self):
        print(f"Name: {self.name}")
        print(f"\t God: {self.god}")
        print(f"\t Rank: #{self.rank}")
        print(f"\t Rating: {self.rating}")
        print(f"\t Wins: {self.wins}")
        print(f"\t Losses: {self.losses}")
        print(f"\t Win Ratio: {self.winRatio} %")
        print(f"\t Streak: {self.streak}")
        print(f"\t Color: R: {self.color[0]} G: {self.color[1]} B: {self.color[2]}")
 

class game:
    def __init__(self, map, numTeams, playerStrings) -> None:
        self.map = map
        self.numTeams = int(numTeams)
        self.TeamGame = self.isTeamGame(playerStrings)
        self.playersList = asyncio.run(self.create_playersList(playerStrings))

    # returns True if it is a TeamGame
    def isTeamGame(self, playersList):
        if len(playersList[0]) == 1:
            return False
        return True

    def get_ladderID(self):
        # if it's a TeamGame, get TeamGame rating
        # otherwise get 1v1 rating
        if self.TeamGame:
            return 327
        return 326

    # creates a list with player objects, given a list containing
    # a playerString string for each player
    async def create_playersList(self, playerStrings):
        api_tasks = []
        playersList = playerStrings.copy()
        ladderID = self.get_ladderID()

        # get top 120 ladder
        async with aiohttp.ClientSession() as session:

            # 3 coroutines to get top 120 players
            # each one returns 40 players
            list40_cor = single_req(f"https://www.voobly.com/api/ladder/{ladderID}?key={voobly_api_key}&start=0", session)
            list80_cor = single_req(f"https://www.voobly.com/api/ladder/{ladderID}?key={voobly_api_key}&start=40", session)
            list120_cor = single_req(f"https://www.voobly.com/api/ladder/{ladderID}?key={voobly_api_key}&start=80", session)

            list40, list80, list120 = await asyncio.gather(list40_cor, list80_cor, list120_cor)

            # merge in a single list
            ladderList = list40 + list80 + list120

            for countTeam, teamList in enumerate(playerStrings):
                for countPlayer, playerString in enumerate(teamList):
                    _player = player(playerString, countTeam)
                    api_tasks.append(asyncio.create_task(_player.get_vooblyData(ladderList, ladderID, session)))
                    playersList[countTeam][countPlayer] = _player
            await asyncio.gather(*api_tasks)

        return playersList

    # prints all of the game's data
    def print(self):
        print(f"Map: {self.map}")
        print("Players:")
        for countTeam, teamList in enumerate(self.playersList):
            for player in teamList:
                player.print()
            if countTeam < self.numTeams - 1:
                print("----- vs. -----")

class parser:
    def __init__(self, filePath) -> None:
        self.filePath = filePath
        self.fileData = None
        self.gameLines = None
        self.fileValid = None
        self.dateFileCreated = None
        self.fileNotLoaded, self.fileLoaded = 0, 1

    def isFileValid(self, fileData):
        if(self.get_line(fileData, "Voobly")):
            return True
        return False

    def isFileDifferent(self, date):
        return date != self.dateFileCreated

    # loads whole file
    # before loading the file, it checks if
    # the file is different and if it is valid.
    # returns True if the file is loaded
    def load_file(self):
        with open(self.filePath) as file:
            fileData = file.readlines()
            dateFileCreated = os.path.getmtime(self.filePath)
            if self.isFileValid(fileData) and self.isFileDifferent(dateFileCreated):
                self.fileData = fileData
                self.dateFileCreated = dateFileCreated
                return self.fileLoaded
        return self.fileNotLoaded

    # searches for a line, that contains the given string
    def get_line(self, lines, string):
        for line in lines:
            if string in line:
                return line
        return None

    # extracts the lines of the players from fileData
    def get_gameLines(self):
        assert isinstance(self.fileData, list)
        start_idx = None
        end_idx = None
        for count, line in enumerate(self.fileData):
            if 'Voobly Balance Patch' in line:
                start_idx = count
            elif 'trSoundPlayFN' in line or 'Observer' in line:
                end_idx = count
                break
        assert start_idx
        assert end_idx
        self.gameLines = self.fileData[start_idx + 1 : end_idx]

    # returns the substring of a line inbetween 2 symbols
    def extract_substring(self, line, start_symbol, end_symbol):
        start_idx = line.find(start_symbol) + 1
        end_idx = line.rfind(end_symbol)
        return line[start_idx:end_idx]
 
    # gets the map of the game
    def get_map(self):
        assert self.gameLines is not None
        map_line = self.gameLines[0]
        map = self.extract_substring(map_line, '>', '<')
        return map
 
    # gets the string that contains name, god & color of a player from a playerLine
    def get_playerString(self, playerLine):
        playerString = self.extract_substring(playerLine, '=', '<')
        return playerString

    # gets a playerString from every playerLine
    def get_playerStrings(self):
        playerStrings = []
        # list for players of the same team
        teamSubList = []
        assert self.gameLines
        for line in self.gameLines[1:]:
            if ' vs. ' not in line:
                teamSubList.append(self.get_playerString(line))
            else:
                playerStrings.append(teamSubList)
                teamSubList = []
        playerStrings.append(teamSubList)
        return playerStrings

    # gets the number of teams
    def get_numTeams(self):
        assert self.fileData is not None
        numTeamsLine = self.get_line(self.fileData, 'cTeams')
        numTeams = self.extract_substring(numTeamsLine, '=', '/').strip(' ').strip(';')
        return numTeams
 
def create_game(_parser):
    _parser.get_gameLines()
    map = _parser.get_map()
    num_teams = _parser.get_numTeams()
    playerStrings = _parser.get_playerStrings()
    _game = game(map, num_teams, playerStrings)
    return _game

def main():
    filePath = f"{Path.home()}/Documents/My Games/Age of Mythology/trigger2/trigtemp.xs"
    _parser = parser(filePath)
    if _parser.load_file() == _parser.fileLoaded:
        _game = create_game(_parser)
        _game.print()

if __name__ == '__main__':
    main()
