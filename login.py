__author__ = 'RiteshReddy'
import __setup_path
from db import *
from flask_base import *

@app.route('/', endpoint="index")
@app.route('/<name>')
@authenticate
def hello_world(name=None):
    return render_template('hello.html', name=name)

@app.route('/login', methods=["GET", "POST"])
def login():
    errors = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        isValid = check_user(username, password)
        if isValid:
            session['username'] = username
            return redirect(request.args.get('next', url_for('index')))
        else:
            errors = "Invalid login/password"

    return render_template("login.html", errors=errors)


@app.route("/logout")
def logout():
    if 'username' in session:
        session.pop('username', None)
    return redirect(url_for('login'))

@app.route("/signup",methods=["POST"])
def signup():
    errors = None
    # save user to database and sign them in

@app.route("/home")
def home():
    return render_template("home.html")

@app.route("/item/<identifier>")
def item(identifier = None):
    return render_template("item.html",identifier = identifier)

def check_user(username, password):
    return username==password

