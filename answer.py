
class answer:
    def __init__(self, inputs, result, question):
        self.inputs = (int(x) for x in inputs.split("|"))
        self.result = result
        if result == question.correctAnswer:
            self.correct = True
        else:
            self.correct = False

    def __str__(self):
        return "%3d = f(%s)"%(self.result, ", ".join("%3d"%(x) for x in self.inputs))
