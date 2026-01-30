# System Management module for DSM 7.0+
# Includes: Resource Monitor, Storage Manager, Log Center, Package Center, Users & Groups

import requests
import json
from typing import Dict, List, Any, Optional
import sys


class SynologySystem:
    """Handles Synology System Management API operations."""

    def __init__(self, base_url: str, session_id: str, verify_ssl: bool = False):
        self.base_url = base_url.rstrip('/')
        self.session_id = session_id
        self.api_url = f"{self.base_url}/webapi/entry.cgi"
        self.verify_ssl = verify_ssl

        # API definitions
        # Resource Monitor
        self.system_info_api = "SYNO.Core.System"
        self.utilization_api = "SYNO.Core.System.Utilization"

        # Storage Manager
        self.storage_api = "SYNO.Storage.CGI.Storage"
        self.volume_api = "SYNO.Core.Storage.Volume"
        self.disk_api = "SYNO.Storage.CGI.Disk"

        # Log Center
        self.log_api = "SYNO.Core.SyslogClient.Log"
        self.event_api = "SYNO.Core.SyslogClient.Event"

        # Package Center
        self.package_api = "SYNO.Core.Package"

        # Users & Groups
        self.user_api = "SYNO.Core.User"
        self.group_api = "SYNO.Core.Group"

    def _make_request(self, api: str, version: str, method: str, use_post: bool = False, **params) -> Dict[str, Any]:
        """Make a request to System API."""
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
                raise Exception(f"System API error {error_code}")

            return data.get('data', {})

        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {e}")

    # ==================== Resource Monitor ====================

    def get_system_info(self) -> Dict[str, Any]:
        """Get general system information."""
        data = self._make_request(self.system_info_api, "1", "info")
        return {
            'model': data.get('model'),
            'serial': data.get('serial'),
            'firmware': data.get('firmware_ver'),
            'firmware_date': data.get('firmware_date'),
            'uptime': data.get('up_time'),
            'temperature': data.get('sys_temp'),
            'cpu_clock_speed': data.get('cpu_clock_speed'),
            'cpu_cores': data.get('cpu_cores'),
            'ram_size': data.get('ram_size')
        }

    def get_utilization(self) -> Dict[str, Any]:
        """Get current system utilization (CPU, RAM, Network, Disk)."""
        data = self._make_request(self.utilization_api, "1", "get")
        return {
            'cpu': {
                'user': data.get('cpu', {}).get('user_load', 0),
                'system': data.get('cpu', {}).get('system_load', 0),
                'total': data.get('cpu', {}).get('user_load', 0) + data.get('cpu', {}).get('system_load', 0)
            },
            'memory': {
                'total': data.get('memory', {}).get('memory_size', 0),
                'used': data.get('memory', {}).get('real_usage', 0),
                'available': data.get('memory', {}).get('avail_real', 0),
                'cached': data.get('memory', {}).get('cached', 0),
                'swap_used': data.get('memory', {}).get('si_disk', 0)
            },
            'network': data.get('network', []),
            'disk': data.get('disk', [])
        }

    # ==================== Storage Manager ====================

    def list_volumes(self) -> Dict[str, Any]:
        """List all storage volumes."""
        try:
            data = self._make_request(self.volume_api, "1", "list")
            volumes = []
            for vol in data.get('volumes', []):
                volumes.append({
                    'id': vol.get('id'),
                    'name': vol.get('display_name'),
                    'status': vol.get('status'),
                    'total_size': vol.get('size', {}).get('total'),
                    'used_size': vol.get('size', {}).get('used'),
                    'free_size': vol.get('size', {}).get('free'),
                    'usage_percent': vol.get('size', {}).get('used_percent'),
                    'fs_type': vol.get('fs_type'),
                    'pool_path': vol.get('pool_path')
                })
            return {'total': len(volumes), 'volumes': volumes}
        except Exception as e:
            raise Exception(f"Failed to list volumes: {e}")

    def list_disks(self) -> Dict[str, Any]:
        """List all physical disks."""
        try:
            data = self._make_request(self.disk_api, "1", "list")
            disks = []
            for disk in data.get('disks', []):
                disks.append({
                    'id': disk.get('id'),
                    'name': disk.get('name'),
                    'device': disk.get('device'),
                    'model': disk.get('model'),
                    'vendor': disk.get('vendor'),
                    'serial': disk.get('serial'),
                    'size': disk.get('size_total'),
                    'status': disk.get('status'),
                    'temperature': disk.get('temp'),
                    'smart_status': disk.get('smart_status'),
                    'type': disk.get('diskType'),
                    'firmware': disk.get('firm')
                })
            return {'total': len(disks), 'disks': disks}
        except Exception as e:
            raise Exception(f"Failed to list disks: {e}")

    def get_storage_overview(self) -> Dict[str, Any]:
        """Get storage overview including volumes and pools."""
        try:
            data = self._make_request(self.storage_api, "1", "load_info")
            return data
        except Exception as e:
            raise Exception(f"Failed to get storage overview: {e}")

    # ==================== Log Center ====================

    def get_logs(self, log_type: str = "general", limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """Get system logs."""
        try:
            data = self._make_request(
                self.log_api, "1", "list",
                log_type=log_type,
                limit=limit,
                offset=offset
            )
            logs = []
            for log in data.get('items', []):
                logs.append({
                    'time': log.get('time'),
                    'user': log.get('user'),
                    'event': log.get('event'),
                    'ip': log.get('ip'),
                    'log_type': log.get('logtype'),
                    'descr': log.get('descr')
                })
            return {'total': data.get('total', len(logs)), 'logs': logs}
        except Exception as e:
            raise Exception(f"Failed to get logs: {e}")

    def get_events(self, limit: int = 100) -> Dict[str, Any]:
        """Get system events (notifications)."""
        try:
            data = self._make_request(self.event_api, "1", "list", limit=limit)
            return data
        except Exception as e:
            raise Exception(f"Failed to get events: {e}")

    def clear_logs(self, log_type: str = "general") -> Dict[str, Any]:
        """Clear system logs."""
        print(f"🗑️ Clearing {log_type} logs", file=sys.stderr)
        self._make_request(self.log_api, "1", "clear", use_post=True, log_type=log_type)
        return {'success': True, 'log_type': log_type, 'action': 'cleared'}

    # ==================== Package Center ====================

    def list_packages(self, installed_only: bool = True) -> Dict[str, Any]:
        """List packages."""
        try:
            params = {}
            if installed_only:
                params['additional'] = 'installed'

            data = self._make_request(self.package_api, "1", "list", **params)
            packages = []
            for pkg in data.get('packages', []):
                packages.append({
                    'id': pkg.get('id'),
                    'name': pkg.get('dname'),
                    'version': pkg.get('version'),
                    'status': pkg.get('status'),
                    'is_running': pkg.get('is_running'),
                    'auto_update': pkg.get('auto_update'),
                    'description': pkg.get('desc')
                })
            return {'total': len(packages), 'packages': packages}
        except Exception as e:
            raise Exception(f"Failed to list packages: {e}")

    def start_package(self, package_id: str) -> Dict[str, Any]:
        """Start a package/service."""
        print(f"▶️ Starting package {package_id}", file=sys.stderr)
        self._make_request(self.package_api, "1", "start", use_post=True, id=package_id)
        return {'success': True, 'package_id': package_id, 'action': 'started'}

    def stop_package(self, package_id: str) -> Dict[str, Any]:
        """Stop a package/service."""
        print(f"⏹️ Stopping package {package_id}", file=sys.stderr)
        self._make_request(self.package_api, "1", "stop", use_post=True, id=package_id)
        return {'success': True, 'package_id': package_id, 'action': 'stopped'}

    def install_package(self, package_id: str) -> Dict[str, Any]:
        """Install a package from Package Center."""
        print(f"📦 Installing package {package_id}", file=sys.stderr)
        self._make_request(self.package_api, "1", "install", use_post=True, id=package_id)
        return {'success': True, 'package_id': package_id, 'action': 'installing'}

    def uninstall_package(self, package_id: str) -> Dict[str, Any]:
        """Uninstall a package."""
        print(f"🗑️ Uninstalling package {package_id}", file=sys.stderr)
        self._make_request(self.package_api, "1", "uninstall", use_post=True, id=package_id)
        return {'success': True, 'package_id': package_id, 'action': 'uninstalled'}

    def update_package(self, package_id: str) -> Dict[str, Any]:
        """Update a package to latest version."""
        print(f"🔄 Updating package {package_id}", file=sys.stderr)
        self._make_request(self.package_api, "1", "upgrade", use_post=True, id=package_id)
        return {'success': True, 'package_id': package_id, 'action': 'updating'}

    # ==================== Users & Groups ====================

    def list_users(self) -> Dict[str, Any]:
        """List all users."""
        try:
            data = self._make_request(self.user_api, "1", "list")
            users = []
            for user in data.get('users', []):
                users.append({
                    'name': user.get('name'),
                    'uid': user.get('uid'),
                    'description': user.get('description'),
                    'email': user.get('email'),
                    'expired': user.get('expired'),
                    'groups': user.get('groups', [])
                })
            return {'total': data.get('total', len(users)), 'users': users}
        except Exception as e:
            raise Exception(f"Failed to list users: {e}")

    def get_user(self, username: str) -> Dict[str, Any]:
        """Get details for a specific user."""
        data = self._make_request(self.user_api, "1", "get", name=username)
        return data

    def list_groups(self) -> Dict[str, Any]:
        """List all groups."""
        try:
            data = self._make_request(self.group_api, "1", "list")
            groups = []
            for group in data.get('groups', []):
                groups.append({
                    'name': group.get('name'),
                    'gid': group.get('gid'),
                    'description': group.get('description'),
                    'members': group.get('members', [])
                })
            return {'total': data.get('total', len(groups)), 'groups': groups}
        except Exception as e:
            raise Exception(f"Failed to list groups: {e}")

    def get_group(self, groupname: str) -> Dict[str, Any]:
        """Get details for a specific group."""
        data = self._make_request(self.group_api, "1", "get", name=groupname)
        return data

    def create_user(self, username: str, password: str, email: str = "", description: str = "") -> Dict[str, Any]:
        """Create a new user."""
        print(f"👤 Creating user {username}", file=sys.stderr)
        self._make_request(
            self.user_api, "1", "create",
            use_post=True,
            name=username,
            password=password,
            email=email,
            description=description
        )
        return {'success': True, 'username': username, 'action': 'created'}

    def delete_user(self, username: str) -> Dict[str, Any]:
        """Delete a user."""
        print(f"🗑️ Deleting user {username}", file=sys.stderr)
        self._make_request(self.user_api, "1", "delete", use_post=True, name=username)
        return {'success': True, 'username': username, 'action': 'deleted'}

    # ==================== System Actions ====================

    def reboot(self) -> Dict[str, Any]:
        """Reboot the NAS (use with caution!)."""
        print("⚠️ Initiating system reboot!", file=sys.stderr)
        self._make_request(self.system_info_api, "1", "reboot", use_post=True)
        return {'success': True, 'action': 'rebooting'}

    def shutdown(self) -> Dict[str, Any]:
        """Shutdown the NAS (use with caution!)."""
        print("⚠️ Initiating system shutdown!", file=sys.stderr)
        self._make_request(self.system_info_api, "1", "shutdown", use_post=True)
        return {'success': True, 'action': 'shutting_down'}
