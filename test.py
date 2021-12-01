from watcher import watcher
from retriever import get_scrim_data, generate_profile, get_player_data
import requests


data = get_scrim_data(2296566455, watcher)

player = get_player_data('SOuPlatinaDes2', watcher)

champion_list = requests.get(
    'http://ddragon.leagueoflegends.com/cdn/11.16.1/data/en_US/champion.json'
).json()

spell_list = requests.get(
    'http://ddragon.leagueoflegends.com/cdn/11.16.1/data/en_US/summoner.json'
).json()


def print_team():
    for team in data["teams"]:
        print(f'Id:{team["teamId"]}')
        print(f'Win:{team["win"]}')
        for ban in team["bans"]:
            print(f'Ban:{ban["championId"]}')
        print('')
# full_data = watcher.match.by_id('br1', 2296567026)


print(generate_profile(player, watcher))
