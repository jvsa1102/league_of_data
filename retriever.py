import requests
import datetime

ROLES = ['DUO', 'NONE', 'SOLO', 'DUO_CARRY', 'DUO_SUPPORT']
LANES = ['MIDDLE', 'TOP', 'JUNGLE', 'BOTTOM']
POSITIONS = ['TOP', 'JUNGLE', 'MIDDLE', 'DUO_CARRY', 'DUO_SUPPORT']
DB_POSITIONS = ['top_id', 'jungle_id', 'mid_id', 'adc_id', 'support_id']
POSICOES = ['Top', 'Jungle', 'Mid', 'Adc', 'Support']
champion_list = requests.get(
    'http://ddragon.leagueoflegends.com/cdn/11.16.1/data/en_US/champion.json').json()


def get_player_data(summoner_name, watcher):
    summoner_data = watcher.summoner.by_name('br1', summoner_name)
    ranked_data = watcher.league.by_summoner('br1', summoner_data['id'])
    player_data = {
        'id': summoner_data['id'],
        'accountId': summoner_data['accountId'],
        'profileIconId': summoner_data['profileIconId'],
        'name': summoner_data['name'],
        'summonerLevel': summoner_data['summonerLevel'],
        'elo': ranked_data[0]['tier'] + ' ' + ranked_data[0]['rank'],
        'lp': ranked_data[0]['leaguePoints'],
        'wins': ranked_data[0]['wins'],
        'losses': ranked_data[0]['losses'],
    }
    return player_data


def generate_profile(player_data, watcher):
    mh = get_match_history(player_data["name"], watcher)
    mh_data = []
    for match in mh:
        match_data = get_match_data(match["gameId"], watcher)
        aux = format_match_data(player_data["accountId"], match_data)
        aux["champion"] = find_champion(aux["championId"])
        aux["championIcon"] = find_champion_icon(aux["champion"])
        aux["spell1Icon"] = find_spell_icon(aux["spell1Id"])
        aux["spell2Icon"] = find_spell_icon(aux["spell2Id"])
        timestamp = datetime.datetime.fromtimestamp(match_data["gameCreation"] / 1000)
        date_str = timestamp.strftime("%d/%m/%Y - %H:%M")
        aux["gameCreation"] = date_str
        aux["gameDuration"] = calculate_duration(match_data["gameDuration"])
        find_items_icons_solo(aux)
        mh_data.append(aux)
    winrate = [0, 0]
    for match in mh_data:
        if match["win"] == "Win":
            winrate[0] += 1
        else:
            winrate[1] += 1
    return mh_data, winrate


def format_match_data(accountId, data):
    # find Id
    for p in data["participantIdentities"]:
        if p["player"]["accountId"] == accountId:
            participantId = p["participantId"]
    # find player
    for p in data["participants"]:
        if p["participantId"] == participantId:
            player = p
    # find team and winner
    for team in data["teams"]:
        if team["teamId"] == player["teamId"]:
            player["win"] = team["win"]

    return player


def get_match_history(summoner_name, watcher):
    summoner_data = get_player_data(summoner_name, watcher)
    matches = watcher.match_v4.matchlist_by_account('br1', summoner_data['accountId'], queue=420, season=13)
    match_history = []
    for i in range(10):
        match_history.append(matches["matches"][i])
    return match_history


def get_match_data(matchId, watcher):
    data = watcher.match.by_id('br1', matchId)
    return data


def get_scrim_data(matchId, watcher):
    data = watcher.match.by_id('br1', matchId)
    f_data = {
        "game": {},
        "blue_team": {},
        "red_team": {}
    }

    f_data["game"]["duration"] = calculate_duration(data["gameDuration"])
    f_data["game"]["durationNum"] = data["gameDuration"] / 60
    f_data["game"]["patch"] = data["gameVersion"][0:5]
    f_data["blue_team"] = data["teams"][0]
    f_data["red_team"] = data["teams"][1]

    find_team_bans(f_data["blue_team"]["bans"])
    find_team_bans(f_data["red_team"]["bans"])

    format_players(data, f_data)

    find_items_icons(f_data["blue_team"]["players"], f_data["red_team"]["players"])

    calculate_totals(f_data)

    return f_data


