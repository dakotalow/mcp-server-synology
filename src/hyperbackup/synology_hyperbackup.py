# Hyper Backup module for DSM 7.0+

import requests
import json
from typing import Dict, List, Any, Optional
import sys


class SynologyHyperBackup:
    """Handles Synology Hyper Backup API operations."""

    def __init__(self, base_url: str, session_id: str, verify_ssl: bool = False):
        self.base_url = base_url.rstrip('/')
        self.session_id = session_id
        self.api_url = f"{self.base_url}/webapi/entry.cgi"
        self.verify_ssl = verify_ssl

        # API definitions
        self.task_api = "SYNO.Backup.Task"
        self.repository_api = "SYNO.Backup.Repository"
        self.config_api = "SYNO.Backup.Config"

    def _make_request(self, api: str, version: str, method: str, use_post: bool = False, **params) -> Dict[str, Any]:
        """Make a request to Hyper Backup API."""
        request_params = {
            'api': api,
            'version': version,
            'method': method,
            '_sid': self.session_id,
            **params
        }

        try:
            if use_post:
                response = requests.post(self.api_url, data=request_params, verify=self.verify_ssl)
            else:
                response = requests.get(self.api_url, params=request_params, verify=self.verify_ssl)

            response.raise_for_status()
            data = response.json()

            if not data.get('success'):
                error_code = data.get('error', {}).get('code', 'unknown')
                raise Exception(f"Hyper Backup API error {error_code}")

            return data.get('data', {})

        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {e}")

    # ==================== Task Operations ====================

    def list_tasks(self) -> Dict[str, Any]:
        """List all backup tasks."""
        try:
            data = self._make_request(self.task_api, "1", "List")
            tasks = []
            for task in data.get('task_list', []):
                tasks.append({
                    'id': task.get('task_id'),
                    'name': task.get('name'),
                    'status': task.get('status'),
                    'state': task.get('state'),
                    'type': task.get('type'),
                    'target': task.get('target'),
                    'schedule_enabled': task.get('schedule_enable'),
                    'last_backup_time': task.get('last_bkp_time'),
                    'last_backup_result': task.get('last_bkp_result'),
                    'next_backup_time': task.get('next_bkp_time'),
                    'progress': task.get('progress'),
                    'transferred_bytes': task.get('transferred_bytes'),
                    'total_bytes': task.get('total_bytes')
                })
            return {'total': len(tasks), 'tasks': tasks}
        except Exception as e:
            raise Exception(f"Failed to list backup tasks: {e}")

    def get_task_info(self, task_id: int) -> Dict[str, Any]:
        """Get detailed info for a specific backup task."""
        data = self._make_request(self.task_api, "1", "Get", task_id=task_id)
        return data

    def start_backup(self, task_id: int) -> Dict[str, Any]:
        """Start a backup task."""
        print(f"💾 Starting backup task {task_id}", file=sys.stderr)
        self._make_request(self.task_api, "1", "Backup", use_post=True, task_id=task_id)
        return {'success': True, 'task_id': task_id, 'action': 'started'}

    def cancel_backup(self, task_id: int) -> Dict[str, Any]:
        """Cancel a running backup task."""
        print(f"⏹️ Canceling backup task {task_id}", file=sys.stderr)
        self._make_request(self.task_api, "1", "Cancel", use_post=True, task_id=task_id)
        return {'success': True, 'task_id': task_id, 'action': 'cancelled'}

    def suspend_backup(self, task_id: int) -> Dict[str, Any]:
        """Suspend a running backup task."""
        print(f"⏸️ Suspending backup task {task_id}", file=sys.stderr)
        self._make_request(self.task_api, "1", "Suspend", use_post=True, task_id=task_id)
        return {'success': True, 'task_id': task_id, 'action': 'suspended'}

    def resume_backup(self, task_id: int) -> Dict[str, Any]:
        """Resume a suspended backup task."""
        print(f"▶️ Resuming backup task {task_id}", file=sys.stderr)
        self._make_request(self.task_api, "1", "Resume", use_post=True, task_id=task_id)
        return {'success': True, 'task_id': task_id, 'action': 'resumed'}

    # ==================== Repository/Version Operations ====================

    def list_versions(self, task_id: int) -> Dict[str, Any]:
        """List backup versions for a task."""
        data = self._make_request(self.repository_api, "1", "List", task_id=task_id)
        versions = []
        for ver in data.get('version_list', []):
            versions.append({
                'version_id': ver.get('version_id'),
                'time': ver.get('time'),
                'size': ver.get('size'),
                'status': ver.get('status'),
                'is_locked': ver.get('is_locked')
            })
        return {'total': len(versions), 'versions': versions}

    def delete_version(self, task_id: int, version_id: int) -> Dict[str, Any]:
        """Delete a backup version."""
        print(f"🗑️ Deleting backup version {version_id} from task {task_id}", file=sys.stderr)
        self._make_request(self.repository_api, "1", "Delete", use_post=True, task_id=task_id, version_id=version_id)
        return {'success': True, 'task_id': task_id, 'version_id': version_id, 'action': 'deleted'}

    # ==================== Integrity Check ====================

    def check_integrity(self, task_id: int) -> Dict[str, Any]:
        """Start integrity check for a backup task."""
        print(f"🔍 Starting integrity check for task {task_id}", file=sys.stderr)
        self._make_request(self.task_api, "1", "IntegrityCheck", use_post=True, task_id=task_id)
        return {'success': True, 'task_id': task_id, 'action': 'integrity_check_started'}

    def get_backup_stats(self) -> Dict[str, Any]:
        """Get overall backup statistics."""
        try:
            tasks = self.list_tasks()
            total_tasks = tasks['total']
            running = sum(1 for t in tasks['tasks'] if t['status'] == 'running')
            success = sum(1 for t in tasks['tasks'] if t['last_backup_result'] == 'success')
            failed = sum(1 for t in tasks['tasks'] if t['last_backup_result'] == 'error')

            return {
                'total_tasks': total_tasks,
                'running': running,
                'last_success_count': success,
                'last_failed_count': failed,
                'tasks': tasks['tasks']
            }
        except Exception as e:
            raise Exception(f"Failed to get backup stats: {e}")
