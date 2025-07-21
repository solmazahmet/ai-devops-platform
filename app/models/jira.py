"""
Jira Integration Database Model
Jira issue'ları ve entegrasyon bilgileri
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class JiraIssue(Base):
    __tablename__ = "jira_issues"
    
    id = Column(Integer, primary_key=True, index=True)
    jira_key = Column(String(50), unique=True, index=True, nullable=False)
    jira_id = Column(String(50), nullable=False)
    summary = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    issue_type = Column(String(50), nullable=False)
    priority = Column(String(20), nullable=True)
    status = Column(String(50), nullable=True)
    assignee = Column(String(255), nullable=True)
    reporter = Column(String(255), nullable=True)
    labels = Column(JSON, nullable=True)
    custom_fields = Column(JSON, nullable=True)
    created_date = Column(DateTime(timezone=True), nullable=True)
    updated_date = Column(DateTime(timezone=True), nullable=True)
    resolved_date = Column(DateTime(timezone=True), nullable=True)
    url = Column(String(500), nullable=True)
    project_key = Column(String(20), nullable=False)
    created_by = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<JiraIssue(id={self.id}, jira_key='{self.jira_key}', summary='{self.summary}')>" 