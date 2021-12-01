from . import db
from flask_login import UserMixin


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(40))
    username = db.Column(db.String(40))
    teams = db.relationship('Team', passive_deletes=True)


class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60))
    summoner_name = db.Column(db.String(60))
    position = db.Column(db.String(30))
    team_id = db.Column(db.Integer, db.ForeignKey(
        'team.id', ondelete='CASCADE'))


class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True)
    players = db.relationship('Player', passive_deletes=True)
    scrims = db.relationship('Scrim', passive_deletes=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey(
            'user.id', ondelete='CASCADE'))


class Scrim(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(100))

    match_id = db.Column(db.String(60))

    side = db.Column(db.String(10))

    team_id = db.Column(db.Integer, db.ForeignKey(
        'team.id', ondelete='CASCADE'))
    top_id = db.Column(db.Integer, db.ForeignKey(
        'player.id', ondelete='CASCADE'))
    jungle_id = db.Column(db.Integer, db.ForeignKey(
        'player.id', ondelete='CASCADE'))
    mid_id = db.Column(db.Integer, db.ForeignKey(
        'player.id', ondelete='CASCADE'))
    adc_id = db.Column(db.Integer, db.ForeignKey(
        'player.id', ondelete='CASCADE'))
    support_id = db.Column(db.Integer, db.ForeignKey(
        'player.id', ondelete='CASCADE'))
