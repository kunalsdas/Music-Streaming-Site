from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, current_user, login_required, logout_user
from app import app,  db, login_manager
from forms import UserRegistrationForm, UserLoginForm, AdminLoginForm, SongForm, AlbumForm,SongRatingForm,PlaylistForm
from models import User, Role, Admin, Song, Album,SongRating,Playlist, Admin
from sqlalchemy import func,desc,or_
from werkzeug.utils import secure_filename
import os

#Redirect to specific dashboard based on logged in
@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'user':
            return redirect(url_for('user_dashboard'))
        elif current_user.role == 'creator':
            return redirect(url_for('creator_dashboard'))
        elif current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
    return render_template('index.html')

#These functions load the respective user objects based on the given ID or return None if not found.
@login_manager.user_loader
def load_admin(admin_id):
    if admin_id is not None:
        return Admin.query.get(admin_id)
    return None

@login_manager.user_loader
def load_user(user_id):
    if user_id is not None:
        return User.query.get(user_id)
    return None

'''
Create admin username and password manually from "flask shell"

from models import Admin
from app import db
admin_user = Admin(username='admin', password='admin')
db.session.add(admin_user)
db.session.commit()
'''

#Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('user_dashboard'))
    form = UserRegistrationForm()
    if form.validate_on_submit():
        try:
            role = Role.query.filter_by(name='User').first()
            user = User(username=form.username.data, email=form.email.data, password=form.password.data, role=role)
            db.session.add(user)
            db.session.commit()
            flash('Your account has been created!', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')

    return render_template('register.html', title='Register', form=form)

#Admin Login
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated and isinstance(current_user, Admin):
        return redirect(url_for('admin_dashboard'))
    form = AdminLoginForm()
    if form.validate_on_submit():
        if form.username.data == 'admin' and form.password.data == 'admin':
            admin_user = Admin.query.filter_by(username='admin').first()
            if admin_user:
                login_user(admin_user)
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Incorrect credentials.', 'danger')
        else:
            flash('Incorrect credentials.', 'danger')
    return render_template('admin_login.html', title='Admin Login', form=form)

#User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('user_dashboard'))
    form = UserLoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.password == form.password.data:
            login_user(user)
            return redirect(url_for('user_dashboard'))
        else:
            flash('Login failed. Incorrect Username or Password.', 'danger')
    return render_template('login.html', title='Login', form=form)

# all about admin

#Admin Dashboard details
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    normal_user_count = User.query.filter_by(role='user').count()
    creator_count = User.query.filter_by(role='creator').count()
    total_songs = Song.query.count()
    total_albums = Album.query.count()
    songs = Song.query.all()
    unique_genres = set()
    for song in songs: 
        unique_genres.add(song.genre)

    total_genres = len(unique_genres)   
    return render_template('admin_dashboard.html', title='Admin Dashboard',normal_user_count=normal_user_count,creator_count=creator_count
                           ,total_songs=total_songs,total_albums=total_albums,total_genres=total_genres)

#Admin Song detail
@app.route('/song-detail/<int:song_id>', methods=['GET'])
@login_required
def admin_song_detail(song_id):
    song = Song.query.get(song_id)

    existing_rating = SongRating.query.filter_by(user_id=current_user.id, song_id=song_id).first()

    return render_template('admin_song_detail.html', title='Song Detail', song=song,existing_rating=existing_rating)

#Admin Albums Section
@app.route('/albums', methods=['GET'])
@login_required
def view_albums():
    albums = Album.query.all()
    songs = Song.query.all()
    return render_template('admin_albums.html', title='All Albums', albums=albums,songs=songs)

#Admin Songs Section with Search functionality present in table to get exact data based on search
@app.route('/admin/songs')
def admin_songs():
    search_term = request.args.get('search', '')   
    if search_term:
        songs = Song.query.filter(or_(Song.title.ilike(f'%{search_term}%'), Song.singer.ilike(f'%{search_term}%'))).all()
    else:
        songs = Song.query.all()
    return render_template('admin_songs.html', songs=songs)

#Admin Delete Song Functionality
@app.route('/admin/delete_song/<int:song_id>', methods=['POST'])
def admin_delete_song(song_id):
    song = Song.query.get(song_id)
    if song:
        SongRating.query.filter_by(song_id=song_id).delete()
        db.session.delete(song)
        db.session.commit()
        flash('Song deleted successfully!', 'success')
    else:
        flash('Song not found.', 'danger')
    return redirect(url_for('admin_songs'))

#Blacklist as a admin
@app.route('/blacklist', methods=['GET', 'POST'])
def blacklist():
    if request.method == 'POST':
        users_to_hide = request.form.getlist('hide_songs[]')

        for user_id in users_to_hide:
            user = User.query.get(user_id)
            if user:
                songs_to_toggle = Song.query.filter_by(creator_id=user_id).all()
                for song in songs_to_toggle:
                    song.is_hidden = True

        checked_users = request.form.getlist('hide_songs[]')
        all_creators = User.query.filter_by(role='creator').all()

        for user in all_creators:
            user.has_hidden_song = str(user.id) in checked_users

            songs_to_update = Song.query.filter_by(creator_id=user.id).all()
            for song in songs_to_update:
                song.is_hidden = user.has_hidden_song

        db.session.commit()
        return redirect(url_for('blacklist'))

    creators = User.query.filter_by(role='creator').all()
    for user in creators:
        user.has_hidden_song = any(song.is_hidden for song in user.songs)
    return render_template('blacklist.html', users=creators)

# End of Admin

#All about normal user 

#User dashboard details
@app.route('/user_dashboard', methods=['GET'])
@login_required
def user_dashboard():
    songs = Song.query.filter_by(is_hidden=False).all()
    albums = Album.query.all()
    playlists = Playlist.query.filter_by(user_id=current_user.id).all()    
    subquery = db.session.query(SongRating.song_id, func.avg(SongRating.rating).label('avg_rating')).group_by(SongRating.song_id).subquery()
    top_rated_songs = Song.query.join(subquery, Song.id == subquery.c.song_id).order_by(desc(subquery.c.avg_rating)).all()
    unique_genres = set()
    for song in songs:
        unique_genres.add(song.genre)
    search_query = request.args.get('search')
    if search_query:
        return redirect(url_for('search_results', search=search_query))
        
    return render_template('user_dashboard.html', title='User Dashboard', songs=songs,albums=albums,
                           playlists=playlists,top_rated_songs=top_rated_songs,
                           search_query=search_query,unique_genres=unique_genres
                          )

#Register as a Creator from Normal User
@app.route('/register_as_creator', methods=['GET'])
@login_required
def register_as_creator():
    if current_user.role == 'user':
        current_user.role = 'creator'
        db.session.commit()
        flash('You have been upgraded to a creator!', 'success')
    
    return redirect(url_for('creator_dashboard'))

#Search Result based on text provided
@app.route('/search_results', methods=['GET'])
@login_required
def search_results():
    search_query = request.args.get('search')
    if search_query:
        songs = Song.query.filter(
            (Song.title.ilike(f"%{search_query}%")) | (Song.singer.ilike(f"%{search_query}%"))
        ).all()
        return render_template('search_results.html', title='Search Results', songs=songs, search_query=search_query)
    else:
        # when search query is not provided
        return render_template('search_results.html', title='Search Results', songs=[], search_query=search_query)

#Profile Section to display user detail
@app.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    user = User.query.get(user_id)
    return render_template('profile.html', title='Profile', user=user)

#Songs present in selected Genre
@app.route('/genre/<selected_genre>', methods=['GET'])
@login_required
def genre_songs(selected_genre):
    songs_by_genre = Song.query.filter_by(genre=selected_genre).all()
    return render_template('genre_songs.html', title=f'{selected_genre} Songs', songs=songs_by_genre)

#Songs present in selected album
@app.route('/album_songs/<int:album_id>', methods=['GET'])
@login_required
def album_songs(album_id):
    album = Album.query.get(album_id)
    songs_in_album = Song.query.filter_by(album_id=album_id).all()
    return render_template('album_songs.html', title=f'{album.title} Songs', album=album, songs=songs_in_album)

#Upgrade to creator page
@app.route('/upgrade_to_creator', methods=['GET'])
@login_required
def upgrade_to_creator():
    return render_template('upgrade_to_creator.html', title='Upgrade to creator')

#View lyrics in Normal User dashboard
@app.route('/user/view_lyrics/<int:song_id>', methods=['GET'])
@login_required
def view_lyrics1(song_id):
    song = Song.query.get(song_id)
    return render_template('view_lyrics1.html', title='View Lyrics', song=song)


#Rate Song as a normal user
@app.route('/rate_song/<int:song_id>', methods=['GET', 'POST'])
@login_required
def rate_song(song_id):
    song = Song.query.get(song_id)
    form = SongRatingForm()

    # Check if the user has already rated this song
    existing_rating = SongRating.query.filter_by(user_id=current_user.id, song_id=song_id).first()

    if existing_rating:
        # If the user has already rated, prepopulate the form with their rating
        form = SongRatingForm(obj=existing_rating)

    if form.validate_on_submit():
        if existing_rating:
            # If the user has already rated, update the rating
            form.populate_obj(existing_rating)
            db.session.commit()
        else:
            # If the user hasn't rated, create a new rating
            new_rating = SongRating(user_id=current_user.id, song_id=song_id, rating=form.rating.data)
            db.session.add(new_rating)
            db.session.commit()

        flash('Rating submitted successfully!', 'success')
        return redirect(url_for('user_dashboard'))

    return render_template('rate_song.html', title='Rate Song', song=song, form=form)


#Create Playlist as a normal user
@app.route('/create_playlist', methods=['GET', 'POST'])
@login_required
def create_playlist():
    form = PlaylistForm()
    songs = Song.query.filter_by(is_hidden=False).all()
    playlist = None  

    if request.method == 'POST':
        # Check if the form is submitted for editing an existing playlist
        playlist_id = request.form.get('playlist_id')
        if playlist_id:
            playlist = Playlist.query.get(playlist_id)
            if playlist:
                playlist.title = form.title.data
                playlist.songs = Song.query.filter(Song.id.in_(request.form.getlist('songs')))
                db.session.commit()
                flash('Playlist edited successfully!', 'success')
                return redirect(url_for('user_dashboard'))
        
        # Create a new playlist
        playlist = Playlist(title=form.title.data, user_id=current_user.id)
        playlist.songs = Song.query.filter(Song.id.in_(request.form.getlist('songs')))
        db.session.add(playlist)
        db.session.commit()
        flash('Playlist created successfully!', 'success')
        return redirect(url_for('user_dashboard'))

    return render_template('create_playlist.html', title='Create Playlist', form=form, songs=songs, playlist=playlist)

#Delete Playlist as a normal user
@app.route('/delete_playlist/<int:playlist_id>', methods=['POST'])
@login_required
def delete_playlist(playlist_id):
    playlist = Playlist.query.get(playlist_id)
    if playlist and playlist.user_id == current_user.id:
        db.session.delete(playlist)
        db.session.commit()
        flash('Playlist deleted successfully!', 'success')
    return redirect(url_for('user_dashboard'))

#End of User 

#Logout functionality
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('index'))

