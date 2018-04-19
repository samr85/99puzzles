import database
import questions
from answer import answer

class userState:
    def __init__(self, databaseEntry):
        if databaseEntry:
            self.name = databaseEntry['username'].decode()
            #self.named = databaseEntry['named']
            #self.password = databaseEntry['passwordHash']
            self.highestSolved = databaseEntry['highestSolved']
            self.id=databaseEntry['id']
        else:
            self.name = None
            self.highestSolved = -1
            self.id = -1

    def getAnswers(self, question):
        c = database.getAnswers(self.id, question.qNo)
        ret = []
        for row in c:
            ret.append(answer(row['inputs'], row['result'], question))
        return ret

    def logAnswer(self, question, inputs, result):
        database.logAnswer(self.id, question.qNo, "|".join(str(x) for x in inputs), str(result))
        if result == question.correctAnswer:
            print("Correct answer submitted: %d, highest: %d"%(question.qNo, self.highestSolved))
            if question.qNo == self.highestSolved + 1:
                print("incrementing highestSolved")
                self.highestSolved = question.qNo
                database.setUserProgress(self.id, self.highestSolved)

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
    dbEntry = database.getUser(name)
    if not dbEntry:
        if not create:
            return userState(None)
        # Create a new database entry for us
        dbEntry = database.createUser(name)
        if not dbEntry:
            raise AssertionError("User still doesn't exist after just creating it????")
    return userState(dbEntry)