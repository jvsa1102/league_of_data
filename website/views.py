from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from . models import Team, Player, Scrim
from . import db
from watcher import watcher
from retriever import get_player_data, get_scrim_data, generate_profile, assign_ids, gold_graph, damage_graph, damage_per_gold_graph
import requests

views = Blueprint('views', __name__)

watcher = watcher
champion_list = requests.get(
    'http://ddragon.leagueoflegends.com/cdn/11.16.1/data/en_US/champion.json').json()

DB_POSITIONS = ['top_id', 'jungle_id', 'mid_id', 'adc_id', 'support_id']
POSICOES = ['Top', 'Jungle', 'Mid', 'Adc', 'Support']


@views.route('/')
def home():
    return redirect(url_for('views.teams'))


@views.route('/teams', methods=['GET', 'POST'])
@login_required
def teams():
    if request.method == 'POST':
        team = request.form.get('team')
        team_exists = Team.query.filter_by(name=team).first()
        if len(team) < 1:
            flash('O nome da equipe não pode ser vazio', 'error')
        elif team_exists and team_exists.user_id == current_user.id:
            flash('Já existe uma equipe com esse nome', 'error')
        else:
            new_team = Team(name=team, user_id=current_user.id)
            db.session.add(new_team)
            db.session.commit()
            flash('Equipe criada', 'sucesso')
    return render_template('teams.html', user=current_user)


@views.route('/scrims/<team_id>', methods=['GET'])
@login_required
def scrims(team_id):
    team = Team.query.filter_by(id=team_id).first()
    return render_template('scrims.html', user=current_user, team=team)


@views.route('/add-scrim/<team_id>', methods=['GET', 'POST'])
@login_required
def add_scrim(team_id):
    team = Team.query.filter_by(id=team_id).first()
    if request.method == 'POST':
        description = request.form.get('description')
        match_id = request.form.get('match_id')
        if not match_id.isnumeric():
            aux = match_id.split('/')[::-1]
            match_id = aux[1]
        top_id = request.form.get('top_id')
        jungle_id = request.form.get('jungle_id')
        mid_id = request.form.get('mid_id')
        adc_id = request.form.get('adc_id')
        support_id = request.form.get('support_id')
        side = request.form.get('side')
        new_scrim = Scrim(
            team_id=team_id,
            description=description,
            match_id=match_id,
            top_id=top_id,
            jungle_id=jungle_id,
            mid_id=mid_id,
            adc_id=adc_id,
            support_id=support_id,
            side=side
        )
        db.session.add(new_scrim)
        db.session.commit()
        flash('Scrim adicionada', 'sucesso')
        return redirect(url_for('views.scrims', team_id=team.id))
    return render_template('add-scrim.html', user=current_user, team=team)


@views.route('/edit-scrim/<scrim_id>', methods=['GET', 'POST'])
@login_required
def edit_scrim(scrim_id):
    scrim = Scrim.query.filter_by(id=scrim_id).first()
    team = Team.query.filter_by(id=scrim.team_id).first()
    if request.method == 'POST':
        description = request.form.get('description')
        match_id = request.form.get('match_id')
        if not match_id.isnumeric():
            aux = match_id.split('/')[::-1]
            match_id = aux[1]
        top_id = request.form.get('top_id')
        jungle_id = request.form.get('jungle_id')
        mid_id = request.form.get('mid_id')
        adc_id = request.form.get('adc_id')
        support_id = request.form.get('support_id')
        side = request.form.get('side')

        scrim.description = description
        scrim.match_id = match_id
        scrim.top_id = top_id
        scrim.jungle_id = jungle_id
        scrim.mid_id = mid_id
        scrim.adc_id = adc_id
        scrim.support_id = support_id
        scrim.side = side

        db.session.add(scrim)
        db.session.commit()
        flash('Scrim adicionada', 'sucesso')
        return redirect(url_for('views.scrims', team_id=team.id))
    return render_template(
        'edit-scrim.html', user=current_user, team=team, scrim=scrim)


@views.route('/delete-scrim/<scrim_id>')
@login_required
def delete_scrim(scrim_id):
    scrim = Scrim.query.filter_by(id=scrim_id).first()
    if not scrim:
        flash("A scrim não existe.", category='error')
    else:
        db.session.delete(scrim)
        db.session.commit()
        flash('Scrim deletada.', category='success')

    return redirect(url_for('views.scrims', team_id=scrim.team_id))


