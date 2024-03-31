from app import db
from flask_login import UserMixin

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(20), nullable=False)
    role = db.Column(db.String(20), default='user') 
    playlists = db.relationship('Playlist', backref='user', lazy='dynamic')
    songs = db.relationship('Song', backref='user', lazy=True)

    def get_id(self):
        return str(self.id)
    
    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        return True
    
class Admin(db.Model,UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    
    def get_id(self):
        return str(self.id)
    
    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        return True
    

class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    singer = db.Column(db.String(20), nullable=False)
    release_date = db.Column(db.Date, nullable=False)
    lyrics = db.Column(db.Text)
    album_id = db.Column(db.Integer, db.ForeignKey('album.id')) 
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ratings = db.relationship('SongRating', backref='song', lazy=True,cascade='all, delete-orphan')
    genre = db.Column(db.String(50), nullable=False)  
    audio_file = db.Column(db.String(100), nullable=False)
    is_hidden = db.Column(db.Boolean, default=False)

class Album(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    release_date = db.Column(db.Date, nullable=False)
    songs = db.relationship('Song', backref='album', lazy=True)    
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) 


class SongRating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('song.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)


playlist_song = db.Table('playlist_song',
    db.Column('playlist_id', db.Integer, db.ForeignKey('playlist.id')),
    db.Column('song_id', db.Integer, db.ForeignKey('song.id'))
)

class Playlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    songs = db.relationship('Song', secondary=playlist_song, backref='playlists', lazy='dynamic')