import uuid
import sqlalchemy

from typing import cast, Any

from sqlalchemy import create_engine, Column, BINARY, String, Float, BigInteger, func
from sqlalchemy.orm import sessionmaker

from ekosis.util.singleton import SingletonType

OrmBaseClass = sqlalchemy.orm.declarative_base()


# --------------------------------------------------------------------------------
class LogRecord(OrmBaseClass):
    __tablename__      = 'tracker_logs'
    record_id          = Column(BigInteger, primary_key=True)
    uid                = Column(BINARY(16), unique=True, index=True, nullable=False, default=uuid.uuid4().bytes)
    request_message    = Column(String)
    request_timestamp  = Column(Float)
    response_message   = Column(String, nullable=True)
    response_timestamp = Column(Float, nullable=True)


# --------------------------------------------------------------------------------
class LogDatabase(metaclass=SingletonType):
    file_path        : str               = None
    connection_string: str               = None
    database_engine  : sqlalchemy.Engine = None
    session          : Any               = None
    initialised      : bool              = False

    # --------------------------------------------------------------------------------
    def initialise(self, file_path: str):
        self.file_path         = file_path
        self.connection_string = f"sqlite:///{file_path}"
        self.database_engine   = create_engine(self.connection_string)
        OrmBaseClass.metadata.create_all(self.database_engine)
        self.session           = sessionmaker(bind=self.database_engine)()
        self.initialised       = True

    # --------------------------------------------------------------------------------
    def log_request(
        self,
        uid              : uuid.UUID,
        request_message  : str,
        request_timestamp: float,
    ):
        new_record = LogRecord(
            record_id         = self.__get_max_record_id() + 1,
            uid               = uid.bytes,
            request_message   = request_message,
            request_timestamp = request_timestamp
        )
        self.session.add(new_record)
        self.session.commit()

    # --------------------------------------------------------------------------------
    def log_response(
        self,
        uid               : uuid.UUID,
        response_message  : str,
        response_timestamp: float
    ):
        log_record = cast(
            LogRecord,
            self.session.query(LogRecord).filter(LogRecord.uid == uid.bytes).one() # noqa PyCharm's report that the equality check has a problem is a false positive.
        )
        log_record.response_message   = response_message
        log_record.response_timestamp = response_timestamp
        self.session.add(log_record)
        self.session.commit()

    # --------------------------------------------------------------------------------
    def size(self) -> int:
        return int(self.session.query(func.count(LogRecord.record_id)).scalar())

    # --------------------------------------------------------------------------------
    def __get_max_record_id(self) -> int:
        if self.size() < 1:
            return 0
        return int(self.session.query(func.max(LogRecord.record_id)).scalar())
