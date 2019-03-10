class Default(object):
    pass

class Development(Default):
    DEBUG = True

class Production(Default):
    DEBUG = False