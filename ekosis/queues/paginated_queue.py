import json
import sqlalchemy

from typing import cast, Dict, List, Type, TypeVar, Generic

from pydantic import BaseModel as PydanticBaseModel

from sqlalchemy import create_engine, Column, BigInteger, BINARY, String, func, Table, MetaData, asc, desc, exists
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import sessionmaker
from ..data_transfer_objects import SpanKey

OrmBaseClass = sqlalchemy.orm.declarative_base()

_QueuedType = TypeVar('_QueuedType', bound=PydanticBaseModel)

# --------------------------------------------------------------------------------
class QueueRecord(OrmBaseClass):
    __tablename__  = 'queued_objects'
    record_id      = Column(BigInteger, primary_key=True)
    span_key       = Column(BINARY(24), unique=True, nullable=False)
    object_string  = Column(String)

# --------------------------------------------------------------------------------
class PageEntry(PydanticBaseModel):
    span_key     : SpanKey
    object_string: str

# --------------------------------------------------------------------------------
class QueuePage:
    def __init__(self, queued_type: Type[_QueuedType]):
        self.__page_data_dict: Dict[SpanKey, PageEntry] = {}
        self.__page_data_list: List[PageEntry]          = []
        self.__queued_type   : Type[_QueuedType]        = queued_type

    def __append_entry(self, entry: PageEntry):
        self.__page_data_list.append(entry)
        self.__page_data_dict[entry.span_key] = entry

    @staticmethod
    def __make_entry(object_to_queue: _QueuedType, span_key: SpanKey) -> PageEntry:
        return PageEntry(
            span_key      = span_key,
            object_string = object_to_queue.model_dump_json()
        )

    def __entry_to_queueable_object(self, entry: PageEntry) -> _QueuedType:
        queued_data = json.loads(entry.object_string)
        return self.__queued_type(**queued_data)

    def push(self, object_to_queue: _QueuedType, span_key: SpanKey) -> SpanKey:
        return self.push_back(object_to_queue, span_key)

    def push_with_str(self, data: str, span_key: SpanKey) -> SpanKey:
        entry = PageEntry(
            span_key      = span_key,
            object_string = data
        )
        self.__append_entry(entry)
        return entry.span_key

    def pop(self) -> _QueuedType | None:
        return self.pop_front()

    def push_back(self, object_to_queue: _QueuedType, span_key: SpanKey) -> SpanKey:
        entry = self.__make_entry(object_to_queue, span_key)
        self.__append_entry(entry)
        return entry.span_key

    def pop_front(self):
        if self.size() < 1:
            return None
        entry = self.__page_data_list.pop(0)
        self.__page_data_dict.pop(entry.span_key)
        return self.__entry_to_queueable_object(entry)

    def size(self):
        return len(self.__page_data_list)

    def get_page_list(self):
        return self.__page_data_list

    def has_entry(self, span_key: SpanKey):
        return span_key in self.__page_data_dict.keys()

    def inspect_entry(self, span_key: SpanKey):
        if span_key not in self.__page_data_dict.keys():
            return None

        return self.__entry_to_queueable_object(self.__page_data_dict[span_key])

    def pop_entry(self, span_key: SpanKey):
        if span_key not in self.__page_data_dict.keys():
            return None

        entry           = self.__page_data_dict.pop(span_key)
        index_to_remove = -1
        for i in range(len(self.__page_data_list)):
            if entry.span_key == self.__page_data_list[i].span_key:
                index_to_remove = i
        self.__page_data_list.pop(index_to_remove)
        return self.__entry_to_queueable_object(entry)

    def get_first_x_span_keys(self, how_many: int):
        retval: List[str] = []
        this_page_size = self.size()
        if this_page_size > 0:
            if this_page_size < how_many:
                for x in range(this_page_size):
                    retval.append(str(self.__page_data_list[x].span_key))
            else:
                for x in range(how_many):
                    retval.append(str(self.__page_data_list[x].span_key))
        return retval

