# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#
import logging
from logging import Formatter, FileHandler

import babel
import dateutil.parser
from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
#from models import  Venue, Artist, Show
from forms import *

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#
app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
# Connect to a local postgresql database
db = SQLAlchemy(app)

# Instantiate Migrate
migrate = Migrate(app, db)


# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#
class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=True, unique=True)
    city = db.Column(db.String, nullable=True)
    state = db.Column(db.String, nullable=True)
    address = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(12), nullable=True)
    genres = db.Column(db.ARRAY(db.String), nullable=True)
    image_link = db.Column(db.String(255), nullable=True)
    facebook_link = db.Column(db.String(255), nullable=True)
    website = db.Column(db.String(255), nullable=True)
    seeking_talent = db.Column(db.Boolean(), default=False)
    seeking_description = db.Column(db.String(128), nullable=True)
    shows = db.relationship('Show', backref='venue', lazy=True, passive_deletes=True)


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=True, unique=True)
    city = db.Column(db.String, nullable=True)
    state = db.Column(db.String, nullable=True)
    phone = db.Column(db.String(12), nullable=True)
    genres = db.Column(db.ARRAY(db.String), nullable=True)
    image_link = db.Column(db.String(255), nullable=True)
    facebook_link = db.Column(db.String(255), nullable=True)
    website = db.Column(db.String(255), nullable=True)
    seeking_venue = db.Column(db.Boolean(), default=False)
    seeking_description = db.Column(db.String(255), nullable=True)
    shows = db.relationship('Show', backref='artist', lazy=True, passive_deletes=True)


class Show(db.Model):
    __tablename__ = 'Show'

    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey(Venue.id, ondelete='CASCADE'), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey(Artist.id, ondelete='CASCADE'), nullable=False)
    start_time = db.Column(db.DateTime(), nullable=False)


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#
def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#
@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------
@app.route('/venues')
def venues():
    # Find distinct city, state areas
    areas = db.session.query(Venue.city, Venue.state).distinct()
    data = []
    for venue in areas:
        # Let venue be a zipped array of keys city, state from the area
        venue = dict(zip(('city', 'state'), venue))
        # Add the venues array to this city, state
        venue['venues'] = []
        venues_for_area = Venue.query.filter_by(city=venue['city'], state=venue['state']).all()
        for venue_data in venues_for_area:
            related_shows = Show.query.filter_by(venue_id=venue_data.id).all()
            venues_data = {
                'id'                : venue_data.id,
                'name'              : venue_data.name,
                'num_upcoming_shows': upcoming_shows_count(related_shows)
            }
            venue['venues'].append(venues_data)
        data.append(venue)

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # search for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    response = {
        "data": []
    }
    # gather all venue names and ids
    venues = db.session.query(Venue.name, Venue.id).all()
    # lower case our search term
    search_term = request.form.get('search_term').lower()
    for venue in venues:
        id = venue[1]
        # lower case our names from db results
        name = venue[0].lower()
        if name.find(search_term) != -1:
            related_shows = Show.query.filter_by(venue_id=id).all()
            venue = dict(zip(('name', 'id'), venue))
            venue['num_upcoming_shows'] = upcoming_shows_count(related_shows)
            response['data'].append(venue)
    response['count'] = len(response['data'])

    return render_template('pages/search_venues.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>', methods=['GET', 'POST'])
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    venue = Venue.query.get(venue_id)
    if venue:
        related_shows = Show.query.filter_by(venue_id=venue_id).all()
        data = {
            "id"                  : venue_id,
            "name"                : venue.name,
            "genres"              : venue.genres,
            "address"             : venue.address,
            "city"                : venue.city,
            "state"               : venue.state,
            "phone"               : venue.phone,
            "website"             : venue.website,
            "facebook_link"       : venue.facebook_link,
            "seeking_talent"      : venue.seeking_talent,
            "seeking_description" : venue.seeking_description,
            "image_link"          : venue.image_link,
            "past_shows"          : past_shows(related_shows),
            "upcoming_shows"      : upcoming_shows(related_shows),
            "past_shows_count"    : past_shows_count(related_shows),
            "upcoming_shows_count": upcoming_shows_count(related_shows),
        }
    else:
        flash('An error occurred. Venue id:' + str(venue_id) + ' could not be found.', 'error')
        return redirect(url_for('venues'))

    return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------
