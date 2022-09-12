from flask import Flask, render_template, redirect, url_for, request, flash
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField, IntegerField
from wtforms.validators import DataRequired
import requests
from waitress import serve


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movie-collection.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
Bootstrap(app)
db = SQLAlchemy(app)

DB_URL = "https://api.themoviedb.org/3/search/movie"
MOVIE_DB_INO_URL = "https://api.themoviedb.org/3/movie"
MOVIE_IMG_URL = "https://www.themoviedb.org/t/p/w600_and_h900_bestv2"
API_KEY = "e89fe85e9620919637bc18f1210dae42"


class FilmRating(FlaskForm):
    rating = FloatField('Your Rating Out of 10. e.g 7.5', validators=[DataRequired()])
    review = StringField('Your Review', validators=[DataRequired()])
    submit = SubmitField('Done')


class AddMovie(FlaskForm):
    title = StringField('Search Movie Title', validators=[DataRequired()])
    add = SubmitField('Add Movie')


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, unique=False, nullable=False)
    description = db.Column(db.Text(1000), unique=True, nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.Text(500), nullable=True)
    img_url = db.Column(db.String(300), unique=True, nullable=False)

    def __repr__(self):
        return self.id, self.title, self.year, self.description, self.rating, self.ranking, self.review, self.img_url


# db.create_all()


@app.route("/")
def home():
    all_movies = Movie.query.order_by(Movie.rating).all()
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", movies=all_movies)


@app.route("/add", methods=["post", "GET"])
def add():
    add_form = AddMovie()
    if add_form.validate_on_submit():
        movie_title = add_form.title.data
        response = requests.get(DB_URL, params={"api_key": API_KEY, "query": movie_title}).json()
        data = response['results']
        if not data:
            flash("Nothing matched with your query! Please check your spelling and try again ")
            return redirect(url_for('add'))
        return render_template("select.html", movies=data)

    return render_template("add.html", form=add_form)


@app.route("/find")
def find_movie():
    movie_id = request.args.get('id')
    if movie_id:
        movie_api_url = f"{MOVIE_DB_INO_URL}/{movie_id}"
        data = requests.get(movie_api_url, params={"api_key": API_KEY}).json()
        new_movie = Movie(
            title=data['title'],
            year=data['release_date'].split("-")[0],
            description=data['overview'],
            img_url=f"{MOVIE_IMG_URL}{data['poster_path']}"
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for('edit', id=new_movie.id))


@app.route("/edit", methods=["POST", 'GET'])
def edit():
    form = FilmRating()
    movie_id = request.args.get('id')
    movie_to_update = Movie.query.get(movie_id)
    if form.validate_on_submit():
        movie_to_update.rating = form.rating.data
        movie_to_update.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))

    return render_template("edit.html", form=form, movie=movie_to_update)


@app.route("/delete", methods=["POST", "GET"])
def delete():
    movie_id = request.args.get('id')
    movie_to_delete = Movie.query.get(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(host="0.0.0.0")
