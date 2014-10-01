from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, UnicodeText, ForeignKey
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.orm import relationship
import logging, uuid
from urllib.parse import urlparse


logger = logging.getLogger(__name__)
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
    user_id = Column(String(64))
    validation_endpoint_id = Column(Integer, ForeignKey("validation_endpoint.id"), nullable=False)
    validation_endpoint = relationship("ValidationEndpoint")

    def __repr__(self):
        return '<Ide %d (%s)>' % (self.id, self.display_name)


class ValidationEndpoint(BASE):
    __tablename__ = 'validation_endpoint'
    id = Column(Integer, primary_key=True)
    url = Column(UnicodeText)
    uuid = Column(UUID())


from sqlalchemy import create_engine
engine = create_engine('sqlite:////tmp/c9hubapi.sqlite')
 
from sqlalchemy.orm import sessionmaker
session = sessionmaker()
session.configure(bind=engine)
BASE.metadata.create_all(engine)


def _register_validation_endpoints(validation_endpoints):
    this_session = session()
    logger.debug('>>> on: ' + str(validation_endpoints))
    for item in validation_endpoints:
        pu = urlparse(item)
        if pu.scheme != 'https' or not pu.netloc:
            logger.error('Ignoring the invalid validation endpoint "{}"'.format(item))
            continue
        if this_session.query(ValidationEndpoint).filter_by(url=pu.geturl()).first() is None:
            logger.debug('Registering the validation endpoint "{}"'.format(item))
            end = ValidationEndpoint(uuid=uuid.uuid4(), url=pu.geturl())
            this_session.add(end)
        else:
            logger.debug('Ignoring the already registered validation endpoint "{}"'.format(item))
    this_session.commit()
    this_session.close()
