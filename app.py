from flask import Flask, render_template, url_for, session, request, redirect, flash
from flask_pymongo import PyMongo
import bcrypt

app = Flask(__name__)
app.config['MONGO_URI'] = "mongodb+srv://AntonioDB:AntonioDB@cluster0-r72se.mongodb.net/Sportify?retryWrites=true&w=majority"
mongo = PyMongo(app);
app.secret_key = 'super secret key'

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('home'))
    else:
        return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    users = mongo.db.users
    login_user = users.find_one({'name' : request.form['username']})

    if login_user:
        if bcrypt.hashpw(request.form['pw'].encode('utf-8'), login_user['password']) == login_user['password']:
            session['username'] = request.form['username']
            try:
                session['team'] = login_user['team']
            except:
                pass
            return redirect(url_for('index'))
    else:
        flash("Username o password errati")
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('team', None)
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/register', methods=['POST','GET'])
def register():
    if request.method == 'POST':
        users = mongo.db.users
        existing_user = users.find_one({'name' : request.form['username']})
        existing_email = users.find_one({'email' : request.form['email']})

        if existing_user is None:
            if existing_email is None:
                hashpass = bcrypt.hashpw(request.form['pw'].encode('utf-8'), bcrypt.gensalt())
                users.insert({'name' : request.form['username'], 'password' : hashpass, 'email' : request.form['email']})
                session['username'] = request.form['username']
                return redirect(url_for('index'))
            else:
                flash("Questa email è già stata registrata da un altro utente")
                return redirect(url_for('register'))
        else:
            flash("Esiste già un utente con questo username!")
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/home')
def home():
    if 'username' in session:
        session.database = mongo.db
        return render_template('home.html')

    else:
        return redirect(url_for('index'))

@app.route('/sport')
def sport():
    if 'username' in session:
        session.database = mongo.db
        return render_template('sport.html')

    else:
        return redirect(url_for('index'))

@app.route('/join/<evento>')
def join(evento):
    mongo.db.events.update_one({'name': evento}, {"$addToSet": {'competitors': session['username']}})
    return redirect(url_for('home'))

@app.route('/aggiungi',methods=['POST'])
def aggiungi():
    newsport = request.form['add']
    user_library = mongo.db.users.find_one({"$and":[{'name': session['username']},{'sports': newsport}]})
    if user_library:
        flash("Sport già presente in libreria")
        return redirect(url_for('sport'))
    else:
        mongo.db.users.update_one({'name': session['username'] }, {"$addToSet": {'sports': newsport}})
        return redirect(url_for('sport'))

@app.route('/search',methods=['POST'])
def search():
    risultato = mongo.db.events.find_one({'name': request.form['codice']})
    if risultato:
        session.ricerca = risultato
        return render_template('search.html')
    else:
        flash("Evento non trovato")
        return redirect(url_for('home'))

@app.route('/admin')
def admin():
    if session['username'] == "admin":
        session.database = mongo.db
        return render_template('admin.html')
    else:
        return redirect(url_for('home'))

@app.route('/addsport',methods=['POST'])
def addsport():
    if mongo.db.sports.find_one({'title': request.form['newsport']}):
        flash("Sport già presente")
        return redirect(url_for('admin'))
    else:
        mongo.db.sports.insert({'title': request.form['newsport']})
        flash("Sport inserito con successo")
        return redirect(url_for('admin'))

@app.route('/addevent',methods=['POST'])
def addevent():
    if mongo.db.events.find_one({'name': request.form['neweventid']}):
        flash("Evento già presente")
        return redirect(url_for('admin'))
    else:
        date= request.form['neweventdate'] + " " + request.form['neweventhour']
        mongo.db.events.insert({'name': request.form['neweventid'], 'title': request.form['neweventsport'], 'date': date})
        flash("Evento inserito con successo")
        return redirect(url_for('admin'))

@app.route('/team')
def team():
    if 'username' in session:
        session.database = mongo.db
        return render_template('team.html')
    else:
        return redirect(url_for('index'))

@app.route('/searchteam',methods=['POST'])
def searchteam():
    risultato = mongo.db.teams.find_one({'name': request.form['teamname']})
    if risultato:
        mongo.db.users.update_one({'name': session['username']},{"$set": {'team': request.form['teamname']}})
        mongo.db.teams.update_one({'name': request.form['teamname']},{"$addToSet":{'users': session['username']}})
        session['team'] = request.form['teamname']
        return redirect(url_for('team'))

    else:
        flash("Il team inserito non è stato trovato")
        return redirect(url_for('team'))

@app.route('/createteam',methods=['POST'])
def createteam():
    risultato = mongo.db.teams.find_one({'name': request.form['teamname']})
    if risultato:
        flash("Esiste già un team con questo nome")
        return redirect(url_for('team'))
    else:
        mongo.db.teams.insert({'name': request.form['teamname']})
        mongo.db.users.update_one({'name': session['username']}, {"$set": {'team': request.form['teamname']}})
        mongo.db.teams.update_one({'name': request.form['teamname']}, {"$addToSet": {'users': session['username']}})
        session['team'] = request.form['teamname']
        return redirect(url_for('team'))

@app.route('/leaveteam')
def leaveteam():
    mongo.db.users.update_one({'name': session['username']}, {"$unset": {'team': session['team']}})
    mongo.db.teams.update_one({'name': session['team']}, {"$pull": {'users': session['username']}})
    numero_membri = mongo.db.teams.find_one({'name': session['team']})
    if len(numero_membri['users']) == 0:
        mongo.db.teams.delete_one({'name': session['team']})
    session.pop('team',None)
    return redirect(url_for('team'))

if __name__ == '__main__':
    app.run(debug=False)

