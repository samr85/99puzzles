from collections import defaultdict
import questions
import pickle
import hashlib

class answer:
    def __init__(self, inputs, result):
        self.inputs = inputs
        self.result = result

    def __str__(self):
        "%3d = f(%s)"%(self.result, ", ".join("%3d"%(x) for x in self.inputs))

class userState:
    def __init__(self, name):
        self.name = name
        self.named = False
        self.password = None
        self.highestSolved = -1
        self.answers = defaultdict(list)

    def logAnswer(self, question, inputs, result):
        self.answers[question.qNo].append(answer(inputs, result))
        if result == question.correctAnswer:
            print("Correct answer submitted: %d, highest: %d"%(question.qNo, self.highestSolved))
            if question.qNo == self.highestSolved + 1:
                print("incrementing highestSolved")
                self.highestSolved = question.qNo

    def availableQuestions(self):
        lastQuestion = min(questions.lastQuestion(), self.highestSolved + 1)
        return range(0, lastQuestion + 1)

    def nameUser(self, newName, password):
        if newName in users:
            return False
        users.pop(self.name)
        self.name = newName
        users[newName] = self
        self.password = hashlib.sha512(password)

users = {}

def getNullUser():
    return userState(None)

def getUser(name, create = False):
    if name in users:
        return users[name]
    if create:
        newUser = userState(name)
        users[name] = newUser
        return newUser
    return None

def requestNamedUser(name, password):
    user = getUser(name)
    if not user:
        return None
    if user.password == hashlib.sha512(password):
        return user
    return None
