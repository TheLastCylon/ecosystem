import json
import uuid
import sqlalchemy

from typing import Type, cast, TypeVar, Generic, List

from pydantic import BaseModel as PydanticBaseModel

from sqlalchemy import create_engine, Column, BigInteger, BINARY, String, func, Table, MetaData
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import sessionmaker


OrmBaseClass = sqlalchemy.orm.declarative_base()

_QueuedType = TypeVar('_QueuedType', bound=PydanticBaseModel)


# --------------------------------------------------------------------------------
class QueueRecord(OrmBaseClass):
    __tablename__ = 'queued_objects'
    record_id     = Column(BigInteger, primary_key=True)
    record_uuid   = Column(BINARY(16), unique=True, index=True, nullable=False, default=uuid.uuid4().bytes)
    object_string = Column(String)


# --------------------------------------------------------------------------------
class SqlPersistedQueueBase:
    def __init__(self, file_path: str):
        self.file_path        : str               = file_path
        self.connection_string: str               = f"sqlite:///{file_path}"
        self.database_engine  : sqlalchemy.Engine = create_engine(self.connection_string)

        OrmBaseClass.metadata.create_all(self.database_engine)

        self.session = sessionmaker(bind=self.database_engine, autoflush=False)()


# --------------------------------------------------------------------------------
class SqlPersistedQueue(Generic[_QueuedType], SqlPersistedQueueBase):
    def __init__(
        self,
        file_path     : str,
        queued_type   : Type[_QueuedType],
        max_uncommited: int = 0,
    ):
        super().__init__(file_path)
        self.max_uncommited  : int               = max_uncommited
        self.uncommited_count: int               = 0
        self.queued_type     : Type[_QueuedType] = queued_type

    # --------------------------------------------------------------------------------
    def shut_down(self):
        self.session.commit()
        self.uncommited_count = 0
        self.session.close()

    # --------------------------------------------------------------------------------
    # Note:
    # Because SQLite defines BIGINT as signed, and can deal with negative values
    # in a primary key. We genuinely don't have to be concerned about dealing with
    # a minimum record id here. Thankyou SQLite guys. I Love your work!
    async def push_front(self, object_to_queue: _QueuedType, uid: uuid.UUID = None) -> uuid.UUID :
        queued_record = self.__get_record_by_uuid(uid)
        if queued_record is not None:
            return uid

        queue_uuid = uid or uuid.uuid4()
        new_record = QueueRecord(
            record_uuid   = queue_uuid.bytes,
            object_string = object_to_queue.model_dump_json()
        )
        new_record.record_id = self.__get_min_record_id() - 1
        self.session.add(new_record)
        self.session.commit()
        return queue_uuid

    # --------------------------------------------------------------------------------
    async def push_back(self, object_to_queue: _QueuedType, uid: uuid.UUID = None) -> uuid.UUID:
        queued_record = self.__get_record_by_uuid(uid)
        if queued_record is not None:
            return uid

        queue_uuid = uid or uuid.uuid4()
        new_record = QueueRecord(
            record_uuid   = queue_uuid.bytes,
            object_string = object_to_queue.model_dump_json()
        )
        new_record.record_id = self.__get_max_record_id() + 1
        self.session.add(new_record)
        self.session.commit()
        return queue_uuid

    # --------------------------------------------------------------------------------
    async def pop_front(self):
        queued_record = self.__get_record_with_lowest_record_id()
        if queued_record is None:
            return None
        queueable_type_object = self.__record_to_queueable_object(queued_record)
        self.session.delete(queued_record)
        self.session.commit()
        return queueable_type_object

    # --------------------------------------------------------------------------------
    async def pop_back(self):
        queued_record = self.__get_record_with_highest_record_id()
        if queued_record is None:
            return None
        queueable_type_object = self.__record_to_queueable_object(queued_record)
        self.session.delete(queued_record)
        self.session.commit()
        return queueable_type_object

    # --------------------------------------------------------------------------------
    async def pop_uuid(self, object_uuid: uuid.UUID):
        queued_record = self.__get_record_by_uuid(object_uuid)
        if queued_record is None:
            return None
        queueable_type_object = self.__record_to_queueable_object(queued_record)
        self.session.delete(queued_record)
        self.session.commit()
        return queueable_type_object

    # --------------------------------------------------------------------------------
    async def inspect_front(self):
        queued_record = self.__get_record_with_lowest_record_id()
        if queued_record is None:
            return None
        return self.__record_to_queueable_object(queued_record)

    # --------------------------------------------------------------------------------
    async def inspect_back(self):
        queued_record = self.__get_record_with_highest_record_id()
        if queued_record is None:
            return None
        return self.__record_to_queueable_object(queued_record)

    # --------------------------------------------------------------------------------
    async def inspect_uuid(self, object_uuid: uuid.UUID):
        queued_record = self.__get_record_by_uuid(object_uuid)
        if queued_record is None:
            return None
        return self.__record_to_queueable_object(queued_record)

    # --------------------------------------------------------------------------------
    def size(self) -> int:
        # return int(self.session.query(func.count(QueueRecord.record_id)).scalar())
        return self.session.query(QueueRecord).count()

    # --------------------------------------------------------------------------------
    def is_empty(self) -> int:
        return self.size() == 0

    # --------------------------------------------------------------------------------
    async def get_first_x_uuids(self, how_many: int = 1) -> List[str]:
        response: List[str] = []
        queued_records      = self.session.query(QueueRecord).limit(how_many).all()
        for record in queued_records:
            response.append(str(uuid.UUID(bytes=record.record_uuid)))
        return response

    # --------------------------------------------------------------------------------
    async def clear(self):
        metadata = MetaData()
        table    = Table("queued_objects", metadata, autoload_with=self.database_engine)
        self.session.query(table).filter(table.c.record_id > 0).delete()
        self.session.query(table).filter(table.c.record_id < 0).delete()
        self.session.query(table).filter(table.c.record_id == 0).delete()
        self.session.commit()
        self.uncommited_count = 0

    # --------------------------------------------------------------------------------
    def __get_min_record_id(self) -> int:
        if self.size() < 1:
            return 0
        return int(self.session.query(func.min(QueueRecord.record_id)).scalar())

    # --------------------------------------------------------------------------------
    def __get_max_record_id(self) -> int:
        if self.size() < 1:
            return 0
        return int(self.session.query(func.max(QueueRecord.record_id)).scalar())

    # --------------------------------------------------------------------------------
    def __get_record_by_record_id(self, record_id: int) -> QueueRecord | None:
        try:
            # cast is used here to stop some IDEs from thinking that the query returns Type[QueueRecord] rather than QueueRecord
            return cast(
                QueueRecord,
                self.session.query(QueueRecord).filter(QueueRecord.record_id == record_id).one() # noqa PyCharm's report that the equality check has a problem is a false positive.
            )
        except NoResultFound:
            return None

    # --------------------------------------------------------------------------------
    def __get_record_by_uuid(self, record_uuid: uuid.UUID) -> QueueRecord | None:
        try:
            # cast is used here to stop some IDEs from thinking that the query returns Type[QueueRecord] rather than QueueRecord
            return cast(
                QueueRecord,
                self.session.query(QueueRecord).filter(QueueRecord.record_uuid == record_uuid.bytes).one() # noqa PyCharm's report that the equality check has a problem is a false positive.
            )
        except NoResultFound:
            return None

    # --------------------------------------------------------------------------------
    def __get_record_with_lowest_record_id(self) -> QueueRecord | None:
        if self.size() < 1:
            return None
        return self.__get_record_by_record_id(self.__get_min_record_id())

    # --------------------------------------------------------------------------------
    def __get_record_with_highest_record_id(self) -> QueueRecord | None:
        if self.size() < 1:
            return None
        return self.__get_record_by_record_id(self.__get_max_record_id())

    # --------------------------------------------------------------------------------
    def __record_to_queueable_object(self, record: QueueRecord) -> _QueuedType:
        queued_data = json.loads(record.object_string)
        return self.queued_type(**queued_data)

    # --------------------------------------------------------------------------------
    # async def __check_commit_count(self):
    #     # if self.uncommited_count >= self.max_uncommited:
    #     #     self.session.commit()
    #     #     self.uncommited_count = 0
    #     return
