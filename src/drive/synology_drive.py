# Synology Drive module for DSM 7.0+

import requests
import json
from typing import Dict, List, Any, Optional
import sys


class SynologyDrive:
    """Handles Synology Drive API operations."""

    def __init__(self, base_url: str, session_id: str, verify_ssl: bool = False):
        self.base_url = base_url.rstrip('/')
        self.session_id = session_id
        self.api_url = f"{self.base_url}/webapi/entry.cgi"
        self.verify_ssl = verify_ssl

        # API definitions
        self.sync_api = "SYNO.SynologyDrive.Sync"
        self.share_api = "SYNO.SynologyDrive.Share"
        self.team_api = "SYNO.SynologyDrive.TeamFolder"
        self.files_api = "SYNO.SynologyDrive.Files"
        self.connection_api = "SYNO.SynologyDrive.Connection"

    def _make_request(self, api: str, version: str, method: str, use_post: bool = False, **params) -> Dict[str, Any]:
        """Make a request to Synology Drive API."""
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
                raise Exception(f"Synology Drive API error {error_code}")

            return data.get('data', {})

        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {e}")

    # ==================== Connection/Status Operations ====================

    def list_connections(self) -> Dict[str, Any]:
        """List all connected Drive clients."""
        try:
            data = self._make_request(self.connection_api, "1", "List")
            connections = []
            for conn in data.get('connections', []):
                connections.append({
                    'id': conn.get('id'),
                    'user': conn.get('user'),
                    'device_name': conn.get('device_name'),
                    'device_type': conn.get('device_type'),
                    'ip': conn.get('ip'),
                    'last_sync': conn.get('last_sync_time'),
                    'status': conn.get('status'),
                    'version': conn.get('client_version')
                })
            return {'total': len(connections), 'connections': connections}
        except Exception as e:
            raise Exception(f"Failed to list connections: {e}")

    def disconnect_client(self, connection_id: str) -> Dict[str, Any]:
        """Disconnect a Drive client."""
        print(f"🔌 Disconnecting client {connection_id}", file=sys.stderr)
        self._make_request(self.connection_api, "1", "Disconnect", use_post=True, id=connection_id)
        return {'success': True, 'connection_id': connection_id, 'action': 'disconnected'}

    # ==================== Team Folder Operations ====================

    def list_team_folders(self) -> Dict[str, Any]:
        """List all team folders."""
        try:
            data = self._make_request(self.team_api, "1", "List")
            folders = []
            for folder in data.get('team_folders', []):
                folders.append({
                    'id': folder.get('id'),
                    'name': folder.get('name'),
                    'path': folder.get('path'),
                    'owner': folder.get('owner'),
                    'enabled': folder.get('enable'),
                    'member_count': folder.get('member_count'),
                    'size': folder.get('size')
                })
            return {'total': len(folders), 'team_folders': folders}
        except Exception as e:
            raise Exception(f"Failed to list team folders: {e}")

    def get_team_folder(self, folder_id: str) -> Dict[str, Any]:
        """Get team folder details."""
        data = self._make_request(self.team_api, "1", "Get", id=folder_id)
        return data

    def enable_team_folder(self, folder_id: str) -> Dict[str, Any]:
        """Enable a team folder."""
        print(f"✅ Enabling team folder {folder_id}", file=sys.stderr)
        self._make_request(self.team_api, "1", "Enable", use_post=True, id=folder_id)
        return {'success': True, 'folder_id': folder_id, 'action': 'enabled'}

    def disable_team_folder(self, folder_id: str) -> Dict[str, Any]:
        """Disable a team folder."""
        print(f"❌ Disabling team folder {folder_id}", file=sys.stderr)
        self._make_request(self.team_api, "1", "Disable", use_post=True, id=folder_id)
        return {'success': True, 'folder_id': folder_id, 'action': 'disabled'}

    # ==================== Share Link Operations ====================

    def list_share_links(self, limit: int = 50) -> Dict[str, Any]:
        """List all share links."""
        try:
            data = self._make_request(self.share_api, "1", "List", limit=limit)
            links = []
            for link in data.get('links', []):
                links.append({
                    'id': link.get('id'),
                    'path': link.get('path'),
                    'url': link.get('url'),
                    'owner': link.get('owner'),
                    'expire_time': link.get('expire_time'),
                    'password_protected': link.get('has_password'),
                    'access_count': link.get('access_count'),
                    'created': link.get('create_time')
                })
            return {'total': data.get('total', len(links)), 'links': links}
        except Exception as e:
            raise Exception(f"Failed to list share links: {e}")

    def create_share_link(self, path: str, password: Optional[str] = None, expire_days: Optional[int] = None) -> Dict[str, Any]:
        """Create a share link for a file or folder."""
        print(f"🔗 Creating share link for {path}", file=sys.stderr)
        params = {'path': path}
        if password:
            params['password'] = password
        if expire_days:
            params['expire_days'] = expire_days

        data = self._make_request(self.share_api, "1", "Create", use_post=True, **params)
        return {'success': True, 'path': path, 'url': data.get('url', ''), 'id': data.get('id', '')}

    def delete_share_link(self, link_id: str) -> Dict[str, Any]:
        """Delete a share link."""
        print(f"🗑️ Deleting share link {link_id}", file=sys.stderr)
        self._make_request(self.share_api, "1", "Delete", use_post=True, id=link_id)
        return {'success': True, 'link_id': link_id, 'action': 'deleted'}

    # ==================== Sync Status ====================

    def get_sync_status(self) -> Dict[str, Any]:
        """Get overall sync status."""
        try:
            data = self._make_request(self.sync_api, "1", "Status")
            return {
                'syncing': data.get('syncing', False),
                'pending_files': data.get('pending_count', 0),
                'error_files': data.get('error_count', 0),
                'last_sync': data.get('last_sync_time')
            }
        except Exception as e:
            return {'syncing': False, 'error': str(e)}

    # ==================== File Version Operations ====================

    def list_file_versions(self, path: str) -> Dict[str, Any]:
        """List version history for a file."""
        data = self._make_request(self.files_api, "1", "ListVersions", path=path)
        versions = []
        for ver in data.get('versions', []):
            versions.append({
                'version': ver.get('version'),
                'time': ver.get('time'),
                'size': ver.get('size'),
                'modified_by': ver.get('user')
            })
        return {'path': path, 'total': len(versions), 'versions': versions}

    def restore_file_version(self, path: str, version: int) -> Dict[str, Any]:
        """Restore a file to a previous version."""
        print(f"🔄 Restoring {path} to version {version}", file=sys.stderr)
        self._make_request(self.files_api, "1", "RestoreVersion", use_post=True, path=path, version=version)
        return {'success': True, 'path': path, 'version': version, 'action': 'restored'}