def format_players(data, f_data):
    f_data["blue_team"]["players"] = []
    f_data["red_team"]["players"] = []

    for p in data["participants"]:
        if p["teamId"] == 100:
            p["champion"] = find_champion(p["championId"])
            p["championIcon"] = find_champion_icon(p["champion"])
            p["spell1Icon"] = find_spell_icon(p["spell1Id"])
            p["spell2Icon"] = find_spell_icon(p["spell2Id"])
            p["position"] = find_real_position(p)
            p["stats"]["csMin"] = round((p["stats"]["totalMinionsKilled"] + p["stats"]["neutralMinionsKilled"]) / f_data["game"]["durationNum"], 1)
            f_data["blue_team"]["players"].append(p)
        else:
            p["champion"] = find_champion(p["championId"])
            p["championIcon"] = find_champion_icon(p["champion"])
            p["spell1Icon"] = find_spell_icon(p["spell1Id"])
            p["spell2Icon"] = find_spell_icon(p["spell2Id"])
            p["position"] = find_real_position(p)
            p["stats"]["csMin"] = round((p["stats"]["totalMinionsKilled"] + p["stats"]["neutralMinionsKilled"]) / f_data["game"]["durationNum"], 1)
            f_data["red_team"]["players"].append(p)


def find_real_position(p):
    for pos in POSITIONS:
        if p["timeline"]["role"] == pos or p["timeline"]["lane"] == pos:
            if pos == 'DUO_CARRY':
                return 'adc'
            elif pos == 'DUO_SUPPORT':
                return 'support'
            elif pos == 'MIDDLE':
                return 'mid'
            else:
                return pos.lower()


def find_team_bans(team_bans):
    for ban in team_bans:
        ban["champion"] = find_champion(ban["championId"])
        ban["championIcon"] = find_champion_icon(ban["champion"])


def calculate_totals(f_data):
    blueTotKills = 0
    blueTotDeaths = 0
    blueTotAssists = 0

    redTotKills = 0
    redTotDeaths = 0
    redTotAssists = 0

    for p in f_data["blue_team"]["players"]:
        blueTotKills += p["stats"]["kills"]
        blueTotDeaths += p["stats"]["deaths"]
        blueTotAssists += p["stats"]["assists"]
    for p in f_data["red_team"]["players"]:
        redTotKills += p["stats"]["kills"]
        redTotDeaths += p["stats"]["deaths"]
        redTotAssists += p["stats"]["assists"]

    f_data["blue_team"]["totalKills"] = blueTotKills
    f_data["blue_team"]["totalDeaths"] = blueTotDeaths
    f_data["blue_team"]["totalAssists"] = blueTotAssists
    f_data["red_team"]["totalKills"] = redTotKills
    f_data["red_team"]["totalDeaths"] = redTotDeaths
    f_data["red_team"]["totalAssists"] = redTotAssists


def calculate_duration(seconds):
    minutes = seconds // 60
    new_seconds = seconds % 60
    if new_seconds < 10:
        new_seconds = f'0{new_seconds}'
    duration = f'{minutes}:{new_seconds}'
    return duration


def find_champion(championId):
    champion_list = requests.get(
        'http://ddragon.leagueoflegends.com/cdn/11.16.1/data/en_US/champion.json'
    ).json()

    for key, value in champion_list["data"].items():
        if value["key"] == str(championId):
            champion = key
    return champion


def find_champion_icon(champion):
    icon_link = f'http://ddragon.leagueoflegends.com/cdn/11.16.1/img/champion/{champion}.png'
    return icon_link


def find_spell_icon(spellId):
    spell_list = requests.get(
        'http://ddragon.leagueoflegends.com/cdn/11.16.1/data/en_US/summoner.json'
    ).json()
    for key, value in spell_list["data"].items():
        if value["key"] == str(spellId):
            spell_name = key

    icon_link = f'http://ddragon.leagueoflegends.com/cdn/11.16.1/img/spell/{spell_name}.png'
    return icon_link