#All about Creator

#Creator Dashboard
@app.route('/creator_dashboard', methods=['GET'])
@login_required
def creator_dashboard():
    if current_user.role == 'creator':
        songs = Song.query.filter_by(creator_id=current_user.id).all()
        albums = Album.query.filter_by(creator_id=current_user.id).all()
        total_songs = len(songs)
        total_albums = len(albums)
        total_ratings = 0
        for song in songs:
            ratings = SongRating.query.filter_by(song_id=song.id).all()
            if ratings:
                total_ratings += sum([rating.rating for rating in ratings])
        average_ratings = total_ratings / total_songs if total_songs > 0 else 0
        unique_genres = set()
        for song in songs: 
            unique_genres.add(song.genre)

        total_genres = len(unique_genres)        

        return render_template('creator_dashboard.html', title='Creator Dashboard', songs=songs, total_songs=total_songs, total_albums=total_albums, average_ratings=average_ratings,total_genres=total_genres)  # Pass the 'songs' variable
    return redirect(url_for('user_dashboard'))


#Add Song as a creator
@app.route('/add_song', methods=['GET', 'POST'])
@login_required
def add_song():
    if current_user.role == 'creator':
        form = SongForm()
        if form.validate_on_submit():
            audio = form.audio_file.data
            audio_filename = secure_filename(audio.filename)
            audio.save(os.path.join(app.config['UPLOAD_FOLDER'], audio_filename))
            song = Song(
                title=form.title.data,
                singer=form.singer.data,
                release_date=form.release_date.data,
                lyrics=form.lyrics.data,
                genre=form.genre.data,
                audio_file=audio_filename,
                creator_id=current_user.id  # Set the creator_id
            )
            db.session.add(song)
            db.session.commit()
            flash('Song added successfully!', 'success')
            return redirect(url_for('creator_dashboard'))
        return render_template('add_song.html', title='Add Song', form=form)
    else:
        return redirect(url_for('user_dashboard'))

