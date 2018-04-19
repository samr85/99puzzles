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
import users

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
        user = users.getUser(userName)
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

class dumpdb(tornado.web.RequestHandler):
    def get(self):
        self.write("<pre>" + database.dumpdb() + "<pre>")

class reload(tornado.web.RequestHandler):
    def get(self):
        questions.reloadQuestions()
        self.write("Questions reloaded")

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

    def getUser(self, create = False):
        userName = self.get_secure_cookie("user", max_age_days=36524)  # Must specify a max_age... 100 years
        if not userName:
            if create:
                userName = ("%06x" % (random.randint(1, 0xffffff))).encode()
                self.set_secure_cookie("user", userName, expires_days=100)
            else:
                return users.getNullUser()

        return users.getUser(userName)

    def getQuestion(self, user):
        # Have they specified a question?
        qNoStr = self.get_query_argument("qNo", default = None)
        if qNoStr:
            try:
                qNo = int(qNoStr)
            except ValueError:
                raise tornado.web.HTTPError(400, "Invalid question number: %s"%(qNoStr))
            if qNo > user.highestSolved + 1:
                raise tornado.web.HTTPError(400, "Cannot request a question you've not earnt!")
        else:
            # Is this a registered user?
            if user:
                qNo = user.highestSolved + 1
                if qNo > questions.lastQuestion():
                    qNo = questions.lastQuestion()
                print("qNo not set, using highest available qNo (%d)"%(qNo))
            else:
                qNo = 1

        return questions.getQuestion(qNo)

    def post(self):
        user = self.getUser(create = True)
        question = self.getQuestion(user)

        # Submit an answer
        justAnswered = self.checkAnswer(user, question)
        self.render(os.path.join("www", "Puzzle.html"), range=range, title="99 puzzles", question = question, user=user, justAnswered = justAnswered)

    def get(self):
        user = self.getUser()
        question = self.getQuestion(user)
        self.render(os.path.join("www", "Puzzle.html"), range=range, title="99 puzzles", question = question, user=user, justAnswered = False)
        
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
        (r"/dumpdb", dumpdb),
        (r"/reload", reload)
        ], **settings)

    if args.debug:
        application.listen(9091)
        server_thread = threading.Thread(target=tornado.ioloop.IOLoop.instance().start)
        # Exit the server thread when the main thread terminates
        server_thread.daemon = True
        server_thread.start()

        import readline
        import rlcompleter
        import code
        readline.parse_and_bind("tab: complete")
        d=database.printdb
        code.interact(local=locals())
        tornado.ioloop.IOLoop.instance().stop()
    else:
        application.listen(80)
        tornado.ioloop.IOLoop.instance().start()
