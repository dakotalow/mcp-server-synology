# Surveillance Station module for DSM 7.0+

import requests
import json
from typing import Dict, List, Any, Optional
import sys


class SynologySurveillance:
    """Handles Synology Surveillance Station API operations."""

    def __init__(self, base_url: str, session_id: str, verify_ssl: bool = False):
        self.base_url = base_url.rstrip('/')
        self.session_id = session_id
        self.api_url = f"{self.base_url}/webapi/entry.cgi"
        self.verify_ssl = verify_ssl

        # API definitions
        self.camera_api = "SYNO.SurveillanceStation.Camera"
        self.recording_api = "SYNO.SurveillanceStation.Recording"
        self.event_api = "SYNO.SurveillanceStation.Event"
        self.info_api = "SYNO.SurveillanceStation.Info"
        self.ptz_api = "SYNO.SurveillanceStation.PTZ"
        self.snapshot_api = "SYNO.SurveillanceStation.SnapShot"
        self.home_mode_api = "SYNO.SurveillanceStation.HomeMode"

    def _make_request(self, api: str, version: str, method: str, use_post: bool = False, **params) -> Dict[str, Any]:
        """Make a request to Surveillance Station API."""
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
                raise Exception(f"Surveillance Station API error {error_code}")

            return data.get('data', {})

        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {e}")

    # ==================== Info Operations ====================

    def get_info(self) -> Dict[str, Any]:
        """Get Surveillance Station information."""
        try:
            data = self._make_request(self.info_api, "1", "GetInfo")
            return data
        except Exception as e:
            raise Exception(f"Failed to get Surveillance Station info: {e}")

    # ==================== Camera Operations ====================

    def list_cameras(self) -> Dict[str, Any]:
        """List all cameras."""
        try:
            data = self._make_request(self.camera_api, "9", "List")
            cameras = []
            for cam in data.get('cameras', []):
                cameras.append({
                    'id': cam.get('id'),
                    'name': cam.get('name'),
                    'ip': cam.get('ip'),
                    'port': cam.get('port'),
                    'model': cam.get('model'),
                    'vendor': cam.get('vendor'),
                    'status': cam.get('status'),
                    'enabled': cam.get('enabled'),
                    'recording': cam.get('recStatus'),
                    'fps': cam.get('fps'),
                    'resolution': f"{cam.get('resolution', {}).get('width', 0)}x{cam.get('resolution', {}).get('height', 0)}"
                })
            return {'total': len(cameras), 'cameras': cameras}
        except Exception as e:
            raise Exception(f"Failed to list cameras: {e}")

    def get_camera_info(self, camera_id: int) -> Dict[str, Any]:
        """Get detailed info for a specific camera."""
        data = self._make_request(self.camera_api, "9", "GetInfo", cameraIds=str(camera_id))
        return data.get('cameras', [{}])[0] if data.get('cameras') else {}

    def enable_camera(self, camera_id: int) -> Dict[str, Any]:
        """Enable a camera."""
        print(f"📷 Enabling camera {camera_id}", file=sys.stderr)
        self._make_request(self.camera_api, "9", "Enable", use_post=True, cameraIds=str(camera_id))
        return {'success': True, 'camera_id': camera_id, 'action': 'enabled'}

    def disable_camera(self, camera_id: int) -> Dict[str, Any]:
        """Disable a camera."""
        print(f"📷 Disabling camera {camera_id}", file=sys.stderr)
        self._make_request(self.camera_api, "9", "Disable", use_post=True, cameraIds=str(camera_id))
        return {'success': True, 'camera_id': camera_id, 'action': 'disabled'}

    # ==================== Recording Operations ====================

    def list_recordings(self, camera_id: Optional[int] = None, limit: int = 50) -> Dict[str, Any]:
        """List recordings, optionally filtered by camera."""
        params = {'limit': limit}
        if camera_id:
            params['cameraIds'] = str(camera_id)

        data = self._make_request(self.recording_api, "5", "List", **params)
        recordings = []
        for rec in data.get('recordings', []):
            recordings.append({
                'id': rec.get('id'),
                'camera_id': rec.get('cameraId'),
                'camera_name': rec.get('cameraName'),
                'start_time': rec.get('startTime'),
                'stop_time': rec.get('stopTime'),
                'file_size': rec.get('fileSize'),
                'event_type': rec.get('eventType')
            })
        return {'total': data.get('total', len(recordings)), 'recordings': recordings}

    def delete_recording(self, recording_id: int) -> Dict[str, Any]:
        """Delete a recording."""
        print(f"🗑️ Deleting recording {recording_id}", file=sys.stderr)
        self._make_request(self.recording_api, "5", "Delete", use_post=True, id=recording_id)
        return {'success': True, 'recording_id': recording_id, 'action': 'deleted'}

    # ==================== Event Operations ====================

    def list_events(self, camera_id: Optional[int] = None, limit: int = 50) -> Dict[str, Any]:
        """List motion detection events."""
        params = {'limit': limit}
        if camera_id:
            params['cameraIds'] = str(camera_id)

        data = self._make_request(self.event_api, "5", "List", **params)
        events = []
        for event in data.get('events', []):
            events.append({
                'id': event.get('id'),
                'camera_id': event.get('cameraId'),
                'camera_name': event.get('cameraName'),
                'time': event.get('time'),
                'event_type': event.get('eventType'),
                'reason': event.get('reason')
            })
        return {'total': data.get('total', len(events)), 'events': events}

    # ==================== Snapshot Operations ====================

    def take_snapshot(self, camera_id: int) -> Dict[str, Any]:
        """Take a snapshot from a camera."""
        print(f"📸 Taking snapshot from camera {camera_id}", file=sys.stderr)
        data = self._make_request(self.snapshot_api, "1", "TakeSnapshot", use_post=True, cameraId=camera_id)
        return {'success': True, 'camera_id': camera_id, 'snapshot': data}

    # ==================== PTZ Operations ====================

    def ptz_move(self, camera_id: int, direction: str) -> Dict[str, Any]:
        """Move PTZ camera (up, down, left, right, home)."""
        valid_directions = ['up', 'down', 'left', 'right', 'home', 'zoom_in', 'zoom_out']
        if direction.lower() not in valid_directions:
            raise Exception(f"Invalid direction. Must be one of: {valid_directions}")

        print(f"🎥 Moving camera {camera_id} {direction}", file=sys.stderr)
        self._make_request(self.ptz_api, "5", "Move", use_post=True, cameraId=camera_id, direction=direction)
        return {'success': True, 'camera_id': camera_id, 'direction': direction}

    # ==================== Home Mode Operations ====================

    def get_home_mode(self) -> Dict[str, Any]:
        """Get current home mode status."""
        data = self._make_request(self.home_mode_api, "1", "GetInfo")
        return data

    def set_home_mode(self, enabled: bool) -> Dict[str, Any]:
        """Enable or disable home mode."""
        mode = "on" if enabled else "off"
        print(f"🏠 Setting home mode to {mode}", file=sys.stderr)
        self._make_request(self.home_mode_api, "1", "Switch", use_post=True, on=enabled)
        return {'success': True, 'home_mode': enabled}
