from flask import Flask, jsonify, request, Markup, send_file
from flask_restful import Resource, Api, reqparse
from sqlalchemy import create_engine
from flask_cors import CORS
import json
import os
import sys
from dotenv import load_dotenv


load_dotenv()
PACKAGE_PATH = os.getenv('PACKAGE_PATH')
sys.path.append(PACKAGE_PATH)
from pokedata.pasteparser import PasteParser

e = create_engine('sqlite:///db/friendlies.db')

app = Flask(__name__)
api = Api(app)
CORS(app)
parser = reqparse.RequestParser()
parser.add_argument('id')
parser.add_argument('pokemon')


@app.route('/api/v1/pasteparser/testing', methods=["GET", "POST"])
def test_view():
    resp_ = request.args.get('responses')
    with open('templates/testing.json','w') as fp:
        json.dump({resp_:''}, fp)
    return jsonify({resp:''})

@app.route('/api/v1/pasteparser/team_sprites', methods=["GET","POST"])
def get_team_image():
    paste = request.args.get('paste')
    full_paste = 'https://pokepast.es/'+paste
    pp = PasteParser(full_paste)
    pp.getPokemon()
    pp.generateMNFSprites('templates/','tmp_team')
    return send_file('templates/tmp_team.png', mimetype='image/png')


@app.route('/api/v1/showdown_replay.js')
def get_showdown_js():
    with open('templates/showdown_replay.js','r') as fp:
        return fp.read()
@app.route('/api/v1/replay')
def get_replay():
    data = parser.parse_args()
    if not data['id']:
        return '<html></html>'
    else:
        file = [a for a in os.listdir('templates') if a.lower().find(data['id'])==0][0]
        with open('templates/'+file,'r') as fp:
            ret_string = fp.read()
        return ret_string

@app.route('/api/v1/sports-center')
def get_sports_center():
    with open('sports-center.json','r') as fp:
        return jsonify(json.load(fp))

class Replays(Resource):
    def get(self, id=None):
        data = parser.parse_args()
        if not data['id']:
            return '<html></html>'
        else:
            file = [a for a in os.listdir('templates') if a.find(data['id'])==0][0]
            with open('templates/'+file,'r') as fp:
                ret_string = fp.read()
            return Markup(ret_string[1:-1])

class Pokemon(Resource):
    def get(self,id=None, pokemon=None):
        data = parser.parse_args()
        print(data.keys())
        print(data)
        if not data['id']:
            if 'pokemon' not in data.keys():
                query_string = 'SELECT * from pokemon;'
            else:
                query_string = f'SELECT * from pokemon WHERE pokemon_name LIKE "%{data["pokemon"]}%"'
        else:
            id = data['id']
            query_string = f'SELECT * from pokemon where pokemon_id="{id}"'
        print(query_string)
        conn = e.connect()
        query = conn.execute(query_string)
        return {
            'pokemon': [
                {
                    'id':a[0],
                    'name': a[1]
                }
                for a in query.cursor.fetchall()
            ]
        }
    def post(self):
        id_ = request.json['pokemon_id']
        name = request.json['pokemon']
        query_string = f"INSERT INTO pokemon VALUES ({id_},{name});"
        conn = e.connect()
        conn.execute(query_string)
        return {
            'pokemon': [
                {
                    'id':id_,
                    'name': name
                }
            ]
        }


class Players(Resource):
    def get(self, id=None):
        data = parser.parse_args()
        if not data['id']:
            query_string = 'select * from players;'
        else:
            query_string = f"SELECT * FROM players WHERE pid = {data['id']}"
        conn = e.connect()
        query = conn.execute(query_string)
        return {
            'players': [
                {
                    'id':a[0],
                    'display_name': a[1],
                    'twitter': a[2],
                    'twitch': a[3],
                    'slug': a[4],
                    'flag': a[5]

                }
                for a in query.cursor.fetchall()
            ]
        }
    def post(self):
        req_type = request.json['req_type']
        players = requets.json['players']
        list_of_reqs = []
        for player in players:
            id_ = request.json['pid']
            name = request.json['display_name']
            twitter = request.json['twitter']
            twitch = request.json['twitch']
            slug = request.json['slug']
            flag_id = request.json['flag_id']
            vals = {'name':name, 'twitter':twitter,'twitch':twitch,'slug':slug,'flag_id':flag_id}
            if req_type == 'UPDATE':
                new_vals = {key:val for key,val in vals.items() if val is not None}
                query_string = f"UPDATE players SET " + ", ".join([f"{key}={val}" for key,val in new_vals])[:-3] + f"WHERE pid = {id_}"
            else:
                query_string = f"INSERT INTO players VALUES ({id_},{name},{twitter},{twitch},{slug},{flag_id});"
            conn = e.connect()
            conn.execute(query_string)
            list_of_reqs.append(query_string)
        return {"request_type":req_type,"sql_statements":list_of_reqs}
        

