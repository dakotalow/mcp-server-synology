# src/config.py - Configuration management

import os
import re
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# The .env beside main.py. Used to persist the 2FA trusted-device token; the
# working directory is not predictable when an MCP client launches the server.
ENV_FILE = Path(__file__).resolve().parent.parent / '.env'


class SynologyConfig:
    """Configuration manager for Synology MCP Server."""
    
    def __init__(self, env_file: Optional[str] = None):
        """Initialize configuration from environment variables and .env file."""
        # Load .env file if specified or if .env exists
        if env_file:
            load_dotenv(env_file)
        elif os.path.exists('.env'):
            load_dotenv('.env')
        
        self._load_config()
    
    def _load_config(self):
        """Load configuration from environment variables."""
        # Synology connection settings
        self.synology_url = os.getenv('SYNOLOGY_URL')
        self.synology_username = os.getenv('SYNOLOGY_USERNAME')
        self.synology_password = os.getenv('SYNOLOGY_PASSWORD')
        # 2-step verification. SYNOLOGY_DEVICE_ID is the long-lived trusted-device
        # token; SYNOLOGY_OTP_CODE is a one-shot code (run bootstrap_2fa.py instead
        # of setting it by hand, since a code expires in 30 seconds).
        self.synology_device_id = os.getenv('SYNOLOGY_DEVICE_ID') or None
        self.synology_otp_code = os.getenv('SYNOLOGY_OTP_CODE') or None
        
        # Server settings
        self.server_name = os.getenv('MCP_SERVER_NAME', 'synology-mcp-server')
        self.server_version = os.getenv('MCP_SERVER_VERSION', '1.0.0')
        
        # Optional settings
        self.default_session_timeout = int(os.getenv('SESSION_TIMEOUT', '3600'))  # 1 hour
        self.auto_login = os.getenv('AUTO_LOGIN', 'true').lower() == 'true'
        self.verify_ssl = os.getenv('VERIFY_SSL', 'false').lower() == 'true'  # Default false for self-signed certs
        
        # Debug settings
        self.debug = os.getenv('DEBUG', 'false').lower() == 'true'
        self.log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    def has_synology_credentials(self) -> bool:
        """Check if Synology credentials are configured."""
        return bool(self.synology_url and self.synology_username and self.synology_password)
    
    def get_synology_config(self) -> Dict[str, Any]:
        """Get Synology connection configuration."""
        return {
            'base_url': self.synology_url,
            'username': self.synology_username,
            'password': self.synology_password,
            'device_id': self.synology_device_id,
            'otp_code': self.synology_otp_code,
            'verify_ssl': self.verify_ssl
        }
    
    def save_device_id(self, device_id: str, env_file: Path = ENV_FILE) -> bool:
        """Write SYNOLOGY_DEVICE_ID into the .env file and drop any spent OTP.

        DSM can issue a fresh token on a trusted-device login, after which the
        old one stops working, so the newest token has to be saved every time.
        Writes via a 0600 temp file and rename so a crash cannot truncate .env.
        Returns True if the file was changed.
        """
        if not device_id or not env_file.exists():
            return False
        lines = env_file.read_text().splitlines()
        kept = [l for l in lines
                if not re.match(r'\s*(SYNOLOGY_DEVICE_ID|SYNOLOGY_OTP_CODE)\s*=', l)]
        if len(kept) == len(lines) - 1 and f'SYNOLOGY_DEVICE_ID={device_id}' in lines:
            return False  # already saved, no OTP left behind
        out = []
        inserted = False
        for l in kept:
            out.append(l)
            if not inserted and re.match(r'\s*SYNOLOGY_PASSWORD\s*=', l):
                out.append(f'SYNOLOGY_DEVICE_ID={device_id}')
                inserted = True
        if not inserted:
            out.append(f'SYNOLOGY_DEVICE_ID={device_id}')
        fd, tmp = tempfile.mkstemp(dir=env_file.parent, prefix='.env.')
        try:
            with os.fdopen(fd, 'w') as f:
                f.write('\n'.join(out) + '\n')
            os.replace(tmp, env_file)
        except Exception:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise
        self.synology_device_id = device_id
        self.synology_otp_code = None
        os.environ['SYNOLOGY_DEVICE_ID'] = device_id
        os.environ.pop('SYNOLOGY_OTP_CODE', None)
        return True

    def validate_config(self) -> list[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        if not self.synology_url:
            errors.append("SYNOLOGY_URL is required")
        elif not self.synology_url.startswith(('http://', 'https://')):
            errors.append("SYNOLOGY_URL must start with http:// or https://")
        
        if not self.synology_username:
            errors.append("SYNOLOGY_USERNAME is required")
        
        if not self.synology_password:
            errors.append("SYNOLOGY_PASSWORD is required")
        
        if self.default_session_timeout < 60:
            errors.append("SESSION_TIMEOUT must be at least 60 seconds")
        
        return errors
    
    def __str__(self) -> str:
        """String representation of config (without sensitive data)."""
        return f"SynologyConfig(url={self.synology_url}, user={self.synology_username}, auto_login={self.auto_login})"


# Global config instance
config = SynologyConfig() 