from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table

Base = declarative_base()


class IdMixin:
    id = Column(Integer, autoincrement=True, primary_key=True)


class UrlMixin:
    url = Column(String, unique=True, nullable=False)


class NameMixin:
    name = Column(String, nullable=False)


tag_post = Table(
    "tag_post",
    Base.metadata,
    Column('post_id', Integer, ForeignKey("post.id")),
    Column('tag_id', Integer, ForeignKey("tag.id")),
)


class Post(IdMixin, UrlMixin, Base):
    __tablename__ = "post"
    title = Column(String, nullable=False)
    author_id = Column(Integer, ForeignKey("writer.id"))
    author = relationship("Writer")
    tags = relationship("Tag", secondary=tag_post)
    image = Column(String)  # в статье может не быть изображений
    date = Column(DateTime, nullable=False)
    comments = relationship("Comment")


class Writer(IdMixin, UrlMixin, NameMixin, Base):
    __tablename__ = "writer"
    posts = relationship("Post")
    comments = relationship("Comment")


class Tag(IdMixin, UrlMixin, NameMixin, Base):
    __tablename__ = "tag"
    posts = relationship("Post", secondary=tag_post)


class Comment(IdMixin, Base):
    __tablename__ = "comments"
    text = Column(String, nullable=False)
    comment_id = Column(Integer)
    author_id = Column(Integer, ForeignKey("writer.id"))
    author = relationship("Writer")
    post_id = Column(Integer, ForeignKey("post.id"))
    post = relationship("Post")
    parent_id = Column(Integer)
