from flask import Flask, jsonify, request
from flask_restful import Resource, Api, reqparse
from sqlalchemy import create_engine
from flask_cors import CORS

e = create_engine('sqlite:///db/friendlies.db')

app = Flask(__name__)
api = Api(app)
CORS(app)
parser = reqparse.RequestParser()
parser.add_argument('id')

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

class Games_Meta(Resource):
    def get(self):
        conn = e.connect()
        query = conn.execute("""SELECT gid, format, series, display_name, youtube_link, players
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
                    'players': a[5].split(',')
                } 
                for a in query.cursor.fetchall()
            ]
        }
        return ret
class Game_Battler_Pokemon(Resource):
    def get(self):
        conn = e.connect()
        game_id = request.args.get('game_id')
        battler_id = request.args.get('player_id')
        query = conn.execute(f"""
            SELECT p.display_name, pk.pokemon_name
            FROM g_p_p
            INNER JOIN players b ON g_p_p.player_id = p.pid
            INNER JOIN pokemon pk ON g_p_p.pokemon_id = p.pokemon_id
            WHERE g_p_p.game_id == {game_id} and g_p_p.player_id = {player_id};
        """)
        res = query.cursor.fetchall()
        return res

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


class MainTable(Resource):
    def get(self):
        conn = e.connect()
        query = conn.execute("""
            SELECT p.pid, p.display_name, a.wins, b.games_played, 1.0*a.wins/b.games_played as WinPct
            FROM
            (
	            SELECT winner, count(*) as wins
	            FROM games
	            GROUP BY winner
            ) a 
            INNER JOIN (
	            SELECT player_id, count(*) as games_played
	            FROM(
		            SELECT player_id, game_id 
		            FROM g_p_p 
		            GROUP BY player_id, game_id
	            )
	            GROUP BY player_id
            ) b 
            ON a.winner = b.player_id
            INNER JOIN players p ON a.winner = p.pid
            ORDER BY 1.0*a.wins/b.games_played DESC, b.Games_played DESC""")
        return [
            {'id':a[0],'name': a[1], 'wins':a[2], 'games_played': a[3], 'win_pct':f'{100*a[4]:.1f}%'}
            for a in query.cursor.fetchall()
        ]

api.add_resource(Players, '/api/v1/players')
api.add_resource(Games_Meta, '/api/v1/games')
api.add_resource(Game_Battler_Pokemon, '/api/v1/pokemon_by_user_by_game')
api.add_resource(MainTable, '/api/v1/table')
api.add_resource(UsageStats, '/api/v1/usage')
if __name__ == '__main__':
    app.run(host='0.0.0.0')
