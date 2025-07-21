"""
Jira Service
Jira entegrasyonu ve issue yönetimi
"""

import logging
from typing import List, Dict, Any, Optional
from jira import JIRA
from app.core.config import settings

logger = logging.getLogger(__name__)


class JiraService:
    def __init__(self):
        self.server_url = settings.JIRA_SERVER_URL
        self.username = settings.JIRA_USERNAME
        self.api_token = settings.JIRA_API_TOKEN
        self.project_key = settings.JIRA_PROJECT_KEY
        
        if all([self.server_url, self.username, self.api_token]):
            self.client = JIRA(
                server=self.server_url,
                basic_auth=(self.username, self.api_token)
            )
        else:
            self.client = None
            logger.warning("Jira credentials eksik - Jira entegrasyonu devre dışı")
    
    async def create_issue(
        self,
        summary: str,
        description: Optional[str] = None,
        issue_type: str = "Bug",
        priority: str = "Medium",
        assignee: Optional[str] = None,
        labels: Optional[List[str]] = None,
        custom_fields: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Jira'da yeni issue oluştur"""
        try:
            if not self.client:
                raise Exception("Jira client başlatılamadı")
            
            issue_dict = {
                'project': {'key': self.project_key},
                'summary': summary,
                'description': description or "",
                'issuetype': {'name': issue_type},
                'priority': {'name': priority}
            }
            
            if assignee:
                issue_dict['assignee'] = {'name': assignee}
            
            if labels:
                issue_dict['labels'] = labels
            
            if custom_fields:
                issue_dict.update(custom_fields)
            
            issue = self.client.create_issue(fields=issue_dict)
            
            logger.info(f"Jira issue oluşturuldu: {issue.key}")
            
            return {
                "key": issue.key,
                "id": issue.id,
                "fields": {
                    "summary": issue.fields.summary,
                    "description": issue.fields.description,
                    "status": {"name": issue.fields.status.name},
                    "assignee": {"displayName": issue.fields.assignee.displayName} if issue.fields.assignee else None,
                    "created": issue.fields.created
                }
            }
            
        except Exception as e:
            logger.error(f"Jira issue oluşturma hatası: {e}")
            raise
    
    async def get_issue(self, issue_key: str) -> Optional[Dict[str, Any]]:
        """Jira issue detaylarını al"""
        try:
            if not self.client:
                raise Exception("Jira client başlatılamadı")
            
            issue = self.client.issue(issue_key)
            
            return {
                "key": issue.key,
                "id": issue.id,
                "fields": {
                    "summary": issue.fields.summary,
                    "description": issue.fields.description,
                    "status": {"name": issue.fields.status.name},
                    "priority": {"name": issue.fields.priority.name},
                    "assignee": {"displayName": issue.fields.assignee.displayName} if issue.fields.assignee else None,
                    "reporter": {"displayName": issue.fields.reporter.displayName},
                    "created": issue.fields.created,
                    "updated": issue.fields.updated
                }
            }
            
        except Exception as e:
            logger.error(f"Jira issue alma hatası: {e}")
            return None
    
    async def update_issue(
        self,
        issue_key: str,
        fields: Dict[str, Any],
        transition: Optional[str] = None
    ) -> bool:
        """Jira issue güncelle"""
        try:
            if not self.client:
                raise Exception("Jira client başlatılamadı")
            
            issue = self.client.issue(issue_key)
            
            # Alanları güncelle
            if fields:
                issue.update(fields=fields)
            
            # Durum geçişi
            if transition:
                transitions = self.client.transitions(issue)
                for t in transitions:
                    if t['name'] == transition:
                        self.client.transition_issue(issue, t['id'])
                        break
            
            logger.info(f"Jira issue güncellendi: {issue_key}")
            return True
            
        except Exception as e:
            logger.error(f"Jira issue güncelleme hatası: {e}")
            return False
    
    async def get_projects(self) -> List[Dict[str, Any]]:
        """Jira projelerini listele"""
        try:
            if not self.client:
                raise Exception("Jira client başlatılamadı")
            
            projects = self.client.projects()
            
            return [
                {
                    "key": project.key,
                    "name": project.name,
                    "projectTypeKey": project.projectTypeKey,
                    "simplified": project.simplified,
                    "style": project.style,
                    "isPrivate": project.isPrivate
                }
                for project in projects
            ]
            
        except Exception as e:
            logger.error(f"Jira projeleri alma hatası: {e}")
            return []
    
    async def get_issue_types(self, project_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """Jira issue tiplerini listele"""
        try:
            if not self.client:
                raise Exception("Jira client başlatılamadı")
            
            if project_key:
                project = self.client.project(project_key)
                issue_types = project.issueTypes
            else:
                issue_types = self.client.issue_types()
            
            return [
                {
                    "id": issue_type.id,
                    "name": issue_type.name,
                    "description": getattr(issue_type, 'description', None),
                    "iconUrl": getattr(issue_type, 'iconUrl', None),
                    "subtask": issue_type.subtask
                }
                for issue_type in issue_types
            ]
            
        except Exception as e:
            logger.error(f"Jira issue tipleri alma hatası: {e}")
            return []
    
    async def search_issues(
        self,
        jql: str,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """JQL ile issue ara"""
        try:
            if not self.client:
                raise Exception("Jira client başlatılamadı")
            
            issues = self.client.search_issues(jql, maxResults=max_results)
            
            return [
                {
                    "key": issue.key,
                    "id": issue.id,
                    "summary": issue.fields.summary,
                    "status": issue.fields.status.name,
                    "assignee": issue.fields.assignee.displayName if issue.fields.assignee else None,
                    "created": issue.fields.created
                }
                for issue in issues
            ]
            
        except Exception as e:
            logger.error(f"Jira issue arama hatası: {e}")
            return []
    
    async def add_comment(self, issue_key: str, comment: str) -> bool:
        """Issue'a yorum ekle"""
        try:
            if not self.client:
                raise Exception("Jira client başlatılamadı")
            
            self.client.add_comment(issue_key, comment)
            
            logger.info(f"Jira yorumu eklendi: {issue_key}")
            return True
            
        except Exception as e:
            logger.error(f"Jira yorum ekleme hatası: {e}")
            return False
    
    async def add_attachment(self, issue_key: str, file_path: str) -> bool:
        """Issue'a dosya ekle"""
        try:
            if not self.client:
                raise Exception("Jira client başlatılamadı")
            
            self.client.add_attachment(issue_key, file_path)
            
            logger.info(f"Jira dosyası eklendi: {issue_key}")
            return True
            
        except Exception as e:
            logger.error(f"Jira dosya ekleme hatası: {e}")
            return False
    
    async def check_connection(self) -> bool:
        """Jira bağlantısını kontrol et"""
        try:
            if not self.client:
                return False
            
            # Basit bir test - projeleri listele
            self.client.projects()
            return True
            
        except Exception as e:
            logger.error(f"Jira bağlantı kontrol hatası: {e}")
            return False
    
    async def get_issue_transitions(self, issue_key: str) -> List[Dict[str, Any]]:
        """Issue için mevcut geçişleri al"""
        try:
            if not self.client:
                raise Exception("Jira client başlatılamadı")
            
            transitions = self.client.transitions(issue_key)
            
            return [
                {
                    "id": t['id'],
                    "name": t['name'],
                    "to": t['to']
                }
                for t in transitions
            ]
            
        except Exception as e:
            logger.error(f"Jira geçiş alma hatası: {e}")
            return []
    
    async def create_test_issue_from_result(
        self,
        test_result: Dict[str, Any],
        issue_type: str = "Bug"
    ) -> Optional[Dict[str, Any]]:
        """Test sonucundan Jira issue oluştur"""
        try:
            if test_result.get("status") != "failed":
                return None
            
            summary = f"Test Hatası: {test_result.get('test_title', 'Bilinmeyen Test')}"
            
            description = f"""
            Test Sonucu Hatası:
            
            Test: {test_result.get('test_title', 'Bilinmeyen')}
            Durum: {test_result.get('status')}
            Hata Mesajı: {test_result.get('error_message', 'Hata mesajı yok')}
            Çalıştırma Süresi: {test_result.get('execution_time', 'Bilinmiyor')} saniye
            Ortam: {test_result.get('environment', 'Bilinmiyor')}
            
            Stack Trace:
            {test_result.get('stack_trace', 'Stack trace yok')}
            """
            
            return await self.create_issue(
                summary=summary,
                description=description,
                issue_type=issue_type,
                priority="High" if test_result.get("priority") == "critical" else "Medium",
                labels=["test-failure", "automated"]
            )
            
        except Exception as e:
            logger.error(f"Test sonucundan issue oluşturma hatası: {e}")
            return None 