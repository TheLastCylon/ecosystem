import uuid
import logging
import sqlalchemy

from typing import Any

from sqlalchemy import create_engine, Column, BINARY, String, Float, BigInteger, func
from sqlalchemy.orm import sessionmaker

from ekosis.configuration.config_models import AppConfiguration
from ekosis.util.singleton import SingletonType

config       = AppConfiguration()
log          = logging.getLogger()
OrmBaseClass = sqlalchemy.orm.declarative_base()

# --------------------------------------------------------------------------------
class LogRecord(OrmBaseClass):
    __tablename__      = 'tracker_logs'
    record_id          = Column(BigInteger, primary_key=True)
    uid                = Column(BINARY(16), unique=True, index=True, nullable=False, default=uuid.uuid4().bytes)
    request_message    = Column(String, nullable=True)
    request_timestamp  = Column(Float , nullable=True)
    response_message   = Column(String, nullable=True)
    response_timestamp = Column(Float , nullable=True)

# --------------------------------------------------------------------------------
class LogDatabase(metaclass=SingletonType):
    connection_string: str               = None
    database_engine  : sqlalchemy.Engine = None
    session          : Any               = None
    initialised      : bool              = False

    # --------------------------------------------------------------------------------
    def initialise(self):
        if not self.initialised:
            self.connection_string = f"sqlite:///{config.extra['DB_FILE']}"
            self.database_engine   = create_engine(self.connection_string)
            OrmBaseClass.metadata.create_all(self.database_engine)
            self.session           = sessionmaker(bind=self.database_engine)()
            self.initialised       = True

    # --------------------------------------------------------------------------------
    def get_existing_record(self, uid: uuid.UUID) -> LogRecord:
        return self.session.query(LogRecord).filter_by(**{"uid": uid.bytes}).first()

    # --------------------------------------------------------------------------------
    def log_request(
        self,
        uid              : uuid.UUID,
        request_message  : str,
        request_timestamp: float,
    ):
        record_to_write = self.get_existing_record(uid)
        if record_to_write is not None:
            record_to_write.request_message   = request_message
            record_to_write.request_timestamp = request_timestamp
        else:
            record_to_write = LogRecord(
                record_id         = self.__get_max_record_id() + 1,
                uid               = uid.bytes,
                request_message   = request_message,
                request_timestamp = request_timestamp
            )
        self.session.add(record_to_write)
        self.session.commit()

    # --------------------------------------------------------------------------------
    def log_response(
        self,
        uid               : uuid.UUID,
        response_message  : str,
        response_timestamp: float
    ):
        record_to_write = self.get_existing_record(uid)
        if record_to_write is not None:
            record_to_write.response_message   = response_message
            record_to_write.response_timestamp = response_timestamp
        else:
            record_to_write = LogRecord(
                record_id          = self.__get_max_record_id() + 1,
                uid                = uid.bytes,
                response_message   = response_message,
                response_timestamp = response_timestamp
            )
        self.session.add(record_to_write)
        self.session.commit()

    # --------------------------------------------------------------------------------
    def size(self) -> int:
        return int(self.session.query(func.count(LogRecord.record_id)).scalar())

    # --------------------------------------------------------------------------------
    def __get_max_record_id(self) -> int:
        if self.size() < 1:
            return 0
        return int(self.session.query(func.max(LogRecord.record_id)).scalar())
