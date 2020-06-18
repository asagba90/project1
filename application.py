import os
import re

from flask import Flask, session, render_template, redirect, request, url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import requests
import json

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

app.static_folder = 'static'

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

#index page
@app.route('/')
def index():
	return render_template('index.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
	# output message if something happens...
	msg = ""
	#check if "username" and "password" post requests exist
	if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
		#create variables
		username = request.form['username']
		password = request.form['password']
		#check if accout exist
		account = db.execute('SELECT * FROM accounts WHERE usersname = :username AND password = :password', {"username": username, "password": password}).fetchone()
		if account:
			#create session data, we access this data in other routes
			session['loggedin'] = True
			session['id'] = account['id']
			session['username'] = account['usersname']
			return redirect(url_for('home'))
		else:
			#Account does not exist or incorrect username or password
			msg = 'incorrect username or password!'

	return render_template("login.html", msg=msg)


@app.route("/home/logout")
def logout():
	# Remove session data, this will log the user out
	session.pop('loggedin', None)
	session.pop('id', None)
	session.pop('username', None)
	#Redirect to login page
	return redirect(url_for('login'))

@app.route("/register", methods=['GET', 'POST'])
def register():
	# output message if goes wrong
	msg = ''
	#check if the form is filled
	if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
		username = request.form['username']
		password = request.form['password']
		email = request.form['email']
		# checking if account exist
		account = db.execute('SELECT * FROM accounts WHERE usersname = :username', {"username": username}).fetchone()
		if account:
			msg = 'Account already exists!'
		elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
			msg = 'Invalid email address! '
		elif not re.match(r'[A-Za-z0-9]+', username):
			msg = 'Username most contain only characters and numbers'
		elif not username or not password or not email:
			msg = '"Please fill out the form!'
		else:
			# Account does not exist and form data is valid, now insert new account into table
			db.execute('INSERT INTO accounts (usersname, password, email) VALUES (:username, :password, :email)', 
				{"username": username, "password": password, "email": email})
			db.commit()
			msg = 'you have successfully registered!'

	elif request.method == 'POST':
		# Form is empty
		msg = 'Please fill out the form!'

	return render_template('register.html', msg=msg)


@app.route('/home')
def home():
	# Check if user is logged in
	if 'loggedin' in session:
		return render_template('home.html', username=session['username'])

	return redirect(url_for('login'))

@app.route("/home/profile")
def profile():
	# check if logged in
	if "loggedin" in session:
		account = db.execute("SELECT * FROM accounts WHERE id = :id", {"id": session['id']}).fetchone()
		#show the profile page with account info
		return render_template("profile.html", account=account)

@app.route('/home/result', methods=['GET', 'POST'])
def result():
	search = request.form.get('search')

	if request.method == "POST":
		result = db.execute("SELECT * FROM books WHERE author iLIKE '%"+search+"%' OR title iLIKE '%"+search+"%' OR isbn iLIKE '%"+search+"%'").fetchall()

		if result:
			book_count = len(result)

			return render_template("search.html", result=result, book_number=book_count, username=session['username'])

		elif len(result) == 0:
			search_error = search + 'Not Found'
			return render_template('home.html', search_error=search_error, username=session['username'])


	else:
		return render_template('home.html',username=session['username'])

@app.route("/home/bookpage/<string:isbn>", methods=['GET', 'POST'])
def  bookpage(isbn):
	request = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "hVKf909VqkHtK6iHy3Mbw", "isbns": isbn})
	result_query = db.execute("SELECT * FROM books WHERE isbn=:isbn",{"isbn":isbn}).fetchall()
	average_rating=request.json()['books'][0]['average_rating']
	work_ratings_count=request.json()['books'][0]['work_ratings_count']
    # return 
	return render_template("bookpage.html",result_query=result_query,average=average_rating,work_ratings_count=work_ratings_count)


@app.route("/home/review/<string:isbn>", methods=['GET', 'POST'])
def review(isbn):
	username=session['username']
	rating = request.form.get('rating')
	review = request.form.get('review')
	data = db.execute('SELECT * FROM review WHERE isbn=:isbn AND username=:username', {"isbn":isbn, "username": username}).fetchall()
	if request.method == 'POST':
		if data:
			return render_template("bookpage.html", review_error="You already rated this book")

		elif review != None and rating != None:
			reviewed = db.execute('INSERT INTO review (username, isbn, review, rating) VALUES (:username, :isbn, :review, :rating)', {"username": username, "isbn": isbn, "review": review, "rating": rating})
			db.commit()
			if reviewed:
				msg = "Review added successfully"
				return render_template("home.html", msg=msg, username=session['username'])
			else:
				msg = "Enter Review"

				return render_template("bookpage.html", review_error=msg)
			

	else:
		return render_template("bookpage.html", msg='Nothing happened')

@app.route("/api/<string:isbn>",methods=["GET","POST"])

def api(isbn):
	request = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "hVKf909VqkHtK6iHy3Mbw", "isbns": isbn})
	result_query = db.execute("SELECT * FROM books WHERE isbn=:isbn",{"isbn":isbn}).fetchall()
	average_rating=request.json()['books'][0]['average_rating']
	work_ratings_count=request.json()['books'][0]['work_ratings_count']
	api_query = db.execute("SELECT * FROM books WHERE isbn=:isbn",{"isbn":isbn}).fetchone()
	if api_query == None:
		return 'Error oooooo' #render_template("error.html")
	data = {"title" : api_query.title,"author": api_query.author,"year":api_query.year,"isbn":api_query.isbn,"review_count":work_ratings_count,"average_score":average_rating}
	dump = json.dumps(data)
	return render_template("api.html",api=dump)
