
class Message:
    def __init__(self, msg):
        self.message = msg


RDFTriples = list   # list of RDFTriple objects


class RDFTriple:
    def __init__(self, subj, pred, obj):
        self.subject = subj
        self.predicate = pred
        self.object = obj

    def to_tuple(self):
        return self.subject, self.predicate, self.object


class EndMessage(Message):
    pass
