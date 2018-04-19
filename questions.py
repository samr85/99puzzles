import database
questionList = {}

def registerQuestion(questionClass):
    question.qNo += 1
    qNo = question.qNo
    newQ = questionClass()
    newQ.qNo = qNo
    questionList[qNo] = newQ

def getQuestion(qNo):
    if qNo in questionList:
        return questionList[qNo]
    raise ValueError("Invalid question number: %s"%(qNo))

def lastQuestion():
    return question.qNo

def reloadQuestions():
    questionList.clear()
    question.qNo = -1
    import imp
    import questionList
    imp.reload(questionList)


class question:
    qNo = -1

    def __init__(self):
        self.introductionHTML = ""
        self.completionHTML = ""
        self.correctAnswer = 99
        self.numInputs = 1
        self.qNo = 0

    def getUserData(self, user):
        return database.getExtraData("%s-%d"%(user.name, self.qNo))

    def setUserData(self, user, data):
        return database.setExtraData("%s-%d"%(user.name, self.qNo), data)

    def questionIntro(self, user):
        return self.introductionHTML

    def questionConclusion(self, user):
        return self.completionHTML

    def calcCheck(self, user, answerList):
        if len(answerList) != self.numInputs:
            raise ValueError("Invalid number of answers")
        return self.calc(user, answerList)

    def calc(self, user, x):
        return x[0]


# Questions must appear in this list in the correct order.
# Dummy example question
#@registerQuestion
class retX(question):
    def __init__(self):
        super().__init__()
        self.introductionHTML = "Welcome to the 99 puzzle hunt!  Your aim with all questions here is to work out how to get the mystery function to calculate 99"

    def calc(self, user, x):
        return x[0]
