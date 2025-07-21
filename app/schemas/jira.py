"""
Jira Integration Pydantic Schemas
Jira issue'ları ve webhook verileri için doğrulama
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class JiraIssueBase(BaseModel):
    summary: str
    description: Optional[str] = None
    issue_type: str
    priority: Optional[str] = "Medium"
    assignee: Optional[str] = None
    labels: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class JiraIssueCreate(JiraIssueBase):
    project_key: str


class JiraIssueUpdate(BaseModel):
    summary: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    assignee: Optional[str] = None
    labels: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class JiraIssueResponse(BaseModel):
    issue_key: str
    issue_id: str
    status: Optional[str] = None
    assignee: Optional[str] = None
    created_date: Optional[str] = None
    url: Optional[str] = None


class JiraWebhookData(BaseModel):
    webhookEvent: str
    issue: Dict[str, Any]
    user: Optional[Dict[str, Any]] = None
    timestamp: Optional[int] = None


class JiraProject(BaseModel):
    key: str
    name: str
    projectTypeKey: str
    simplified: bool
    style: str
    isPrivate: bool


class JiraIssueType(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    iconUrl: Optional[str] = None
    subtask: bool


class JiraTransition(BaseModel):
    id: str
    name: str
    to: Dict[str, Any]
    fields: Optional[Dict[str, Any]] = None


class JiraComment(BaseModel):
    id: str
    body: str
    author: Dict[str, Any]
    created: str
    updated: Optional[str] = None


class JiraAttachment(BaseModel):
    id: str
    filename: str
    size: int
    mimeType: str
    content: Optional[str] = None
    created: str 