from sqlalchemy import Column, Integer, String, DateTime, Enum
from datetime import datetime
from database import Base


class Video(Base):
    __tablename__ = 'video'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    thumbnail = Column(String)
    rtmp = Column(String)
    url = Column(String)
    lang = Column(String)
    quality = Column(String)
    date = Column(DateTime)

    state = Column(Enum("NEW", "LOADING", "CONVERTING", "COMPLETE", "FAIL"), default="NEW")
    enqueued = Column(DateTime, default=datetime.now)

    def json_repr(self):
        json_attrs = ["id", "name", "thumbnail", "url", "enqueued", "date", "quality", "lang", "state"]
        json_dict = {}
        for attr in json_attrs:
            value = getattr(self, attr)
            if isinstance(value, datetime):
                value = value.strftime("%Y-%m-%d %H:%M")
            json_dict[attr] = value

        return json_dict

    def __repr__(self):
        return '<Video %r>' % (self.name)