@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    error = False
    form = VenueForm()
    try:
        create_venue = Venue(
            name=form.name.data,
            city=form.city.data,
            state=form.state.data,
            address=form.address.data,
            phone=form.phone.data,
            genres=form.genres.data,
            website=form.website.data,
            facebook_link=form.facebook_link.data,
            image_link=form.image_link.data,
            seeking_talent=form.seeking_talent.data,
            seeking_description=form.seeking_description.data
        )
        db.session.add(create_venue)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
    finally:
        db.session.close()
    if error:
        # on error, flash error message
        flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.', 'error')
        return render_template('forms/new_venue.html', form=form)
    else:
        # on successful db insert, flash success
        flash('Venue ' + request.form['name'] + ' was successfully listed!', 'success')

    return redirect(url_for('venues'))


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    all_artists = Artist.query.order_by(Artist.name).all()
    data = []
    for artist in all_artists:
        artist = {
            "id"  : artist.id,
            "name": artist.name
        }
        data.append(artist)

    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # search for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    response = {
        "data": []
    }
    # gather all venue names and ids
    all_artists = db.session.query(Artist.name, Artist.id).all()
    # lower case our search term
    search_term = request.form.get('search_term').lower()
    for artist in all_artists:
        id = artist[1]
        # lower case our names from db results
        name = artist[0].lower()

        if name.find(search_term) != -1:
            related_shows = Show.query.filter_by(venue_id=id).all()
            artist = dict(zip(('name', 'id'), artist))
            artist['num_upcoming_shows'] = upcoming_shows_count(related_shows)
            response['data'].append(artist)
    response['count'] = len(response['data'])

    return render_template('pages/search_artists.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>', methods=['GET', 'POST'])
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    artist = Artist.query.get(artist_id)
    related_shows = Show.query.filter_by(artist_id=artist_id).all()
    data = {
        "id"                  : artist_id,
        "name"                : artist.name,
        "genres"              : artist.genres,
        "city"                : artist.city,
        "state"               : artist.state,
        "phone"               : artist.phone,
        "website"             : artist.website,
        "facebook_link"       : artist.facebook_link,
        "seeking_venue"       : artist.seeking_venue,
        "seeking_description" : artist.seeking_description,
        "image_link"          : artist.image_link,
        "past_shows"          : past_shows(related_shows),
        "upcoming_shows"      : upcoming_shows(related_shows),
        "past_shows_count"    : past_shows_count(related_shows),
        "upcoming_shows_count": upcoming_shows_count(related_shows),
    }

    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    artist = Artist.query.get(artist_id)
    form = ArtistForm(obj=artist)
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # artist record with ID <artist_id> using the new attributes
    error = False
    form = ArtistForm()
    try:
        artist = Artist.query.get(artist_id)
        # assign new form values to database
        artist.name = form.name.data
        artist.city = form.city.data
        artist.state = form.state.data
        artist.phone = form.phone.data
        artist.genres = form.genres.data
        artist.website = form.website.data
        artist.facebook_link = form.facebook_link.data
        artist.image_link = form.image_link.data
        artist.seeking_venue = form.seeking_venue.data
        artist.seeking_description = form.seeking_description.data

        # db.session.update(venue)
        db.session.commit()
    except Exception as e:
        print(f'Error ==> {e}')
        error = True
        db.session.rollback()
    finally:
        db.session.close()
    if error:
        # on error, flash error message
        flash('An error occurred. Artist ' + str(artist_id) + ' could not be updated.', 'error')
    else:
        # on successful db insert, flash success
        flash('Artist ' + str(artist_id) + ' was successfully updated!', 'success')

    return redirect(url_for('show_artist', artist_id=artist_id))


# Not working... Getting 405 method not allowed = Why?
# -----------------------------------------------------
# @app.route('/artist/<artist_id>', methods=['DELETE'])
# def delete_artist(artist_id):
#     error = False
#     response = True
#     body = []
#     try:
#         artist = Artist.query.get(artist_id)
#         body = {
#             "id"   : artist.id,
#             "name" : artist.name
#         }
#         db.session.delete(artist)
#         db.session.commit()
#     except:
#         db.session.rollback()
#     finally:
#         db.session.close()
#     if error:
#         response = False
#         # on error, flash error message
#         flash('An error occurred. Artist id:' + str(artist_id) + ' could not be deleted!', 'error')
#         body['error'] = error
#     else:
#         # on successful db delete, flash success
#         flash('Artist id:' + str(artist_id) + ' was successfully removed!', 'success')
#         body['response'] = response
#
#     return jsonify(body)


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    venue = Venue.query.get(venue_id)
    form = VenueForm(obj=venue)
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # venue record with ID <venue_id> using the new attributes
    error = False
    form = VenueForm()
    try:
        venue = Venue.query.get(venue_id)
        # assign new form values to database
        venue.name = form.name.data
        venue.city = form.city.data
        venue.state = form.state.data
        venue.address = form.address.data
        venue.phone = form.phone.data
        venue.genres = form.genres.data
        venue.website = form.website.data
        venue.facebook_link = form.facebook_link.data
        venue.image_link = form.image_link.data
        venue.seeking_talent = form.seeking_talent.data
        venue.seeking_description = form.seeking_description.data

        # db.session.update(venue)
        db.session.commit()
    except Exception as e:
        print(f'Error ==> {e}')
        error = True
        db.session.rollback()
    finally:
        db.session.close()
    if error:
        # on error, flash error message
        flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated.', 'error')
    else:
        # on successful db insert, flash success
        flash('Venue ' + request.form['name'] + ' was successfully updated!', 'success')

    return redirect(url_for('show_venue', venue_id=venue_id))


