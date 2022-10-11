from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests

numbers='0123456789'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-key'
app.config['SQLALCHEMY_DATABASE_URI']= 'sqlite:///movie-collection.db'
Bootstrap(app)
db = SQLAlchemy(app)
db.init_app(app)
TMDB_ENDPOINT = 'https://api.themoviedb.org/3'
TMDB_API_KEY = 'user-api-key'


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    title = db.Column(db.String(200), nullable=False, unique=True)
    year = db.Column(db.String(25), nullable=False)
    description = db.Column(db.String(1000), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, unique=False)
    review = db.Column(db.String)
    img_url = db.Column(db.String, nullable=True)

class Form(FlaskForm):
    movie_rating = StringField(label='Your Movie Rating (out of 10) Eg. 7.5 : ',validators=[DataRequired()])
    movie_review = StringField(label='Your Movie Review: ', validators=[DataRequired()])
    done = SubmitField(label='Done')

class AddForm(FlaskForm):
    movie_title = StringField(label='Movie Title')
    add_movie_button = SubmitField(label='Add Movie')

with app.app_context():
    db.create_all()


@app.route("/")
def home():
    movies = Movie.query.order_by(Movie.ranking.desc()).all()
    if len(movies) == 0:
        return render_template("index.html",movie_len=len(movies))
    else:
        return render_template('index.html',moviez=movies, movie_len=len(movies))


@app.route('/edit', methods=['GET','POST'])
def edit():
    edit_rating = Form()
    if request.method == "POST":
        prim = ''
        for i in request.query_string.decode():
            if i in numbers:
                prim += i
        prim = int(prim)
        movie = Movie.query.get(prim)
        movie.rating = edit_rating.movie_rating.data
        movie.review = edit_rating.movie_review.data
        db.session.commit()
        prim = 0
        return redirect(url_for('home'))
    return render_template('edit.html', form=edit_rating, rank=request.args.get('num'))

@app.route('/delete', methods=['GET','POST'])
def delete():
    card_no = ''
    if request.method == 'GET':
        for i in request.query_string.decode():
            if i in numbers:
                card_no += i
        card_no = int(card_no)
        movie = Movie.query.get(card_no)
        db.session.delete(movie)
        db.session.commit()
        return redirect(url_for('home'))

@app.route('/add', methods=['GET','POST'])
def add():
    af = AddForm()
    if request.method == 'POST':
        return redirect(url_for('select',search=af.movie_title.data))

    return render_template('add.html', form=af)

@app.route('/select', methods=['GET','POST'])
def select():
    similar_results = []
    ids = []
    title_as_param = request.query_string.decode().split('=')
    title = title_as_param[1]
    access = requests.get(url=f"{TMDB_ENDPOINT}/search/movie",params={'api_key':TMDB_API_KEY, 'query':title, 'include_adult':True})
    details = access.json()
    for i in details['results']:
        similar_results.append(f"{i['title']} - {i['release_date']}")
        ids.append(i['id'])
    return render_template('select.html', movies=similar_results, movies_id=ids, results=len(similar_results))

@app.route('/temp')
def temp():
    identity_query = request.query_string.decode().split('=')
    identity = identity_query[1]
    access = requests.get(url=f"{TMDB_ENDPOINT}/movie/{identity}", params={'api_key':TMDB_API_KEY}).json()
    i = Movie.query.all()
    rat = []
    for j in i:
        rat.append(j.rating)
    rat.append(access['vote_average'])
    rat.sort(reverse=True)
    for m in i:
        m.ranking = rat.index(m.rating)+1
        db.session.commit()
    movie = Movie(id=access['id'],title=access['original_title'],year=access['release_date'],description=access['overview'], rating=access['vote_average'],ranking=rat.index(access['vote_average'])+1, review='None', img_url=f"https://image.tmdb.org/t/p/w500{access['poster_path']}")
    db.session.add(movie)
    db.session.commit()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
