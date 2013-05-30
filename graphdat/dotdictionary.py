
__all__ = ['DotDictionary']

class DotDictionary(dict):

    """
    Extend the dictionary to add dot notation, nice and simple
    http://stackoverflow.com/questions/224026/javascript-style-dot-notation-for-dictionary-keys-unpythonic
    """

    def __getattr__(self, attr):
        return self.get(attr, None)

    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__