# --------------------------------------------------------------------------------
class PaginatedQueue(Generic[_QueuedType]):
    def __init__(
        self,
        file_path  : str,
        queued_type: Type[_QueuedType],
        page_size  : int = 100,
    ):
        self.file_path        : str               = file_path
        self.connection_string: str               = f"sqlite:///{file_path}"
        self.database_engine  : sqlalchemy.Engine = create_engine(self.connection_string)
        self.queued_type      : Type[_QueuedType] = queued_type
        self.page_size        : int               = page_size
        self.front_page       : QueuePage         = QueuePage(queued_type)
        self.back_page        : QueuePage         = self.front_page

        OrmBaseClass.metadata.create_all(self.database_engine)

        self.session = sessionmaker(bind=self.database_engine, autoflush=False)()
        self.__do_initial_load()

    # --------------------------------------------------------------------------------
    def __do_initial_load(self):
        if self.__get_database_size() > 0:
            self.__load_front_page()

        if self.__get_database_size() > 0: # If there is still data AFTER loading the front page.
            self.back_page = QueuePage(self.queued_type)
            self.__load_back_page()

    # --------------------------------------------------------------------------------
    def __get_max_record_id(self) -> int:
        if self.__get_database_size() < 1:
            return 0
        return int(self.session.query(func.max(QueueRecord.record_id)).scalar())

    # --------------------------------------------------------------------------------
    def __get_min_record_id(self) -> int:
        if self.__get_database_size() < 1:
            return 0
        return int(self.session.query(func.min(QueueRecord.record_id)).scalar())

    # --------------------------------------------------------------------------------
    def __delete_record_ids(self, record_ids: List[int]):
        self.session.\
            query(QueueRecord).\
            filter(QueueRecord.record_id.in_(record_ids)).\
            delete(synchronize_session='fetch')
        self.session.commit()

    # --------------------------------------------------------------------------------
    def __load_front_page(self):
        records = self.session.\
            query(QueueRecord).\
            order_by(asc(QueueRecord.record_id)).\
            limit(self.page_size).all()

        for record in records:
            self.front_page.push_with_str(str(record.object_string), SpanKey.from_bytes(record.span_key))
        ids_to_delete: List[int] = [int(x.record_id) for x in records]
        self.__delete_record_ids(ids_to_delete)

    # --------------------------------------------------------------------------------
    def __load_back_page(self):
        records = self.session.\
            query(QueueRecord).\
            order_by(desc(QueueRecord.record_id)).\
            limit(self.page_size).all()

        for record in records:
            self.back_page.push_with_str(str(record.object_string), SpanKey.from_bytes(record.span_key))
        ids_to_delete: List[int] = [int(x.record_id) for x in records]
        self.__delete_record_ids(ids_to_delete)

    # --------------------------------------------------------------------------------
    def __write_front_page(self):
        page_data     = list(reversed(self.front_page.get_page_list()))
        min_record_id = self.__get_min_record_id() - 1
        data_to_write = []
        for entry in page_data:
            data_to_write.append(QueueRecord(
                record_id    = min_record_id,
                span_key     = entry.span_key.bytes,
                object_string= entry.object_string
            ))
            min_record_id -= 1
        self.session.bulk_save_objects(data_to_write)
        self.session.commit()
        self.front_page = QueuePage(self.queued_type)

    # --------------------------------------------------------------------------------
    def __write_back_page(self):
        page_data     = self.back_page.get_page_list()
        max_record_id = self.__get_max_record_id() + 1
        data_to_write = []
        for entry in page_data:
            data_to_write.append(QueueRecord(
                record_id    = max_record_id,
                span_key     = entry.span_key.bytes,
                object_string= entry.object_string
            ))
            max_record_id += 1
        self.session.bulk_save_objects(data_to_write)
        self.session.commit()
        self.back_page = QueuePage(self.queued_type)

    # --------------------------------------------------------------------------------
    def __get_database_size(self):
        return self.session.query(QueueRecord).count()

    # --------------------------------------------------------------------------------
    def __get_record_by_span_key(self, span_key: SpanKey) -> QueueRecord|None:
        try:
            record = self.session.\
                query(QueueRecord).\
                filter(QueueRecord.span_key == span_key.bytes).\
                one()
            return cast(QueueRecord, record)
        except NoResultFound:
            return None

    # --------------------------------------------------------------------------------
    def __check_record_exists(self, span_key: SpanKey) -> bool:
        return self.session.\
            query(exists().where(QueueRecord.span_key == span_key.bytes)).\
            scalar()

    # --------------------------------------------------------------------------------
    async def pop(self):
        if self.front_page.size() > 0:
            return self.front_page.pop()
        elif self.__get_database_size() > 0:
            self.__load_front_page()
            return self.front_page.pop()
        elif self.back_page.size() > 0:
            self.front_page = self.back_page
            return self.front_page.pop()
        else:
            self.front_page = self.back_page
            return None

    # --------------------------------------------------------------------------------
    async def push(self, object_to_queue: _QueuedType, span_key: SpanKey) -> SpanKey:
        if (self.back_page.has_entry(span_key)  or
            self.front_page.has_entry(span_key) or
            self.__check_record_exists(span_key)):
            return span_key

        if self.back_page.size() < self.page_size:
            return self.back_page.push(object_to_queue, span_key)
        elif self.back_page is self.front_page:
            self.back_page = QueuePage(self.queued_type)
            return self.back_page.push(object_to_queue, span_key)
        else:
            self.__write_back_page()
            return self.back_page.push(object_to_queue, span_key)

    # --------------------------------------------------------------------------------
    def size(self):
        total = self.__get_database_size()
        if self.front_page is self.back_page:
            total += self.front_page.size()
        else:
            front_size = self.front_page.size()
            back_size  = self.back_page.size()
            total     += front_size + back_size
        return total

    # --------------------------------------------------------------------------------
    async def inspect_span_key(self, span_key: SpanKey):
        if self.front_page.has_entry(span_key):
            return self.front_page.inspect_entry(span_key)

        if self.back_page.has_entry(span_key):
            return self.back_page.inspect_entry(span_key)

        record = self.__get_record_by_span_key(span_key)
        if record is None:
            return None
        queued_data = json.loads(record.object_string)
        return self.queued_type(**queued_data)

    # --------------------------------------------------------------------------------
    async def pop_span_key(self, span_key: SpanKey):
        if self.front_page.has_entry(span_key):
            return self.front_page.pop_entry(span_key)

        if self.back_page.has_entry(span_key):
            return self.back_page.pop_entry(span_key)

        record = self.__get_record_by_span_key(span_key)
        if record is None:
            return None
        queued_data = json.loads(record.object_string)
        self.session.delete(record)
        self.session.commit()
        return self.queued_type(**queued_data)

    # --------------------------------------------------------------------------------
    def is_empty(self) -> int:
        return self.size() == 0

    # TODO: There is a bug with this:
    #   - When there are fewer then the requested amount of items in the queue.
    #   - It is currently possible for entries to be spread between front page, database
    #   - and back page. And this only reports on what is in the front page.
    # --------------------------------------------------------------------------------
    async def get_first_x_span_keys(self, how_many: int = 1) -> List[str]:
        return self.front_page.get_first_x_span_keys(how_many)

    # --------------------------------------------------------------------------------
    async def clear(self):
        metadata = MetaData()
        table    = Table("queued_objects", metadata, autoload_with=self.database_engine)
        self.session.query(table).filter(table.c.record_id > 0).delete()
        self.session.query(table).filter(table.c.record_id < 0).delete()
        self.session.query(table).filter(table.c.record_id == 0).delete()
        self.session.commit()
        self.front_page = QueuePage(self.queued_type)
        self.back_page  = self.front_page

    # --------------------------------------------------------------------------------
    def shut_down(self):
        if self.front_page is self.back_page:
            if self.front_page.size() > 0:
                self.__write_front_page()
        else:
            if self.front_page.size() > 0:
                self.__write_front_page()

            if self.back_page.size() > 0:
                self.__write_back_page()
        self.session.close()