@app.route('/venues/<int:venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    error = False
    response = True
    body = []
    try:
        venue = Venue.query.get(venue_id)
        body = {
            "id"   : venue.id,
            "name" : venue.name
        }
        db.session.delete(venue)
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    if error:
        response = False
        # on error, flash error message
        flash('An error occurred. Venue id:' + str(venue_id) + ' could not be removed!', 'error')
        body['error'] = error
    else:
        # on successful db delete, flash success
        flash('Venue id:' + str(venue_id) + ' was successfully removed!', 'success')
        body['response'] = response

    return jsonify(body)


#  Create Artist
#  ----------------------------------------------------------------
@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    error = False
    form = ArtistForm()
    try:
        create_artist = Artist(
            name=form.name.data,
            city=form.city.data,
            state=form.state.data,
            phone=form.phone.data,
            genres=form.genres.data,
            facebook_link=form.facebook_link.data,
            website=form.website.data,
            image_link=form.image_link.data,
            seeking_venue=form.seeking_venue.data,
            seeking_description=form.seeking_description.data
        )
        db.session.add(create_artist)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
    finally:
        db.session.close()
    if error:
        # on error, flash error message
        flash('An error occurred. Artist ' + form.name.data + ' could not be listed.', 'error')
        return render_template('forms/new_artist.html', form=form)
    else:
        # on successful db insert, flash success
        flash('Artist ' + form.name.data + ' was successfully listed!', 'success')

    return redirect(url_for('artists'))


#  Shows
#  ----------------------------------------------------------------
@app.route('/shows')
def shows():
    # displays list of shows at /shows
    shows = Show.query.all()
    data = []
    for show in shows:
        show = {
            "venue_id"         : show.venue_id,
            "venue_name"       : Venue.query.get(show.venue_id).name,
            "artist_id"        : show.artist_id,
            "artist_name"      : Artist.query.get(show.artist_id).name,
            "artist_image_link": Artist.query.get(show.artist_id).image_link,
            "start_time"       : format_datetime(str(show.start_time))
        }
        data.append(show)

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create', methods=['GET'])
def create_shows():
    form = ShowForm()
    # form.artist_id.choices = db.session.query(Artist.id, Artist.name).order_by(Artist.name).all()
    # Adding the ID to the name in selectField
    choices = db.session.query(Artist.id, Artist.name).order_by(Artist.name).all()
    artist_choices = {}
    for choice in choices:
        id = choice[0]
        name = choice[1]
        new_name = 'ID: ' + str(id) + ' - ' + name
        artist_choices[id] = new_name
    form.artist_id.choices = list(artist_choices.items())

    # form.venue_id.choices = db.session.query(Venue.id, Venue.name).order_by(Venue.name).all()
    # Adding the ID to the name in selectField
    venue_choices = db.session.query(Venue.id, Venue.name).order_by(Venue.name).all()
    new_venue_choices = {}
    for venue_choice in venue_choices:
        id = venue_choice[0]
        name = venue_choice[1]
        new_name = 'ID: ' + str(id) + ' - ' + name
        new_venue_choices[id] = new_name
    form.venue_id.choices = list(new_venue_choices.items())

    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    error = False
    form = ShowForm()
    try:
        create_show = Show(
            artist_id=form.artist_id.data,
            venue_id=form.venue_id.data,
            start_time=form.start_time.data
        )
        db.session.add(create_show)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
    finally:
        db.session.close()
    if error:
        # on error, flash error message
        flash('An error occurred. Show could not be listed.', 'error')
    else:
        # on successful db insert, flash success
        flash('Show was successfully listed!', 'success')

    return redirect(url_for('shows'))


def upcoming_shows(shows):
    upcoming = []
    for show in shows:
        if start_time_obj(show.start_time) > datetime.now():
            upcoming.append({
                "artist_id"        : show.artist_id,
                "artist_name"      : Artist.query.get(show.artist_id).name,
                "artist_image_link": Artist.query.get(show.artist_id).image_link,
                "start_time"       : format_datetime(str(show.start_time))
            })

    return upcoming


def upcoming_shows_count(shows):
    return len(upcoming_shows(shows))


def past_shows(shows):
    past = []
    for show in shows:
        if start_time_obj(show.start_time) < datetime.now():
            past.append({
                "artist_id"        : show.artist_id,
                "artist_name"      : Artist.query.filter_by(id=show.artist_id).first().name,
                "artist_image_link": Artist.query.filter_by(id=show.artist_id).first().image_link,
                "start_time"       : format_datetime(str(show.start_time))
            })

    return past


def past_shows_count(shows):
    return len(past_shows(shows))


def start_time_obj(start_time):
    formatted_date = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
    return formatted_date


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
