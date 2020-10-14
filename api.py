from flask import Flask, jsonify, request
from flask_restful import Resource, Api, reqparse
from sqlalchemy import create_engine
from flask_cors import CORS

e = create_engine('sqlite:///db/friendlies.db')

app = Flask(__name__)
api = Api(app)
CORS(app)

class Battlers_Meta(Resource):
    def get(self):
        conn = e.connect()
        query = conn.execute('select * from battlers;')
        return {
            'battlers': [
                {
                    'username':a[0],
                    'twitter': a[1],
                    'twitch': a[2]
                }
                for a in query.cursor.fetchall()
            ]
        }

class Games_Meta(Resource):
    def get(self):
        conn = e.connect()
        query = conn.execute("""SELECT game_id, format, series, battlers.display_name, youtube_link 
FROM games INNER JOIN battlers ON games.winner = battlers.battler_id;""")
        return {
            'games': [
                {
                    'game_id': a[0],
                    'format': a[1],
                    'series': a[2],
                    'winner': a[3],
                    'youtube': a[4]
                } 
                for a in query.cursor.fetchall()
            ]
        }
class Game_Battler_Pokemon(Resource):
    def get(self):
        conn = e.connect()
        game_id = request.args.get('game_id')
        battler_id = request.args.get('battler_id')
        query = conn.execute(f"""
            SELECT b.display_name, p.pokemon_name
            FROM battler_game_pokemon bgp
            INNER JOIN battlers b ON bgp.battler_id = b.battler_id
            INNER JOIN pokemon p ON bgp.pokemon_id = p.pokemon_id
            WHERE bgp.game_id == {game_id} and bgp.battler_id = {battler_id};
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
            FROM battler_game_pokemon  bgp
            INNER JOIN games g on bgp.game_id = g.game_id
            INNER JOIN pokemon p on bgp.pokemon_id = p.pokemon_id
            where g.format = 'VGC2020'
            AND g.series = {series}
            GROUP BY bgp.pokemon_id
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
            SELECT bt.display_name, a.wins, b.games_played, 1.0*a.wins/b.games_played as WinPct
            FROM
            (
	            SELECT winner, count(*) as wins
	            FROM games
	            GROUP BY winner
            ) a 
            INNER JOIN (
	            SELECT battler_id, count(*) as games_played
	            FROM(
		            SELECT battler_id, game_id 
		            FROM battler_game_pokemon 
		            GROUP BY battler_id, game_id
	            )
	            GROUP BY battler_id
            ) b 
            ON a.winner = b.battler_id
            INNER JOIN battlers bt ON a.winner = bt.battler_id
            ORDER BY 1.0*a.wins/b.games_played DESC, b.Games_played DESC""")
        return [
            {'name': a[0], 'wins':a[1], 'games_played': a[2], 'win_%':f'{100*a[3]:.1f}%'}
            for a in query.cursor.fetchall()
        ]

api.add_resource(Battlers_Meta, '/api/v1/battlers')
api.add_resource(Games_Meta, '/api/v1/games')
api.add_resource(Game_Battler_Pokemon, '/api/v1/pokemon_by_user_by_game')
api.add_resource(MainTable, '/api/v1/table')
api.add_resource(UsageStats, '/api/v1/usage')
if __name__ == '__main__':
    app.run(host='0.0.0.0')
