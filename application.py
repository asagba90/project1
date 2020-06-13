import os
import re

from flask import Flask, session, render_template, redirect, request, url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

#this will be the login page
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

@app.route('home/profile')
def profile():
	#check if user is loggedin
	if 'loggedin' in session:
		account = db.execute('SELECT * from accounts where id = :id', {"id": session['id']}).fetchone()
		#show the profile page with account info
		return render_template('profile.html', account=account)
	#User is not loggedin redirect to login page
	return redirect(url_for('login'))