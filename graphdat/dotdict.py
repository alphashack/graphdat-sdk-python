# thanks SO
# http://stackoverflow.com/questions/224026/javascript-style-dot-notation-for-dictionary-keys-unpythonic

class dotdict(dict):

    def __getattr__(self, attr):
        return self.get(attr, None)

    __setattr__= dict.__setitem__
    __delattr__= dict.__delitem__
