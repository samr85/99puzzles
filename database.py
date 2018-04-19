from collections import defaultdict
import hashlib
import sqlite3
import pickle
from threading import RLock

database = sqlite3.connect("userdatabase.db", check_same_thread = False)
databaseWriteLock = RLock()

def initDb():
    database.row_factory = sqlite3.Row
    usersTableSyntax = "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, named INTEGER DEFAULT 0, passwordHash TEXT, highestSolved INTEGER DEFAULT -1)"
    answersTableSyntax = "CREATE TABLE IF NOT EXISTS answers (id INTEGER PRIMARY KEY, time INTEGER(4) DEFAULT (strftime('%s','now')), userid INTEGER, questionNumber INTEGER, inputs TEXT, result TEXT)"
    extraDataTableSyntax = "CREATE TABLE IF NOT EXISTS extraData (indexString TEXT UNIQUE, data TEXT)"

    c = database.cursor()
    c.execute(usersTableSyntax)
    c.execute(answersTableSyntax)
    c.execute(extraDataTableSyntax)
    database.commit()
    c.close()
    
initDb()

def dumpdb():
    ''' Purely for debugging - prints out the users and answers tables '''
    import prettytable
    c = database.cursor()
    ret = str(prettytable.from_db_cursor(c.execute("SELECT * FROM users"))) + "\n\n"
    ret += str(prettytable.from_db_cursor(c.execute("SELECT * FROM answers"))) + "\n\n"
    c.execute("SELECT * FROM extraData")
    table = prettytable.PrettyTable()
    table.field_names = [col[0] for col in c.description]
    for row in c.fetchall():
        newRow = list(row)
        newRow[1] = pickle.loads(row[1])
        table.add_row(newRow)
    ret += str(table)
    return ret

def printdb():
    print(dumpdb())

def getExtraData(index):
   getDataSql = "SELECT data FROM extraData WHERE indexString=?"
   c = database.cursor()
   c.execute(getDataSql, (index,))
   dataRow = c.fetchone()
   if dataRow:
       try:
           return pickle.loads(dataRow["data"])
       except Exception as ex:
           print("Exception loading stored data: " + str(ex))
           return None
   return None

def setExtraData(index, data):
    """ Save some arbitrary data into the database.  Will except if data is not serialisable """
    saveDataSql = "INSERT OR REPLACE INTO extraData VALUES (?, ?)"
    c = database.cursor()
    with databaseWriteLock:
        c.execute(saveDataSql, (index, pickle.dumps(data)))
        database.commit()


def getUser(userName):
    getUserSQL = "SELECT * FROM users where username=?"
    c = database.cursor()
    c.execute(getUserSQL, (userName, ))
    return c.fetchone()

def createUser(userName):
    createUserSQL = "INSERT INTO users(username) values (?)"
    with databaseWriteLock:
        c.execute(createUserSQL, (userName, ))
        database.commit()
    return self.getUser(userName)

def getAnswers(userId, questionNumber):
    getAnswersSQL = "SELECT inputs, result FROM answers WHERE userid=? AND questionNumber=? ORDER BY time"
    c = database.cursor()
    c.execute(getAnswersSQL, (userId, questionNumber))
    return c

def logAnswer(userId, questionNumber, inputString, result):
    createAnswerSQL = "INSERT INTO answers(userid, questionNumber, inputs, result) values (?, ?, ?, ?)"
    c = database.cursor()
    with databaseWriteLock:
        c.execute(createAnswerSQL, (userId, questionNumber, inputString, result))
        database.commit()

def setUserProgress(userId, highestSolved):
    updateQnoSQL = "UPDATE users SET highestSolved=? WHERE id=?"
    with databaseWriteLock:
        c.execute(updateQnoSQL, (highestSolved, userId))
        database.commit()

#def requestNamedUser(name, password):
#    user = getUser(name)
#    if not user:
#        return None
#    if user.password == hashlib.sha512(password):
#        return user
#    return None
