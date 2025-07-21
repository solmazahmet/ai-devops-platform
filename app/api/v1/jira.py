"""
Jira Entegrasyonu API Endpoints
Test sonuçlarının Jira'ya entegrasyonu
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.jira import JiraIssueCreate, JiraIssueResponse, JiraWebhookData
from app.services.jira_service import JiraService
from app.tasks.jira_tasks import create_jira_issue_async, update_jira_issue_async

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/create-issue", response_model=JiraIssueResponse)
async def create_jira_issue(
    issue_data: JiraIssueCreate,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Jira'da yeni issue oluştur"""
    try:
        jira_service = JiraService()
        
        # Jira issue oluştur
        issue = await jira_service.create_issue(
            summary=issue_data.summary,
            description=issue_data.description,
            issue_type=issue_data.issue_type,
            priority=issue_data.priority,
            assignee=issue_data.assignee,
            labels=issue_data.labels,
            custom_fields=issue_data.custom_fields
        )
        
        logger.info(f"Jira issue oluşturuldu: {issue.get('key')}")
        
        return JiraIssueResponse(
            issue_key=issue.get("key"),
            issue_id=issue.get("id"),
            status=issue.get("fields", {}).get("status", {}).get("name"),
            assignee=issue.get("fields", {}).get("assignee", {}).get("displayName"),
            created_date=issue.get("fields", {}).get("created"),
            url=f"{jira_service.server_url}/browse/{issue.get('key')}"
        )
        
    except Exception as e:
        logger.error(f"Jira issue oluşturma hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Jira issue oluşturulurken hata oluştu"
        )

@router.post("/create-issue-async")
async def create_jira_issue_background(
    issue_data: JiraIssueCreate,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Jira'da yeni issue oluştur (background task)"""
    try:
        # Background task olarak çalıştır
        background_tasks.add_task(
            create_jira_issue_async,
            user_email=current_user,
            issue_data=issue_data.dict()
        )
        
        logger.info(f"Jira issue oluşturma başlatıldı: {issue_data.summary}")
        
        return {
            "message": "Jira issue oluşturma başlatıldı",
            "task_status": "started",
            "summary": issue_data.summary
        }
        
    except Exception as e:
        logger.error(f"Jira issue oluşturma hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Jira issue oluşturulurken hata oluştu"
        )

@router.get("/issues/{issue_key}")
async def get_jira_issue(
    issue_key: str,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Jira issue detaylarını al"""
    try:
        jira_service = JiraService()
        
        issue = await jira_service.get_issue(issue_key)
        
        if not issue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Jira issue bulunamadı"
            )
        
        return {
            "issue_key": issue.get("key"),
            "summary": issue.get("fields", {}).get("summary"),
            "description": issue.get("fields", {}).get("description"),
            "status": issue.get("fields", {}).get("status", {}).get("name"),
            "priority": issue.get("fields", {}).get("priority", {}).get("name"),
            "assignee": issue.get("fields", {}).get("assignee", {}).get("displayName"),
            "reporter": issue.get("fields", {}).get("reporter", {}).get("displayName"),
            "created_date": issue.get("fields", {}).get("created"),
            "updated_date": issue.get("fields", {}).get("updated"),
            "url": f"{jira_service.server_url}/browse/{issue.get('key')}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Jira issue alma hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Jira issue alınırken hata oluştu"
        )

@router.put("/issues/{issue_key}")
async def update_jira_issue(
    issue_key: str,
    update_data: dict,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Jira issue güncelle"""
    try:
        jira_service = JiraService()
        
        updated_issue = await jira_service.update_issue(
            issue_key=issue_key,
            fields=update_data.get("fields", {}),
            transition=update_data.get("transition")
        )
        
        logger.info(f"Jira issue güncellendi: {issue_key}")
        
        return {
            "message": "Jira issue başarıyla güncellendi",
            "issue_key": issue_key,
            "updated_fields": list(update_data.get("fields", {}).keys())
        }
        
    except Exception as e:
        logger.error(f"Jira issue güncelleme hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Jira issue güncellenirken hata oluştu"
        )

@router.post("/webhook")
async def jira_webhook(
    webhook_data: JiraWebhookData,
    db: Session = Depends(get_db)
):
    """Jira webhook endpoint'i"""
    try:
        logger.info(f"Jira webhook alındı: {webhook_data.webhookEvent}")
        
        # Webhook verilerini işle
        if webhook_data.webhookEvent == "jira:issue_created":
            await process_issue_created(webhook_data, db)
        elif webhook_data.webhookEvent == "jira:issue_updated":
            await process_issue_updated(webhook_data, db)
        elif webhook_data.webhookEvent == "jira:issue_deleted":
            await process_issue_deleted(webhook_data, db)
        
        return {"message": "Webhook başarıyla işlendi"}
        
    except Exception as e:
        logger.error(f"Jira webhook işleme hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook işlenirken hata oluştu"
        )

@router.get("/projects")
async def get_jira_projects(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Jira projelerini listele"""
    try:
        jira_service = JiraService()
        
        projects = await jira_service.get_projects()
        
        return {
            "projects": projects,
            "total": len(projects)
        }
        
    except Exception as e:
        logger.error(f"Jira projeleri alma hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Jira projeleri alınırken hata oluştu"
        )

@router.get("/issue-types")
async def get_jira_issue_types(
    project_key: Optional[str] = None,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Jira issue tiplerini listele"""
    try:
        jira_service = JiraService()
        
        issue_types = await jira_service.get_issue_types(project_key)
        
        return {
            "issue_types": issue_types,
            "total": len(issue_types)
        }
        
    except Exception as e:
        logger.error(f"Jira issue tipleri alma hatası: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Jira issue tipleri alınırken hata oluştu"
        )

@router.get("/status")
async def get_jira_service_status(
    current_user: str = Depends(get_current_user)
):
    """Jira servis durumunu kontrol et"""
    try:
        jira_service = JiraService()
        status = await jira_service.check_connection()
        
        return {
            "status": "connected" if status else "disconnected",
            "server_url": jira_service.server_url,
            "username": jira_service.username,
            "available": status
        }
        
    except Exception as e:
        logger.error(f"Jira servis durumu kontrol hatası: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

# Webhook işleme fonksiyonları
async def process_issue_created(webhook_data: JiraWebhookData, db: Session):
    """Issue oluşturulduğunda işle"""
    logger.info(f"Yeni issue oluşturuldu: {webhook_data.issue.get('key')}")

async def process_issue_updated(webhook_data: JiraWebhookData, db: Session):
    """Issue güncellendiğinde işle"""
    logger.info(f"Issue güncellendi: {webhook_data.issue.get('key')}")

async def process_issue_deleted(webhook_data: JiraWebhookData, db: Session):
    """Issue silindiğinde işle"""
    logger.info(f"Issue silindi: {webhook_data.issue.get('key')}") 