class Games_Meta(Resource):
    def get(self):
        conn = e.connect()
        query = conn.execute("""SELECT gid, format, series, display_name, youtube_link, players, game_date
FROM games 
INNER JOIN players ON winner = pid
INNER JOIN (SELECT game_id, group_concat(distinct(display_name)) as players
FROM g_p_p INNER JOIN players on player_id = pid
GROUP BY game_id) b on gid = b.game_id;""")
        ret = {
            'games': [
                {
                    'game_id': a[0],
                    'format': a[1],
                    'series': a[2],
                    'winner': a[3],
                    'youtube': a[4],
                    'players': a[5].split(','),
                    'date': a[6]
                } 
                for a in query.cursor.fetchall()
            ]
        }
        return ret

    def put(self):
        req_type = request.json['req_type']
        games = requets.json['games']
        list_of_reqs
        for game in games:
            vals = {}
            vals['gid'] = game['gid']
            vals['format_'] = game['format']
            vals['series'] = game['series']
            vals['winner'] = game['winner']
            vals['youtube'] = game['youtube']
            vals['date'] = game['date']
            if req_type == 'UPDATE':
                new_vals = {key:val for key,val in vals if val is not None}
                query_string = f"UPDATE games SET " + ", ".join([f"{key}={val}" for key,val in new_vals])[:-3] + f"WHERE gid = {vals['gid']}"
            else:
                querey_string = f"INSERT INTO games VALUES ({vals['gid']},{vals['format_']},{vals['series']},{vals['winner']},{vals['youtube']},{vals['date']})"
            conn = e.connect()
            conn.execute(query_string)
            list_of_reqs.append(query_string)
        return {"request_type":req_type,"sql_statements":list_of_reqs}

class Game_Battler_Pokemon(Resource):
    def get(self):
        conn = e.connect()
        game_id = request.args.get('game_id',default=0)
        battler_id = request.args.get('player_id',default=1)
        query_str = f"""
            SELECT p.display_name, pk.pokemon_name
            FROM g_p_p
            INNER JOIN players p ON g_p_p.player_id = p.pid
            INNER JOIN pokemon pk ON g_p_p.pokemon_id = pk.pokemon_id
            WHERE g_p_p.game_id = {game_id} and g_p_p.player_id = {battler_id};
        """
        query = conn.execute(query_str)
        res = {'game':game_id,'pokemon':query.cursor.fetchall()}
        return res
    def post(self):
        conn = e.connect()
        # INSSERT ONLY on this one
        games = requets.json['games']
        queries = []
        for game in games:
            vals = {}
            val['game_id'] = games['game_id']
            val['player_id'] = games['player_id']
            val['pokemon'] = games['pokemon']
            query_str = "INSERT INTO g_p_p VALUES "
            for pokemon in val['pokemon']:
                query_str += f"({val['game_id']},{val['player_id']},{val['pokemon']}),"
            query_str = query_str[:-1]
            conn.execute(query_str)
            queries.append(query_str)
        return {'queries':queries}

class UsageStats(Resource):
    def get(self):
        conn = e.connect()
        series = request.args.get('series')
        if not series:
            # defaults to current series
            series = 6
        query = conn.execute(f"""
            SELECT g.format, g.series,
                 p.pokemon_name,
	             1.0*count(*)/(select 2*count(*) from games where series = {series}) as 'Usage'
            FROM g_p_p
            INNER JOIN games g on g_p_p.game_id = g.gid
            INNER JOIN pokemon p on g_p_p.pokemon_id = p.pokemon_id
            where g.format = 'VGC2020'
            AND g.series = {series}
            GROUP BY g_p_p.pokemon_id
            ORDER BY Usage DESC;
        """)
        res = query.cursor.fetchall()
        return {
            'format': res[0][0],
            'series': res[1][1],
            'pokemon': [
                {'name': a[2], 'usage': f'{100*a[3]:.1f}%'}
                for a in res
            ]
            
        }

class Home(Resource):
    def get(self):
        return "Hello! We'll eventually make some documentation here :) "

class MainTable(Resource):
    def get(self):
        conn = e.connect()
        query = conn.execute("""
        with ranked_games as (
	SELECT g.*, ROW_NUMBER() OVER (PARTITION by pid ORDER BY gid DESC) as rn
	FROM (SELECT pid, gid, youtube_link
FROM players JOIN g_p_p ON pid = player_id
join games ON gid = game_id) g
	WHERE youtube_link != ''
)
SELECT p.pid, 
	   p.display_name, 
	   b.wins,
	   a.games_played,
	   1.0*b.wins / a.games_played as win_pct,
	   p.twitter,
	    p.twitch,
	    p.flag_id,
	    rg.youtube_link,
        b.wins*10 - (a.games_played-b.wins)*4 as points
    FROM
	    (
		    SELECT player_id, count(*) as games_played
	  	    FROM (
	  		    SELECT player_id, game_id 
			    FROM g_p_p 
			    GROUP BY player_id, game_id
	  	    )
	  	    GROUP BY player_id
	    ) a
	    LEFT JOIN (
		    SELECT pid as winner, count(gid) as wins
			from players LEFT JOIN games
			ON players.pid = games.winner
			GROUP BY pid
	    ) b 
        ON b.winner = a.player_id
	    INNER JOIN players p ON a.player_id = p.pid
	    LEFT JOIN ranked_games rg on rg.pid = p.pid
	    WHERE rn = 1 OR rn is NULL
	    ORDER BY points DESC,
	    win_pct DESC;
        """)
        return [
            {'id':a[0],'name': a[1], 'wins':a[2], 'games_played': a[3], 'win_pct':f'{100*a[4]:.1f}%', 'twitter': a[5], 'twitch': a[6], 'flag':a[7], 'yt':a[8], 'points':max(a[9],0)}
            for a in query.cursor.fetchall()
        ]

api.add_resource(Players, '/api/v1/players')
api.add_resource(Games_Meta, '/api/v1/games')
api.add_resource(Game_Battler_Pokemon, '/api/v1/pokemon_by_user_by_game')
api.add_resource(MainTable, '/api/v1/table')
api.add_resource(UsageStats, '/api/v1/usage')
api.add_resource(Home, '/api/v1/docs')
api.add_resource(Replays, '/api/v1/replay')
api.add_resource(Pokemon, '/api/v1/pokemon')
if __name__ == '__main__':
    app.run(host='0.0.0.0')