@views.route('/scrim-data/<scrim_id>')
@login_required
def scrim_data(scrim_id):
    scrim = Scrim.query.filter_by(id=scrim_id).first()
    team = Team.query.filter_by(id=scrim.team_id).first()
    data = get_scrim_data(scrim.match_id, watcher)
    assign_ids(scrim, data)
    blue_labels, red_labels, blue_values, red_values = damage_graph(data["blue_team"]["players"], data["red_team"]["players"])
    blue_gold_values, red_gold_values = gold_graph(data["blue_team"]["players"], data["red_team"]["players"])
    blue_dmg_gold_values, red_dmg_gold_values = damage_per_gold_graph(blue_values, blue_gold_values, red_values, red_gold_values)
    all_labels = []
    for i in range(5):
        all_labels.insert(i, (f'{blue_labels[i]}/{red_labels[i]}'))
    return render_template(
        'scrim-data.html', user=current_user, data=data,
        team=team, champion_list=champion_list, scrim=scrim,
        blue_labels=blue_labels, blue_values=blue_values,
        red_labels=red_labels, red_values=red_values,
        blue_gold_values=blue_gold_values, red_gold_values=red_gold_values,
        blue_dmg_gold_values=blue_dmg_gold_values, red_dmg_gold_values=red_dmg_gold_values,
        all_labels=all_labels, posicoes=POSICOES)


@views.route('/delete-team/<id>')
@login_required
def delete_team(id):
    team = Team.query.filter_by(id=id).first()
    if not team:
        flash("O time não existe.", category='error')
    elif current_user.id != team.user_id:
        flash('Sem permissão para deletar este time.', category='error')
    else:
        for player in team.players:
            db.session.delete(player)
        for scrim in team.scrims:
            db.session.delete(scrim)
        db.session.delete(team)
        db.session.commit()
        flash('Time deletado.', category='success')

    return redirect(url_for('views.teams'))


@views.route('/edit-team/<id>', methods=['GET'])
@login_required
def edit_team(id):
    team = Team.query.filter_by(id=id).first()
    return render_template('edit-team.html', user=current_user, team=team)


@views.route('/add-player/<id>', methods=['GET', 'POST'])
@login_required
def add_player(id):
    team = Team.query.filter_by(id=id).first()
    if request.method == 'POST':
        name = request.form.get('name')
        summoner_name = request.form.get('summoner_name')
        position = request.form.get('position')
        player_exists = Player.query.filter_by(
            summoner_name=summoner_name).first()

        if len(summoner_name) < 1 or len(name) < 1:
            flash('O nome do jogador não pode ser vazio', 'error')
        elif player_exists and player_exists.team_id == team.id:
            flash('Já existe um jogador nesta equipe com este nome', 'error')
        else:
            new_player = Player(
                summoner_name=summoner_name,
                name=name, team_id=team.id,
                position=position)
            db.session.add(new_player)
            db.session.commit()
            flash('Jogador adicionado', 'sucesso')
            return redirect(url_for('views.edit_team', id=team.id))
    return render_template('add-player.html', user=current_user, team=team)


@views.route('/edit-player/<id>', methods=['GET', 'POST'])
@login_required
def edit_player(id):
    positions = ['top', 'jungle', 'mid', 'adc', 'support']
    name = request.form.get('name')
    summoner_name = request.form.get('summoner_name')
    position = request.form.get('position')
    player = Player.query.filter_by(id=id).first()
    team = Team.query.filter_by(id=player.team_id).first()
    if request.method == 'POST':
        if len(summoner_name) < 1 or len(name) < 1:
            flash('O nome do jogador não pode ser vazio', 'error')
        else:
            player.name = name
            player.summoner_name = summoner_name
            player.position = position
            db.session.add(player)
            db.session.commit()
            flash('Jogador alterado', 'sucesso')
            return redirect(url_for('views.edit_team', id=player.team_id))
    return render_template(
        'edit-player.html',
        user=current_user,
        positions=positions,
        player=player, team=team)


@views.route('/delete-player/<id>')
@login_required
def delete_player(id):
    player = Player.query.filter_by(id=id).first()
    team = Team.query.filter_by(id=player.team_id).first()
    if not player:
        flash("O jogador não existe.", category='error')
    elif current_user.id != team.user_id:
        flash('Sem permissão para deletar este jogador.', category='error')
    else:
        db.session.delete(player)
        db.session.commit()
        flash('Jogador deletado.', category='success')

    return redirect(url_for('views.edit_team', id=team.id))


@views.route('/profile/<id>')
@login_required
def profile(id):
    player = Player.query.filter_by(id=id).first()
    team = Team.query.filter_by(id=player.team_id).first()
    profile_data = get_player_data(player.summoner_name, watcher)
    mh_data, winrate = generate_profile(profile_data, watcher)
    winrate_pct = round(profile_data["wins"] / (profile_data["wins"] + profile_data["losses"]) * 100, 1)
    return render_template(
        'profile.html',
        user=current_user, player=player, team=team, profile_data=profile_data, mh_data=mh_data, winrate=winrate, winrate_pct=winrate_pct)
