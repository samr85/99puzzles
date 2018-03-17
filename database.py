from collections import defaultdict
import questions
import hashlib
import sqlite3
from threading import RLock

database = sqlite3.connect("userdatabase.db", check_same_thread = False)
databaseWriteLock = RLock()
database.row_factory = sqlite3.Row

usersTableSyntax = "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, named INTEGER DEFAULT 0, passwordHash TEXT, highestSolved INTEGER DEFAULT -1)"
answersTableSyntax = "CREATE TABLE IF NOT EXISTS answers (id INTEGER PRIMARY KEY, time INTEGER(4) DEFAULT (strftime('%s','now')), userid INTEGER, questionNumber INTEGER, inputs TEXT, result TEXT)"

c = database.cursor()
c.execute(usersTableSyntax)
c.execute(answersTableSyntax)
database.commit()
c.close()

def dumpdb():
    ''' Purely for debugging - prints out the users and answers tables '''
    import prettytable
    c = database.cursor()
    print(prettytable.from_db_cursor(c.execute("SELECT * FROM users")))
    print(prettytable.from_db_cursor(c.execute("SELECT * FROM answers")))


class answer:
    def __init__(self, inputs, result, question):
        self.inputs = (int(x) for x in inputs.split("|"))
        self.result = result
        if result == question.correctAnswer:
            self.correct = True
        else:
            self.correct = False

    def __str__(self):
        "%3d = f(%s)"%(self.result, ", ".join("%3d"%(x) for x in self.inputs))

class userState:
    def __init__(self, databaseEntry):
        if databaseEntry:
            self.name = databaseEntry['username']
            #self.named = databaseEntry['named']
            #self.password = databaseEntry['passwordHash']
            self.highestSolved = databaseEntry['highestSolved']
            self.id=databaseEntry['id']
        else:
            self.name = None
            self.highestSolved = -1
            self.id = -1

    def getAnswers(self, question):
        getAnswersSQL = "SELECT inputs, result FROM answers WHERE userid=? AND questionNumber=? ORDER BY time"
        c = database.cursor()
        c.execute(getAnswersSQL, (self.id, question.qNo))
        ret = []
        for row in c:
            ret.append(answer(row['inputs'], row['result'], question))
        return ret

    def logAnswer(self, question, inputs, result):
        createAnswerSQL = "INSERT INTO answers(userid, questionNumber, inputs, result) values (?, ?, ?, ?)"
        c = database.cursor()
        with databaseWriteLock:
            c.execute(createAnswerSQL, (self.id, question.qNo, "|".join(str(x) for x in inputs), str(result)))
            database.commit()

        if result == question.correctAnswer:
            print("Correct answer submitted: %d, highest: %d"%(question.qNo, self.highestSolved))
            if question.qNo == self.highestSolved + 1:
                print("incrementing highestSolved")
                self.highestSolved = question.qNo
                updateQnoSQL = "UPDATE users SET highestSolved=? WHERE id=?"
                with databaseWriteLock:
                    c.execute(updateQnoSQL, (self.highestSolved, self.id))
                    database.commit()

    def availableQuestions(self):
        lastQuestion = min(questions.lastQuestion(), self.highestSolved + 1)
        return range(0, lastQuestion + 1)

    #def nameUser(self, newName, password):
    #    if newName in users:
    #        return False
    #    users.pop(self.name)
    #    self.name = newName
    #    users[newName] = self
    #    self.password = hashlib.sha512(password)

def getNullUser():
    return userState(None)

def getUser(name, create = True):
    getUserSQL = "SELECT * FROM users where username=?"
    c = database.cursor()
    c.execute(getUserSQL, (name, ))
    row = c.fetchone()
    if not row:
        if not create:
            return userState(None)
        # Create a new database entry for us
        createUserSQL = "INSERT INTO users(username) values (?)"
        with databaseWriteLock:
            c.execute(createUserSQL, (name, ))
            database.commit()
        c.execute(getUserSQL, (name, ))
        row = c.fetchone()
        if not row:
            raise AssertionError("User still doesn't exist after just creating it????")
    return userState(row)

#def requestNamedUser(name, password):
#    user = getUser(name)
#    if not user:
#        return None
#    if user.password == hashlib.sha512(password):
#        return user
#    return None