#Edit Song as a creator
@app.route('/edit_song/<int:song_id>', methods=['GET', 'POST'])
@login_required
def edit_song(song_id):
    song = Song.query.get(song_id)
    
    if current_user.role == 'creator' and song.creator_id == current_user.id:
        form = SongForm(obj=song)
        if form.validate_on_submit():
            song.title = form.title.data
            song.singer = form.singer.data
            song.release_date = form.release_date.data
            song.lyrics = form.lyrics.data
            song.genre = form.genre.data
            audio = form.audio_file.data
            if audio:  # Check if file was uploaded
                audio_filename = secure_filename(audio.filename)
                audio.save(os.path.join(app.config['UPLOAD_FOLDER'], audio_filename))
                song.audio_file = audio_filename

            db.session.commit()
            flash('Song updated successfully!', 'success')
            return redirect(url_for('creator_dashboard'))
        return render_template('edit_song.html', title='Edit Song', form=form, song=song)
    else:
        return redirect(url_for('creator_dashboard'))

#Delete Song as a creator
@app.route('/delete_song/<int:song_id>', methods=['POST'])
@login_required
def delete_song(song_id):
    song = Song.query.get(song_id)

    if current_user.role == 'creator' and song.creator_id == current_user.id:
        db.session.delete(song)
        db.session.commit()
        flash('Song deleted successfully!', 'success')
        return redirect(url_for('creator_dashboard'))
    else:
        return redirect(url_for('creator_dashboard'))
    
