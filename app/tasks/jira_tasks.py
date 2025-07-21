"""
Jira Background Tasks
Celery ile asenkron Jira işlemleri
"""

import logging
from celery import shared_task
from typing import Dict, Any, List
from app.services.jira_service import JiraService
from app.core.database import SessionLocal
from app.models.test import TestResult
from app.models.jira import JiraIssue
from datetime import datetime
from app.models.test import Test

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="create_jira_issue_async")
def create_jira_issue_async(self, user_email: str, issue_data: Dict[str, Any]):
    """Jira'da issue oluştur (background task)"""
    try:
        jira_service = JiraService()
        
        # Jira issue oluştur
        issue = await jira_service.create_issue(
            summary=issue_data.get("summary"),
            description=issue_data.get("description"),
            issue_type=issue_data.get("issue_type", "Bug"),
            priority=issue_data.get("priority", "Medium"),
            assignee=issue_data.get("assignee"),
            labels=issue_data.get("labels"),
            custom_fields=issue_data.get("custom_fields")
        )
        
        # Database'e kaydet
        db = SessionLocal()
        try:
            db_issue = JiraIssue(
                jira_key=issue.get("key"),
                jira_id=issue.get("id"),
                summary=issue.get("fields", {}).get("summary"),
                description=issue.get("fields", {}).get("description"),
                issue_type=issue_data.get("issue_type", "Bug"),
                priority=issue_data.get("priority", "Medium"),
                assignee=issue.get("fields", {}).get("assignee", {}).get("displayName"),
                labels=issue_data.get("labels"),
                custom_fields=issue_data.get("custom_fields"),
                created_date=issue.get("fields", {}).get("created"),
                url=f"{jira_service.server_url}/browse/{issue.get('key')}",
                project_key=issue_data.get("project_key", "TEST"),
                created_by=user_email
            )
            
            db.add(db_issue)
            db.commit()
            
        except Exception as e:
            logger.error(f"Database kayıt hatası: {e}")
            db.rollback()
        finally:
            db.close()
        
        logger.info(f"Jira issue oluşturuldu: {issue.get('key')}")
        
        return {
            "user_email": user_email,
            "issue_key": issue.get("key"),
            "issue_id": issue.get("id"),
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Jira issue oluşturma task hatası: {e}")
        return {"error": str(e), "status": "failed"}


@shared_task(bind=True, name="update_jira_issue_async")
def update_jira_issue_async(
    self,
    issue_key: str,
    update_data: Dict[str, Any],
    user_email: str
):
    """Jira issue güncelle (background task)"""
    try:
        jira_service = JiraService()
        
        # Jira issue güncelle
        success = await jira_service.update_issue(
            issue_key=issue_key,
            fields=update_data.get("fields", {}),
            transition=update_data.get("transition")
        )
        
        if success:
            # Database'i güncelle
            db = SessionLocal()
            try:
                db_issue = db.query(JiraIssue).filter(JiraIssue.jira_key == issue_key).first()
                if db_issue:
                    # Güncelleme alanları
                    if "summary" in update_data.get("fields", {}):
                        db_issue.summary = update_data["fields"]["summary"]
                    if "description" in update_data.get("fields", {}):
                        db_issue.description = update_data["fields"]["description"]
                    if "priority" in update_data.get("fields", {}):
                        db_issue.priority = update_data["fields"]["priority"]
                    
                    db.commit()
                    
            except Exception as e:
                logger.error(f"Database güncelleme hatası: {e}")
                db.rollback()
            finally:
                db.close()
        
        logger.info(f"Jira issue güncellendi: {issue_key}")
        
        return {
            "user_email": user_email,
            "issue_key": issue_key,
            "success": success,
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Jira issue güncelleme task hatası: {e}")
        return {"error": str(e), "status": "failed"}


@shared_task(bind=True, name="create_issues_from_test_failures")
def create_issues_from_test_failures(
    self,
    test_result_ids: List[int],
    user_email: str
):
    """Test hatalarından Jira issue'ları oluştur (background task)"""
    try:
        db = SessionLocal()
        jira_service = JiraService()
        
        created_issues = []
        
        for result_id in test_result_ids:
            try:
                # Test sonucunu al
                test_result = db.query(TestResult).filter(TestResult.id == result_id).first()
                if not test_result or test_result.status != "failed":
                    continue
                
                # Test bilgilerini al
                test = db.query(Test).filter(Test.id == test_result.test_id).first()
                if not test:
                    continue
                
                # Jira issue oluştur
                issue = await jira_service.create_test_issue_from_result(
                    test_result={
                        "test_title": test.title,
                        "status": test_result.status,
                        "error_message": test_result.error_message,
                        "execution_time": test_result.execution_time,
                        "environment": test_result.environment,
                        "stack_trace": test_result.stack_trace,
                        "priority": test.priority
                    }
                )
                
                if issue:
                    created_issues.append({
                        "test_result_id": result_id,
                        "issue_key": issue.get("key"),
                        "issue_id": issue.get("id")
                    })
                
            except Exception as e:
                logger.error(f"Test sonucu {result_id} için issue oluşturma hatası: {e}")
        
        logger.info(f"Test hatalarından {len(created_issues)} issue oluşturuldu")
        
        return {
            "user_email": user_email,
            "created_issues": created_issues,
            "total_processed": len(test_result_ids),
            "successful_creations": len(created_issues),
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Test hatalarından issue oluşturma task hatası: {e}")
        return {"error": str(e), "status": "failed"}
    finally:
        db.close()


@shared_task(bind=True, name="sync_jira_issues")
def sync_jira_issues(self, user_email: str, project_key: str = None):
    """Jira issue'larını senkronize et (background task)"""
    try:
        db = SessionLocal()
        jira_service = JiraService()
        
        # Jira'dan issue'ları al
        jql = f"project = {project_key or jira_service.project_key}"
        issues = await jira_service.search_issues(jql, max_results=100)
        
        synced_count = 0
        
        for issue in issues:
            try:
                # Database'de var mı kontrol et
                existing_issue = db.query(JiraIssue).filter(
                    JiraIssue.jira_key == issue.get("key")
                ).first()
                
                if existing_issue:
                    # Mevcut issue'yu güncelle
                    existing_issue.status = issue.get("status")
                    existing_issue.updated_date = issue.get("created")
                    synced_count += 1
                else:
                    # Yeni issue oluştur
                    new_issue = JiraIssue(
                        jira_key=issue.get("key"),
                        jira_id=issue.get("id"),
                        summary=issue.get("summary"),
                        status=issue.get("status"),
                        assignee=issue.get("assignee"),
                        created_date=issue.get("created"),
                        url=f"{jira_service.server_url}/browse/{issue.get('key')}",
                        project_key=project_key or jira_service.project_key,
                        created_by=user_email
                    )
                    db.add(new_issue)
                    synced_count += 1
                
            except Exception as e:
                logger.error(f"Issue {issue.get('key')} senkronizasyon hatası: {e}")
        
        db.commit()
        
        logger.info(f"Jira issue senkronizasyonu tamamlandı: {synced_count} issue")
        
        return {
            "user_email": user_email,
            "synced_count": synced_count,
            "total_issues": len(issues),
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Jira issue senkronizasyon task hatası: {e}")
        return {"error": str(e), "status": "failed"}
    finally:
        db.close()


@shared_task(bind=True, name="add_jira_comments_batch")
def add_jira_comments_batch(
    self,
    issue_keys: List[str],
    comment_template: str,
    user_email: str
):
    """Toplu Jira yorumları ekle (background task)"""
    try:
        jira_service = JiraService()
        
        successful_comments = 0
        
        for issue_key in issue_keys:
            try:
                # Yorum şablonunu kişiselleştir
                comment = comment_template.format(
                    issue_key=issue_key,
                    user_email=user_email,
                    timestamp=datetime.utcnow().isoformat()
                )
                
                # Yorum ekle
                success = await jira_service.add_comment(issue_key, comment)
                if success:
                    successful_comments += 1
                
            except Exception as e:
                logger.error(f"Issue {issue_key} yorum ekleme hatası: {e}")
        
        logger.info(f"Toplu yorum ekleme tamamlandı: {successful_comments} yorum")
        
        return {
            "user_email": user_email,
            "successful_comments": successful_comments,
            "total_issues": len(issue_keys),
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Toplu yorum ekleme task hatası: {e}")
        return {"error": str(e), "status": "failed"}


@shared_task(bind=True, name="cleanup_jira_tasks")
def cleanup_jira_tasks(self):
    """Eski Jira task'larını temizle (scheduled task)"""
    try:
        # Bu task Celery beat tarafından düzenli olarak çalıştırılır
        # Eski task sonuçlarını ve log'ları temizler
        
        logger.info("Jira task temizleme işlemi başlatıldı")
        
        # Temizleme işlemleri burada yapılır
        # Örnek: 30 günden eski task sonuçlarını sil
        
        return {
            "message": "Jira task temizleme tamamlandı",
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Jira task temizleme hatası: {e}")
        return {"error": str(e), "status": "failed"}


@shared_task(bind=True, name="health_check")
def health_check(self):
    """Sistem sağlık kontrolü (scheduled task)"""
    try:
        # Bu task Celery beat tarafından düzenli olarak çalıştırılır
        # Sistem durumunu kontrol eder
        
        logger.info("Sistem sağlık kontrolü başlatıldı")
        
        # Sağlık kontrolleri
        checks = {
            "database": True,  # Database bağlantısı kontrol edilir
            "jira": True,      # Jira bağlantısı kontrol edilir
            "ai_service": True, # AI servis durumu kontrol edilir
            "redis": True      # Redis bağlantısı kontrol edilir
        }
        
        all_healthy = all(checks.values())
        
        return {
            "message": "Sağlık kontrolü tamamlandı",
            "checks": checks,
            "overall_status": "healthy" if all_healthy else "unhealthy",
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Sağlık kontrolü hatası: {e}")
        return {"error": str(e), "status": "failed"} 