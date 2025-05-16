from datetime import datetime, timezone
import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase
from sqlalchemy import DateTime


class Rating(SqlAlchemyBase):
    __tablename__ = 'ratings'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
    news_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('news.id'))
    value = sqlalchemy.Column(sqlalchemy.Integer)
    created_at = sqlalchemy.Column(DateTime, default=datetime.now)
    user = orm.relationship("User", back_populates="ratings")
    news = orm.relationship("News", back_populates="ratings")


class News(SqlAlchemyBase):
    __tablename__ = 'news'
    
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    content = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.now)
    is_private = sqlalchemy.Column(sqlalchemy.Boolean, default=True)
    file_path = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    user = orm.relationship('User', back_populates="news")
    ratings = orm.relationship('Rating', back_populates="news")
    categories = orm.relationship("Category", secondary="association", backref="news")
    
    def rating_score(self):
        return sum(rating.value for rating in self.ratings) if self.ratings else 0
