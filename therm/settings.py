import os


class Default(object):
    POLL_INTERVAL = 60
    """Temp sensor polling interval in seconds."""
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DB_URL = os.environ.get("THERM_DB_URL")
    DB_UNAME = os.environ.get("THERM_DB_UNAME")
    DB_PASS = os.environ.get("THERM_DB_PASS")
    DB_NAME = "therm"
    LOG_DIR = "."

    SQS_QUEUE_NAME = "therm-heartbeat"
    SNS_TOPIC_NAME = "therm-alerts"
    HEARTBEAT_ALARM_NAME = "therm-heartbeat-stopped"
    ALARM_PERIOD = 600

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
    POLL_INTERVAL = 10
    ALARM_PERIOD = 300
    ENV = "Development"
    DEBUG = True


class Production(Default):
    ENV = "Production"
    DEBUG = False
