from sqlalchemy import Column, Integer, String, Text
from database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    goal = Column(Text, nullable=False)
    status = Column(String, default="pending")
    user_id = Column(Integer, nullable=True, index=True)
    workspace = Column(String, default="gmail")
    resource = Column(Text, nullable=True)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)


class Connection(Base):
    __tablename__ = "connections"

    id = Column(Integer, primary_key=True, index=True)
    service = Column(String, index=True)
    status = Column(String, default="connected")
    user_id = Column(Integer, nullable=False, index=True)
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    service = Column(String, index=True)
    action = Column(String)
    allowed = Column(Integer, default=0)
    user_id = Column(Integer, nullable=False, index=True)


class Approval(Base):
    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True, index=True)
    service = Column(String)
    action = Column(String)
    details = Column(Text, nullable=True)
    status = Column(String, default="pending")
    user_id = Column(Integer, nullable=False, index=True)
    task_id = Column(Integer, nullable=True, index=True)


class ToolActivity(Base):
    __tablename__ = "tool_activity"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, nullable=False, index=True)
    tool = Column(String)
    result = Column(Text)
    user_id = Column(Integer, nullable=False, index=True)