def find_items_icons(blue_players, red_players):
    for p in blue_players:
        p["stats"]["item0icon"] = f'http://ddragon.leagueoflegends.com/cdn/11.16.1/img/item/{p["stats"]["item0"]}.png'
        p["stats"]["item1icon"] = f'http://ddragon.leagueoflegends.com/cdn/11.16.1/img/item/{p["stats"]["item1"]}.png'
        p["stats"]["item2icon"] = f'http://ddragon.leagueoflegends.com/cdn/11.16.1/img/item/{p["stats"]["item2"]}.png'
        p["stats"]["item3icon"] = f'http://ddragon.leagueoflegends.com/cdn/11.16.1/img/item/{p["stats"]["item3"]}.png'
        p["stats"]["item4icon"] = f'http://ddragon.leagueoflegends.com/cdn/11.16.1/img/item/{p["stats"]["item4"]}.png'
        p["stats"]["item5icon"] = f'http://ddragon.leagueoflegends.com/cdn/11.16.1/img/item/{p["stats"]["item5"]}.png'
        p["stats"]["item6icon"] = f'http://ddragon.leagueoflegends.com/cdn/11.16.1/img/item/{p["stats"]["item6"]}.png'
    for p in red_players:
        p["stats"]["item0icon"] = f'http://ddragon.leagueoflegends.com/cdn/11.16.1/img/item/{p["stats"]["item0"]}.png'
        p["stats"]["item1icon"] = f'http://ddragon.leagueoflegends.com/cdn/11.16.1/img/item/{p["stats"]["item1"]}.png'
        p["stats"]["item2icon"] = f'http://ddragon.leagueoflegends.com/cdn/11.16.1/img/item/{p["stats"]["item2"]}.png'
        p["stats"]["item3icon"] = f'http://ddragon.leagueoflegends.com/cdn/11.16.1/img/item/{p["stats"]["item3"]}.png'
        p["stats"]["item4icon"] = f'http://ddragon.leagueoflegends.com/cdn/11.16.1/img/item/{p["stats"]["item4"]}.png'
        p["stats"]["item5icon"] = f'http://ddragon.leagueoflegends.com/cdn/11.16.1/img/item/{p["stats"]["item5"]}.png'
        p["stats"]["item6icon"] = f'http://ddragon.leagueoflegends.com/cdn/11.16.1/img/item/{p["stats"]["item6"]}.png'


def find_items_icons_solo(p):
    p["stats"]["item0icon"] = f'http://ddragon.leagueoflegends.com/cdn/11.16.1/img/item/{p["stats"]["item0"]}.png'
    p["stats"]["item1icon"] = f'http://ddragon.leagueoflegends.com/cdn/11.16.1/img/item/{p["stats"]["item1"]}.png'
    p["stats"]["item2icon"] = f'http://ddragon.leagueoflegends.com/cdn/11.16.1/img/item/{p["stats"]["item2"]}.png'
    p["stats"]["item3icon"] = f'http://ddragon.leagueoflegends.com/cdn/11.16.1/img/item/{p["stats"]["item3"]}.png'
    p["stats"]["item4icon"] = f'http://ddragon.leagueoflegends.com/cdn/11.16.1/img/item/{p["stats"]["item4"]}.png'
    p["stats"]["item5icon"] = f'http://ddragon.leagueoflegends.com/cdn/11.16.1/img/item/{p["stats"]["item5"]}.png'
    p["stats"]["item6icon"] = f'http://ddragon.leagueoflegends.com/cdn/11.16.1/img/item/{p["stats"]["item6"]}.png'


def assign_ids(scrim, data):
    if scrim.side == 'blue':
        for p in data["blue_team"]["players"]:
            if p["position"] == 'top':
                p["playerId"] = scrim.top_id
            elif p["position"] == 'jungle':
                p["playerId"] = scrim.jungle_id
            elif p["position"] == 'mid':
                p["playerId"] = scrim.mid_id
            elif p["position"] == 'adc':
                p["playerId"] = scrim.adc_id
            elif p["position"] == 'support':
                p["playerId"] = scrim.support_id
        data["blue_team"]["show_players"] = True
        data["red_team"]["show_players"] = False
    else:
        for p in data["red_team"]["players"]:
            if p["position"] == 'top':
                p["playerId"] = scrim.top_id
            elif p["position"] == 'jungle':
                p["playerId"] = scrim.jungle_id
            elif p["position"] == 'mid':
                p["playerId"] = scrim.mid_id
            elif p["position"] == 'adc':
                p["playerId"] = scrim.adc_id
            elif p["position"] == 'support':
                p["playerId"] = scrim.support_id
        data["blue_team"]["show_players"] = False
        data["red_team"]["show_players"] = True