#View Lyrics
@app.route('/view_lyrics/<int:song_id>', methods=['GET'])
@login_required
def view_lyrics(song_id):
    song = Song.query.get(song_id)
    return render_template('view_lyrics.html', title='View Lyrics', song=song)

#Add album as a creator
@app.route('/add_album', methods=['GET', 'POST'])
@login_required
def add_album():
    form = AlbumForm()
    form.songs.choices = [(song.id, song.title) for song in Song.query.filter_by(creator_id=current_user.id).all()]

    if form.validate_on_submit():
        album = Album(title=form.title.data, release_date=form.release_date.data,creator_id=current_user.id)
        selected_song_ids = form.songs.data 
        selected_songs = Song.query.filter(Song.id.in_(selected_song_ids)).all()
        album.songs.extend(selected_songs)
        db.session.add(album)
        db.session.commit()
        flash('Album added successfully!', 'success')
        return redirect(url_for('add_album'))
    
    albums = Album.query.all()
    
    return render_template('add_album.html', form=form, albums=albums)

#Edit Album as a creator
@app.route('/edit_album/<int:album_id>', methods=['GET', 'POST'])
@login_required
def edit_album(album_id):
    album = Album.query.get(album_id)
    if not album:
        flash('Album not found', 'danger')
        return redirect(url_for('creator_dashboard'))
    
    form = AlbumForm(obj=album)
    form.songs.choices = [(song.id, song.title) for song in Song.query.filter_by(creator_id=current_user.id).all()]

    if form.validate_on_submit():
        album.title = form.title.data
        album.release_date = form.release_date.data
        
        # Update the selected songs for the album
        selected_song_ids = form.songs.data
        selected_songs = Song.query.filter(Song.id.in_(selected_song_ids)).all()
        album.songs = selected_songs
        
        db.session.commit()
        flash('Album updated successfully!', 'success')
        return redirect(url_for('add_album'))
    
    songs = Song.query.filter_by(creator_id=current_user.id).all()
    
    return render_template('edit_album.html', form=form, album=album, songs=songs)

#Delete Album as a Creator
@app.route('/delete_album/<int:album_id>', methods=['POST'])
@login_required
def delete_album(album_id):
    album = Album.query.get(album_id)
    if not album:
        flash('Album not found', 'danger')
    else:
        db.session.delete(album)
        db.session.commit()
        flash('Album deleted successfully!', 'success')
    
    return redirect(url_for('creator_dashboard'))

#End of Creator