# src/synology_auth.py - Simple Synology authentication utilities

import requests
import urllib3
from typing import Dict, Any, Optional

# Suppress SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Connection timeout in seconds (connect timeout, read timeout)
DEFAULT_TIMEOUT = (5, 10)


def _refused_redirect(response) -> Dict[str, Any]:
    """Failure returned when auth.cgi answers with a 3xx (not followed)."""
    location = response.headers.get('Location', '<no Location header>')
    return {
        'success': False,
        'error': {
            'code': 'unexpected_redirect',
            'message': (f"auth.cgi returned HTTP {response.status_code} redirecting to "
                        f"{location}; refused so no credentials were sent there. "
                        "Set SYNOLOGY_URL to the final https:// address."),
        },
    }


class SynologyAuth:
    """Handles Synology NAS authentication using simple API calls."""

    def __init__(self, base_url: str, timeout: tuple = DEFAULT_TIMEOUT):
        self.base_url = base_url.rstrip('/')
        self.current_session_id: Optional[str] = None
        self.current_session_type: str = 'FileStation'
        # Trusted-device token from the last 2FA login, for the caller to persist.
        self.current_device_id: Optional[str] = None
        self.timeout = timeout
    
    def login(self, username: str, password: str,
              otp_code: Optional[str] = None,
              device_id: Optional[str] = None) -> Dict[str, Any]:
        """Authenticate with Synology NAS and return session info.

        For accounts with 2-step verification:
            - device_id: a trusted-device token (`did`) DSM issued on an earlier
              OTP login. DSM skips the OTP step when it is presented.
            - otp_code: a one-time 6-digit code, needed only for the first login
              (when no device_id exists yet). DSM is asked to issue a device
              token, which is left in `current_device_id` for the caller to save.
        """
        return self.login_with_session(username, password, 'FileStation',
                                       otp_code=otp_code, device_id=device_id)

    def login_with_session(self, username: str, password: str, session_type: str = 'FileStation',
                           otp_code: Optional[str] = None,
                           device_id: Optional[str] = None) -> Dict[str, Any]:
        """Authenticate with Synology NAS using specific session type."""
        login_url = f"{self.base_url}/webapi/auth.cgi"

        # Try common API versions (start with newer versions)
        api_versions = ['7', '6', '3', '2']
        # First-time 2FA login: v7 can succeed without returning a device token
        # (seen on DSM 7.3.2), which leaves every later start asking for an OTP.
        # v6 returns it. Ported from upstream atom2ueki/mcp-server-synology 1.8.0.
        if otp_code and not device_id:
            api_versions = ['6', '7', '3', '2']

        for version in api_versions:
            payload = {
                'api': 'SYNO.API.Auth',
                'version': version,
                'method': 'login',
                'account': username,
                'passwd': password,
                'session': session_type,
                'format': 'sid'
            }
            if device_id:
                payload['device_id'] = device_id
            elif otp_code:
                payload['otp_code'] = otp_code
                payload['enable_device_token'] = 'yes'

            try:
                # POST, not GET: a password or OTP in the query string lands in
                # DSM's access log. Redirects are refused because requests would
                # replay this body, credentials included, to the redirect target.
                response = requests.post(login_url, data=payload, verify=False,
                                         timeout=self.timeout, allow_redirects=False)
                if 300 <= response.status_code < 400:
                    return _refused_redirect(response)
                response.raise_for_status()
                result = response.json()

                if result.get('success'):
                    # Store session info for automatic logout
                    self.current_session_id = result['data']['sid']
                    self.current_session_type = session_type
                    # DSM returns `did` only on the OTP path; on the trusted-device
                    # path it may issue a fresh one or echo nothing.
                    did = result['data'].get('did') or device_id
                    if did:
                        self.current_device_id = did
                    return result
                else:
                    error_code = result.get('error', {}).get('code', 'unknown')
                    # Don't try other versions for auth errors
                    if error_code in [400, 401, 402, 403, 404]:
                        return result
            except Exception:
                continue

        # If all versions failed, return the last result
        return {'success': False, 'error': {'code': 'unknown', 'message': 'Authentication failed'}}

    def login_download_station(self, username: str, password: str,
                               otp_code: Optional[str] = None,
                               device_id: Optional[str] = None) -> Dict[str, Any]:
        """Authenticate specifically for Download Station."""
        return self.login_with_session(username, password, 'DownloadStation',
                                       otp_code=otp_code, device_id=device_id)

    def logout(self, session_id: Optional[str] = None, session_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Logout from Synology NAS.
        
        Args:
            session_id: Session ID to logout. If None, uses current session.
            session_type: Session type to logout. If None, uses current session type.
        
        Returns:
            Dict with success status and any error details.
        """
        # Use provided parameters or fall back to current session
        logout_session_id = session_id or self.current_session_id
        logout_session_type = session_type or self.current_session_type
        
        if not logout_session_id:
            return {
                'success': False, 
                'error': {'code': 'no_session', 'message': 'No session ID provided or available'}
            }
        
        logout_url = f"{self.base_url}/webapi/auth.cgi"
        
        # Try multiple API versions for logout (same approach as login)
        api_versions = ['7', '6', '3', '2']
        last_error = None
        
        for version in api_versions:
            payload = {
                'api': 'SYNO.API.Auth',
                'version': version,
                'method': 'logout',
                'session': logout_session_type,
                '_sid': logout_session_id
            }
            
            try:
                response = requests.post(logout_url, data=payload, verify=False,
                                         timeout=self.timeout, allow_redirects=False)
                if 300 <= response.status_code < 400:
                    return _refused_redirect(response)
                response.raise_for_status()
                result = response.json()

                if result.get('success'):
                    # Clear current session if we logged out our own session
                    if logout_session_id == self.current_session_id:
                        self.current_session_id = None
                        self.current_session_type = 'FileStation'
                    return result
                else:
                    last_error = result
                    error_code = result.get('error', {}).get('code', 'unknown')
                    # For certain errors, don't try other versions
                    if error_code in [105, 106]:  # Invalid session or not logged in
                        break

            except requests.RequestException as e:
                last_error = {
                    'success': False, 
                    'error': {'code': 'network_error', 'message': f'Network error: {str(e)}'}
                }
                continue
            except Exception as e:
                last_error = {
                    'success': False, 
                    'error': {'code': 'unknown_error', 'message': f'Unexpected error: {str(e)}'}
                }
                continue
        
        # If we reach here, all attempts failed
        if last_error:
            return last_error
        else:
            return {
                'success': False, 
                'error': {'code': 'all_versions_failed', 'message': 'Logout failed with all API versions'}
            }
    
    def is_logged_in(self) -> bool:
        """Check if there's an active session."""
        return self.current_session_id is not None
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get current session information."""
        return {
            'session_id': self.current_session_id,
            'session_type': self.current_session_type,
            'logged_in': self.is_logged_in()
        } 