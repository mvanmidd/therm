import os


class Default(object):
    DB_URL = os.environ.get("THERM_DB_URL")
    DB_UNAME = os.environ.get("THERM_DB_UNAME")
    DB_PASS = os.environ.get("THERM_DB_PASS")
    DB_NAME = "therm"

    def __init__(self):
        self.SQLALCHEMY_DATABASE_URI = "postgresql://{}:{}@{}:5432/{}".format(
            self.DB_UNAME, self.DB_PASS, self.DB_URL, self.DB_NAME
        )


class Test(Default):
    DB_NAME = "test"

    def __init__(self):
        super().__init__(self)
        self.SQLALCHEMY_DATABASE_URI = "sqlite:///test.db"


class Development(Default):
    DEBUG = True


class Production(Default):
    DEBUG = False
