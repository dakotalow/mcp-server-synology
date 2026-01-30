# Virtual Machine Manager module for DSM 7.0+

import requests
import json
from typing import Dict, List, Any, Optional
import sys


class SynologyVMM:
    """Handles Synology Virtual Machine Manager API operations."""

    def __init__(self, base_url: str, session_id: str, verify_ssl: bool = False):
        self.base_url = base_url.rstrip('/')
        self.session_id = session_id
        self.api_url = f"{self.base_url}/webapi/entry.cgi"
        self.verify_ssl = verify_ssl

        # API definitions
        self.guest_api = "SYNO.Virtualization.Guest"
        self.image_api = "SYNO.Virtualization.Guest.Image"
        self.network_api = "SYNO.Virtualization.Network"
        self.storage_api = "SYNO.Virtualization.Storage"
        self.cluster_api = "SYNO.Virtualization.Cluster"

    def _make_request(self, api: str, version: str, method: str, use_post: bool = False, **params) -> Dict[str, Any]:
        """Make a request to VMM API."""
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
                raise Exception(f"VMM API error {error_code}")

            return data.get('data', {})

        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {e}")

    # ==================== VM Operations ====================

    def list_guests(self) -> Dict[str, Any]:
        """List all virtual machines."""
        try:
            data = self._make_request(self.guest_api, "1", "List")
            guests = []
            for guest in data.get('guests', []):
                guests.append({
                    'id': guest.get('guest_id'),
                    'name': guest.get('guest_name'),
                    'status': guest.get('status'),
                    'autorun': guest.get('autorun'),
                    'vcpu': guest.get('vcpu_num'),
                    'memory': guest.get('vram_size'),
                    'description': guest.get('desc'),
                    'os_type': guest.get('os_type'),
                    'storage_name': guest.get('storage_name')
                })
            return {'total': len(guests), 'guests': guests}
        except Exception as e:
            raise Exception(f"Failed to list VMs: {e}")

    def get_guest_info(self, guest_id: str) -> Dict[str, Any]:
        """Get detailed info for a specific VM."""
        data = self._make_request(self.guest_api, "1", "Get", guest_id=guest_id)
        return data

    def start_guest(self, guest_id: str) -> Dict[str, Any]:
        """Start a virtual machine."""
        print(f"🖥️ Starting VM {guest_id}", file=sys.stderr)
        self._make_request(self.guest_api, "1", "PowerOn", use_post=True, guest_id=guest_id)
        return {'success': True, 'guest_id': guest_id, 'action': 'started'}

    def stop_guest(self, guest_id: str, force: bool = False) -> Dict[str, Any]:
        """Stop a virtual machine."""
        action = "PowerOff" if force else "Shutdown"
        print(f"🖥️ {'Force stopping' if force else 'Shutting down'} VM {guest_id}", file=sys.stderr)
        self._make_request(self.guest_api, "1", action, use_post=True, guest_id=guest_id)
        return {'success': True, 'guest_id': guest_id, 'action': 'stopped', 'forced': force}

    def restart_guest(self, guest_id: str) -> Dict[str, Any]:
        """Restart a virtual machine."""
        print(f"🔄 Restarting VM {guest_id}", file=sys.stderr)
        self._make_request(self.guest_api, "1", "Restart", use_post=True, guest_id=guest_id)
        return {'success': True, 'guest_id': guest_id, 'action': 'restarted'}

    def suspend_guest(self, guest_id: str) -> Dict[str, Any]:
        """Suspend a virtual machine."""
        print(f"⏸️ Suspending VM {guest_id}", file=sys.stderr)
        self._make_request(self.guest_api, "1", "Suspend", use_post=True, guest_id=guest_id)
        return {'success': True, 'guest_id': guest_id, 'action': 'suspended'}

    def resume_guest(self, guest_id: str) -> Dict[str, Any]:
        """Resume a suspended virtual machine."""
        print(f"▶️ Resuming VM {guest_id}", file=sys.stderr)
        self._make_request(self.guest_api, "1", "Resume", use_post=True, guest_id=guest_id)
        return {'success': True, 'guest_id': guest_id, 'action': 'resumed'}

    # ==================== Snapshot Operations ====================

    def list_snapshots(self, guest_id: str) -> Dict[str, Any]:
        """List snapshots for a VM."""
        data = self._make_request(self.guest_api, "1", "SnapshotList", guest_id=guest_id)
        snapshots = []
        for snap in data.get('snapshots', []):
            snapshots.append({
                'id': snap.get('snapshot_id'),
                'name': snap.get('snapshot_name'),
                'time': snap.get('create_time'),
                'description': snap.get('desc'),
                'locked': snap.get('locked')
            })
        return {'guest_id': guest_id, 'total': len(snapshots), 'snapshots': snapshots}

    def create_snapshot(self, guest_id: str, name: str, description: str = "") -> Dict[str, Any]:
        """Create a snapshot of a VM."""
        print(f"📸 Creating snapshot '{name}' for VM {guest_id}", file=sys.stderr)
        self._make_request(
            self.guest_api, "1", "SnapshotCreate",
            use_post=True,
            guest_id=guest_id,
            snapshot_name=name,
            desc=description
        )
        return {'success': True, 'guest_id': guest_id, 'snapshot_name': name, 'action': 'created'}

    def delete_snapshot(self, guest_id: str, snapshot_id: str) -> Dict[str, Any]:
        """Delete a VM snapshot."""
        print(f"🗑️ Deleting snapshot {snapshot_id} from VM {guest_id}", file=sys.stderr)
        self._make_request(
            self.guest_api, "1", "SnapshotDelete",
            use_post=True,
            guest_id=guest_id,
            snapshot_id=snapshot_id
        )
        return {'success': True, 'guest_id': guest_id, 'snapshot_id': snapshot_id, 'action': 'deleted'}

    def restore_snapshot(self, guest_id: str, snapshot_id: str) -> Dict[str, Any]:
        """Restore a VM to a snapshot."""
        print(f"🔄 Restoring VM {guest_id} to snapshot {snapshot_id}", file=sys.stderr)
        self._make_request(
            self.guest_api, "1", "SnapshotRestore",
            use_post=True,
            guest_id=guest_id,
            snapshot_id=snapshot_id
        )
        return {'success': True, 'guest_id': guest_id, 'snapshot_id': snapshot_id, 'action': 'restored'}

    # ==================== Network Operations ====================

    def list_networks(self) -> Dict[str, Any]:
        """List virtual networks."""
        data = self._make_request(self.network_api, "1", "List")
        networks = []
        for net in data.get('networks', []):
            networks.append({
                'id': net.get('network_id'),
                'name': net.get('network_name'),
                'type': net.get('type'),
                'vswitch': net.get('vswitch_name'),
                'vlan_id': net.get('vlan_id')
            })
        return {'total': len(networks), 'networks': networks}

    # ==================== Storage Operations ====================

    def list_storage(self) -> Dict[str, Any]:
        """List VM storage pools."""
        data = self._make_request(self.storage_api, "1", "List")
        return data

    # ==================== Cluster Operations ====================

    def get_cluster_info(self) -> Dict[str, Any]:
        """Get VMM cluster information."""
        try:
            data = self._make_request(self.cluster_api, "1", "Get")
            return data
        except Exception:
            return {'cluster': 'standalone', 'note': 'No cluster configured'}