def damage_graph(blue_players, red_players):
    data_blue = [('foo', 'foo'), ('foo', 'foo'), ('foo', 'foo'), ('foo', 'foo'), ('foo', 'foo')]
    data_red = [('foo', 'foo'), ('foo', 'foo'), ('foo', 'foo'), ('foo', 'foo'), ('foo', 'foo')]
    for b in blue_players:
        if b["position"] == 'top':
            data_blue.pop(0)
            data_blue.insert(0, (b["champion"], b["stats"]["totalDamageDealtToChampions"], b["position"]))
        elif b["position"] == 'jungle':
            data_blue.pop(1)
            data_blue.insert(1, (b["champion"], b["stats"]["totalDamageDealtToChampions"], b["position"]))
        elif b["position"] == 'mid':
            data_blue.pop(2)
            data_blue.insert(2, (b["champion"], b["stats"]["totalDamageDealtToChampions"], b["position"]))
        elif b["position"] == 'adc':
            data_blue.pop(3)
            data_blue.insert(3, (b["champion"], b["stats"]["totalDamageDealtToChampions"], b["position"]))
        elif b["position"] == 'support':
            data_blue.pop(4)
            data_blue.insert(4, (b["champion"], b["stats"]["totalDamageDealtToChampions"], b["position"]))
    for r in red_players:
        if r["position"] == 'top':
            data_red.pop(0)
            data_red.insert(0, (r["champion"], r["stats"]["totalDamageDealtToChampions"], r["position"]))
        elif r["position"] == 'jungle':
            data_red.pop(1)
            data_red.insert(1, (r["champion"], r["stats"]["totalDamageDealtToChampions"], r["position"]))
        elif r["position"] == 'mid':
            data_red.pop(2)
            data_red.insert(2, (r["champion"], r["stats"]["totalDamageDealtToChampions"], r["position"]))
        elif r["position"] == 'adc':
            data_red.pop(3)
            data_red.insert(3, (r["champion"], r["stats"]["totalDamageDealtToChampions"], r["position"]))
        elif r["position"] == 'support':
            data_red.pop(4)
            data_red.insert(4, (r["champion"], r["stats"]["totalDamageDealtToChampions"], r["position"]))

    blue_labels = [row[0] for row in data_blue]
    blue_damage_values = [row[1] for row in data_blue]
    red_labels = [row[0] for row in data_red]
    red_damage_values = [row[1] for row in data_red]
    return blue_labels, red_labels, blue_damage_values, red_damage_values


def gold_graph(blue_players, red_players):
    data_blue = [('foo', 'foo'), ('foo', 'foo'), ('foo', 'foo'), ('foo', 'foo'), ('foo', 'foo')]
    data_red = [('foo', 'foo'), ('foo', 'foo'), ('foo', 'foo'), ('foo', 'foo'), ('foo', 'foo')]
    for b in blue_players:
        if b["position"] == 'top':
            data_blue.pop(0)
            data_blue.insert(0, (b["champion"], b["stats"]["goldEarned"], b["position"]))
        elif b["position"] == 'jungle':
            data_blue.pop(1)
            data_blue.insert(1, (b["champion"], b["stats"]["goldEarned"], b["position"]))
        elif b["position"] == 'mid':
            data_blue.pop(2)
            data_blue.insert(2, (b["champion"], b["stats"]["goldEarned"], b["position"]))
        elif b["position"] == 'adc':
            data_blue.pop(3)
            data_blue.insert(3, (b["champion"], b["stats"]["goldEarned"], b["position"]))
        elif b["position"] == 'support':
            data_blue.pop(4)
            data_blue.insert(4, (b["champion"], b["stats"]["goldEarned"], b["position"]))
    for r in red_players:
        if r["position"] == 'top':
            data_red.pop(0)
            data_red.insert(0, (r["champion"], r["stats"]["goldEarned"], r["position"]))
        elif r["position"] == 'jungle':
            data_red.pop(1)
            data_red.insert(1, (r["champion"], r["stats"]["goldEarned"], r["position"]))
        elif r["position"] == 'mid':
            data_red.pop(2)
            data_red.insert(2, (r["champion"], r["stats"]["goldEarned"], r["position"]))
        elif r["position"] == 'adc':
            data_red.pop(3)
            data_red.insert(3, (r["champion"], r["stats"]["goldEarned"], r["position"]))
        elif r["position"] == 'support':
            data_red.pop(4)
            data_red.insert(4, (r["champion"], r["stats"]["goldEarned"], r["position"]))

    # blue_labels = [row[0] for row in data_blue]
    blue_gold_values = [row[1] for row in data_blue]
    # red_labels = [row[0] for row in data_red]
    red_gold_values = [row[1] for row in data_red]
    return blue_gold_values, red_gold_values


def damage_per_gold_graph(blue_damage_values, blue_gold_values, red_damage_values, red_gold_values):
    blue_damage_per_gold = []
    red_damage_per_gold = []
    for i in range(5):
        blue_damage_per_gold.append(blue_damage_values[i] / blue_gold_values[i])
        red_damage_per_gold.append(red_damage_values[i] / red_gold_values[i])
    return blue_damage_per_gold, red_damage_per_gold
