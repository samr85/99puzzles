import threading
import tornado.web
import tornado.websocket
import json
import os
import random
import argparse

import questions
import questionList
import database

class register(tornado.web.RequestHandler):
    def renderPage(message = ""):
        self.render(os.path.join("www", "register.html"), message=message)

    def get(self):
        self.renderPage()

    def post(self):
        newName = self.get_body_argument("username")
        password = self.get_body_argument("password")
        confirmPassword = self.get_body_argument("confirmPassword")
        if password != confirmPassword:
            return self.renderPage("password and confirmed password do not match!")

        userName = self.get_secure_cookie("user", max_age_days=36524)  # Must specify a max_age... 100 years
        if not userName:
            userName = "%06x"%(random.randint(1, 0xffffff))
            self.set_secure_cookie("user", userName, expires_days=None)
        user = database.getUser(userName)
        ret = user.nameUser(newName, password)
        if ret:
            self.set_secure_cookie("user", newName, expires_days=None)
            return self.redirect("/")
        else:
            return self.renderPage("Username %s already exists"%(userName))

class login(tornado.web.RequestHandler):
    def renderPage(message = ""):
        self.render(os.path.join("www", "login.html"), message=message)
    
    def get(self):
        self.renderPage()

    def post(self):
        newName = self.get_body_argument("username")
        password = self.get_body_argument("password")
        ret = database.requestNamedUser(newName, password)
        if ret:
            self.set_secure_cookie("user", newName, expires_days=None)
            return self.redirect("/")
        return self.renderPage("Username or password incorrect")

class logout(tornado.web.RequestHandler):
    def get(self):
        self.clear_all_cookies()

class puzzle(tornado.web.RequestHandler):

    def checkAnswer(self, user, question):
        A = []
        for i in range(question.numInputs):
            try:
                A.append(int(self.get_body_argument("A%d" % (i))))
            except ValueError:
                A.append(0)
            if A[i] == None:
                raise tornado.web.HTTPError(400, "No answer submitted in position %d" % (i))
        ret = question.calcCheck(user, A)
        user.logAnswer(question, A, ret)
        print("Q: %d User: %s got %s by submitting: %s"%(question.qNo, user.name, ret, ", ".join("%s"%(x) for x in A)))
        if ret == question.correctAnswer:
            return True
        return False

    def getUserAndQuestion(self):
        userName = self.get_secure_cookie("user", max_age_days=36524)  # Must specify a max_age... 100 years
        if not userName:
            print("userName not set, creating")
            userName = "%06x"%(random.randint(1, 0xffffff))
            self.set_secure_cookie("user", userName, expires_days=None)
        self.user = database.getUser(userName, create=True)

        # What question are they interested in?
        qNoStr = self.get_query_argument("qNo", default = None)

        if qNoStr == None:
            qNo = self.user.highestSolved + 1
            print("qNo not set, using highest available qNo (%d)"%(qNo))
        else:
            try:
                qNo = int(qNoStr)
            except ValueError:
                raise tornado.web.HTTPError(400, "Invalid question number: %s"%(qNoStr))
            if qNo > self.user.highestSolved + 1:
                raise tornado.web.HTTPError(400, "Cannot request a question you've not earnt!")
        if questions.lastQuestion() < qNo:
            qNo = questions.lastQuestion()
        self.question = questions.getQuestion(qNo)

    def post(self):
        self.getUserAndQuestion()

        # Submit an answer
        justAnswered = self.checkAnswer(self.user, self.question)
        self.render(os.path.join("www", "Puzzle.html"), range=range, title="99 puzzles", question = self.question, user=self.user, justAnswered = justAnswered)

    def get(self):
        self.getUserAndQuestion()
        self.render(os.path.join("www", "Puzzle.html"), range=range, title="99 puzzles", question = self.question, user=self.user, justAnswered = False)
        

def startServer():
    server_thread = threading.Thread(target=tornado.ioloop.IOLoop.instance().start)
    # Exit the server thread when the main thread terminates
    server_thread.daemon = True
    server_thread.start()

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Runs 99puzzles webserver")
    parser.add_argument("--debug", "-d", action="store_true", help="Run in debug mode, default port 9091")
    args = parser.parse_args()

    settings={
        "debug": args.debug,
        "static_path": os.path.join(os.path.dirname(__file__), os.path.join("www", "static")),
        "cookie_secret": "123",
        "autoreload": False
        }
    application = tornado.web.Application([
        (r"/", puzzle),
        ], **settings)

    if args.debug:
        application.listen(9091)
    else:
        application.listen(80)

    startServer()
    import readline
    import rlcompleter
    import code
    readline.parse_and_bind("tab: complete")
    code.interact(local=locals())
    tornado.ioloop.IOLoop.instance().stop()