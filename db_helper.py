import sqlite3


class DBHelper:
    def __init__(self, dbname="games.sqlite"):
        self.dbname = dbname
        self.conn = sqlite3.connect(dbname)

    def setup_games(self):
        stmt = "CREATE TABLE IF NOT EXISTS games (day text, date text, announced boolean)"
        self.conn.execute(stmt)
        self.conn.commit()
        
    def setup_players(self):
        stmt = "CREATE TABLE IF NOT EXISTS players (day text, player text)"
        self.conn.execute(stmt)
        self.conn.commit()
        
    def drop_games(self):
        stmt = "DROP TABLE games"
        self.conn.execute(stmt)
        self.conn.commit()
        
    def drop_players(self):
        stmt = "DROP TABLE players"
        self.conn.execute(stmt)
        self.conn.commit()
        
    def add_game(self, day, date):
        stmt = "INSERT INTO games (day, date, is_announced) VALUES (?, ?, ?)"
        args = (day, date, 0)
        self.conn.execute(stmt, args)
        self.conn.commit()
        
    def add_player(self, day, player):
        stmt = "INSERT INTO players (day, player) VALUES (?, ?)"
        args = (day, player)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def delete_game(self, day):
        stmt = "DELETE FROM games WHERE day = (?)"
        args = (day, )
        self.conn.execute(stmt, args)
        self.conn.commit()
    
    def delete_player(self, day, player):
        stmt = "DELETE FROM players WHERE day = (?) and player = (?)"
        args = (day, player)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def get_games(self):
        stmt = "SELECT day FROM games"
        return [x[0] for x in self.conn.execute(stmt)]
    
    def get_games_dates(self):
        stmt = 'SELECT date FROM games'
        return [x[0] for x in self.conn.execute(stmt)]
    
    def get_weekday_of_game(self, date):
        stmt = 'SELECT day FROM games WHERE date = (?)'
        args = (date, )
        return [x[0] for x in self.conn.execute(stmt, args)]
    
    def get_is_announced_of_game(self, date):
        stmt = 'SELECT is_announced FROM games WHERE date = (?)'
        args = (date, )
        return [x[0] for x in self.conn.execute(stmt, args)]
    
    def check_as_announced(self, date):
        stmt = 'UPDATE games SET is_announced = 1 WHERE date = (?)'
        args = (date,)
        self.conn.execute(stmt, args)
        self.conn.commit()
    
    def get_players(self, day):
        stmt = "SELECT player FROM players WHERE day = (?)"
        args = (day, )
        return ['@'+x[0].replace("_", "\_") for x in self.conn.execute(stmt, args)]
    
    def get_one_player(self, day, player):
        stmt = "SELECT player FROM players WHERE (day) = (?) and player = (?)"
        args = (day, player)
        return [x[0] for x in self.conn.execute(stmt, args)]
    
    def count_players(self, day):
        stmt = "SELECT count(1) FROM players WHERE (day) = (?)"
        args = (day,)
        return [x for x in self.conn.execute(stmt, args)]