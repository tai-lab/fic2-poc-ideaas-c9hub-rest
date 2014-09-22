from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.types import TypeDecorator, CHAR
import uuid


BASE = declarative_base()


class UUID(TypeDecorator):
    """Platform-independent GUID type.

    CHAR(32), storing as stringified hex values.

    """
    impl = CHAR

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % str(uuid.UUID(value))
            else:
                # hexstring
                return "%.32x" % value
            
    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            return uuid.UUID(value)


class Ide(BASE):
    __tablename__ = 'ide'
    id = Column(Integer, primary_key=True)
    display_name = Column(String(64))
    username = Column(String(32))
    password = Column(String(32))
    uuid = Column(UUID())
    container_id = Column(String(64))


    def __repr__(self):
        return '<Ide %d (%s)>' % (self.id, self.display_name)


from sqlalchemy import create_engine
engine = create_engine('sqlite:////tmp/c9hubapi.sqlite')
 
from sqlalchemy.orm import sessionmaker
session = sessionmaker()
session.configure(bind=engine)
BASE.metadata.create_all(engine)
