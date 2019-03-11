import os


class Default(object):
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DB_URL = os.environ.get("THERM_DB_URL")
    DB_UNAME = os.environ.get("THERM_DB_UNAME")
    DB_PASS = os.environ.get("THERM_DB_PASS")
    DB_NAME = "therm"
    LOG_DIR = "."

    def __init__(self):
        self.SQLALCHEMY_DATABASE_URI = "postgresql://{}:{}@{}:5432/{}".format(
            self.DB_UNAME, self.DB_PASS, self.DB_URL, self.DB_NAME
        )


class Test(Default):
    ENV = "Test"
    TESTING = True
    DB_NAME = "test"

    def __init__(self):
        super().__init__()
        self.SQLALCHEMY_DATABASE_URI = "sqlite:///test.db"


class Development(Default):
    ENV = "Development"
    DEBUG = True


class Production(Default):
    ENV = "Production"
    DEBUG = False
