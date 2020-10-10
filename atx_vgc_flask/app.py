import flask
import json
from flask_cors import CORS


with open('users.json','r') as fp:
    users = json.load(fp)
with  open('games.json','r') as fp:
    games = json.load(fp)

app = flask.Flask(__name__)
app.config['DEBUG'] = True
CORS(app)

@app.route('/users',methods=['GET'])
def get_users():    
    return flask.jsonify(users)

@app.route('/games',methods=['GET'])
def get_games():
    return flask.jsonify(games)

@app.route('/table',methods=['GET'])
def get_table():
    data = []
    for user in users:
        name = user['name']
        wins = games_won(user['id'], games)
        gp = games_played(user['id'], games)
        pct = f'{wins/gp*100:.1f}%'
        data.append({'name':name,'wins':wins,'games_played':gp,'win_%':pct})
    return flask.jsonify(data)
def games_played(pid, json):
    return len([a for a in json if pid in [b['id'] for b in a['competitors']]])
    
def games_won(pid,json):
    return len([a for a in json if pid == a['winner']])

if __name__ == '__main__':
    app.run()