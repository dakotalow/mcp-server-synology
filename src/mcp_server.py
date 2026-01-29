# src/mcp_server.py - MCP Server for Synology NAS operations

import asyncio
import json
import sys
import requests
from typing import Any, Dict, Optional
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

import mcp.types as types
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.lowlevel import NotificationOptions
import mcp.server.stdio

from config import config
from auth import SynologyAuth
from filestation import SynologyFileStation
from downloadstation import SynologyDownloadStation
from docker import SynologyDocker
from surveillance import SynologySurveillance
from hyperbackup import SynologyHyperBackup
from vmm import SynologyVMM
from drive import SynologyDrive
from system import SynologySystem
from network import SynologyNetwork
from mcp_handlers_extended import get_extended_tool_definitions


class SynologyMCPServer:
    """MCP Server for Synology NAS operations."""
    
    def __init__(self):
        self.server = Server(config.server_name)
        self.auth_instances: Dict[str, SynologyAuth] = {}
        self.sessions: Dict[str, str] = {}  # base_url -> session_id
        self.filestation_instances: Dict[str, SynologyFileStation] = {}
        self.downloadstation_instances: Dict[str, SynologyDownloadStation] = {}
        self.docker_instances: Dict[str, SynologyDocker] = {}
        self.surveillance_instances: Dict[str, SynologySurveillance] = {}
        self.hyperbackup_instances: Dict[str, SynologyHyperBackup] = {}
        self.vmm_instances: Dict[str, SynologyVMM] = {}
        self.drive_instances: Dict[str, SynologyDrive] = {}
        self.system_instances: Dict[str, SynologySystem] = {}
        self.network_instances: Dict[str, SynologyNetwork] = {}
        self._setup_handlers()
    
    def _get_filestation(self, base_url: str) -> SynologyFileStation:
        """Get or create FileStation instance for a base URL."""
        if base_url not in self.sessions:
            raise Exception(f"No active session for {base_url}. Please login first.")
        
        if base_url not in self.filestation_instances:
            session_id = self.sessions[base_url]
            self.filestation_instances[base_url] = SynologyFileStation(base_url, session_id)
        
        return self.filestation_instances[base_url]
    
    def _get_downloadstation(self, base_url: str) -> SynologyDownloadStation:
        """Get or create DownloadStation instance for a base URL."""
        if base_url not in self.sessions:
            raise Exception(f"No active session for {base_url}. Please login first.")

        if base_url not in self.downloadstation_instances:
            session_id = self.sessions[base_url]
            self.downloadstation_instances[base_url] = SynologyDownloadStation(base_url, session_id)

        return self.downloadstation_instances[base_url]

    def _get_docker(self, base_url: str) -> SynologyDocker:
        """Get or create Docker instance for a base URL."""
        if base_url not in self.sessions:
            raise Exception(f"No active session for {base_url}. Please login first.")

        if base_url not in self.docker_instances:
            session_id = self.sessions[base_url]
            self.docker_instances[base_url] = SynologyDocker(base_url, session_id)

        return self.docker_instances[base_url]

    def _get_surveillance(self, base_url: str) -> SynologySurveillance:
        """Get or create Surveillance Station instance for a base URL."""
        if base_url not in self.sessions:
            raise Exception(f"No active session for {base_url}. Please login first.")

        if base_url not in self.surveillance_instances:
            session_id = self.sessions[base_url]
            self.surveillance_instances[base_url] = SynologySurveillance(base_url, session_id)

        return self.surveillance_instances[base_url]

    def _get_hyperbackup(self, base_url: str) -> SynologyHyperBackup:
        """Get or create Hyper Backup instance for a base URL."""
        if base_url not in self.sessions:
            raise Exception(f"No active session for {base_url}. Please login first.")

        if base_url not in self.hyperbackup_instances:
            session_id = self.sessions[base_url]
            self.hyperbackup_instances[base_url] = SynologyHyperBackup(base_url, session_id)

        return self.hyperbackup_instances[base_url]

    def _get_vmm(self, base_url: str) -> SynologyVMM:
        """Get or create VMM instance for a base URL."""
        if base_url not in self.sessions:
            raise Exception(f"No active session for {base_url}. Please login first.")

        if base_url not in self.vmm_instances:
            session_id = self.sessions[base_url]
            self.vmm_instances[base_url] = SynologyVMM(base_url, session_id)

        return self.vmm_instances[base_url]

    def _get_drive(self, base_url: str) -> SynologyDrive:
        """Get or create Synology Drive instance for a base URL."""
        if base_url not in self.sessions:
            raise Exception(f"No active session for {base_url}. Please login first.")

        if base_url not in self.drive_instances:
            session_id = self.sessions[base_url]
            self.drive_instances[base_url] = SynologyDrive(base_url, session_id)

        return self.drive_instances[base_url]

    def _get_system(self, base_url: str) -> SynologySystem:
        """Get or create System instance for a base URL."""
        if base_url not in self.sessions:
            raise Exception(f"No active session for {base_url}. Please login first.")

        if base_url not in self.system_instances:
            session_id = self.sessions[base_url]
            self.system_instances[base_url] = SynologySystem(base_url, session_id)

        return self.system_instances[base_url]

    def _get_network(self, base_url: str) -> SynologyNetwork:
        """Get or create Network instance for a base URL."""
        if base_url not in self.sessions:
            raise Exception(f"No active session for {base_url}. Please login first.")

        if base_url not in self.network_instances:
            session_id = self.sessions[base_url]
            self.network_instances[base_url] = SynologyNetwork(base_url, session_id)

        return self.network_instances[base_url]
    
    async def _auto_login_if_configured(self):
        """Automatically login if credentials are configured and auto_login is enabled."""
        # Debug output to see what config values we have
        print(f"🔍 DEBUG: config.auto_login = {config.auto_login}", file=sys.stderr)
        print(f"🔍 DEBUG: config.has_synology_credentials() = {config.has_synology_credentials()}", file=sys.stderr)
        print(f"🔍 DEBUG: config = {config}", file=sys.stderr)
        
        if config.auto_login and config.has_synology_credentials():
            try:
                synology_config = config.get_synology_config()
                base_url = synology_config['base_url']
                
                print(f"Auto-login enabled, attempting to login to {base_url}", file=sys.stderr)
                
                # Create auth instance
                if base_url not in self.auth_instances:
                    self.auth_instances[base_url] = SynologyAuth(base_url)
                
                auth = self.auth_instances[base_url]
                result = auth.login(synology_config['username'], synology_config['password'])
                
                if result.get("success"):
                    session_id = result["data"]["sid"]
                    self.sessions[base_url] = session_id
                    print(f"✅ Auto-login successful for {base_url} (Session: {session_id[:8]}...)", file=sys.stderr)
                    
                    # Clear any existing instances to force recreation with new session
                    if base_url in self.filestation_instances:
                        del self.filestation_instances[base_url]
                    if base_url in self.downloadstation_instances:
                        del self.downloadstation_instances[base_url]
                    if base_url in self.docker_instances:
                        del self.docker_instances[base_url]
                else:
                    error_msg = f"Auto-login failed for {base_url}: {result}"
                    print(f"❌ {error_msg}", file=sys.stderr)
                    print("⚠️  Server will continue without auto-login. Use manual login or check NAS connectivity.", file=sys.stderr)

            except requests.exceptions.ConnectTimeout:
                print(f"❌ Auto-login timeout: Could not connect to {base_url} within 5 seconds", file=sys.stderr)
                print("⚠️  Server will continue without auto-login. Check VPN/network connection.", file=sys.stderr)
            except requests.exceptions.ConnectionError as e:
                print(f"❌ Auto-login connection error: {e}", file=sys.stderr)
                print("⚠️  Server will continue without auto-login. NAS may be unreachable.", file=sys.stderr)
            except Exception as e:
                error_msg = f"Auto-login error: {e}"
                print(f"❌ {error_msg}", file=sys.stderr)
                if config.debug:
                    import traceback
                    traceback.print_exc(file=sys.stderr)
                print("⚠️  Server will continue without auto-login.", file=sys.stderr)
        elif not config.auto_login:
            print("⚠️  Auto-login disabled (AUTO_LOGIN=false)", file=sys.stderr)
        elif not config.has_synology_credentials():
            print("⚠️  No Synology credentials configured", file=sys.stderr)
        else:
            print("⚠️  Auto-login conditions not met", file=sys.stderr)
    
    def _setup_handlers(self):
        """Setup MCP server handlers."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """List available Synology tools."""
            tools = self._get_tool_definitions()
            
            # Add login/logout tools only if not using auto-login or no credentials configured
            if not config.auto_login or not config.has_synology_credentials():
                tools.extend([
                    types.Tool(
                        name="synology_login",
                        description="Authenticate with Synology NAS and establish session",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "base_url": {
                                    "type": "string",
                                    "description": "Synology NAS base URL (e.g., https://192.168.1.100:5001)"
                                },
                                "username": {
                                    "type": "string",
                                    "description": "Username for authentication"
                                },
                                "password": {
                                    "type": "string",
                                    "description": "Password for authentication"
                                }
                            },
                            "required": ["base_url", "username", "password"]
                        }
                    ),
                    types.Tool(
                        name="synology_logout",
                        description="Logout from Synology NAS session",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "base_url": {
                                    "type": "string",
                                    "description": "Synology NAS base URL"
                                }
                            },
                            "required": ["base_url"]
                        }
                    )
                ])
            
            return tools
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
            """Handle tool calls."""
            try:
                print(f"🛠️ Executing tool: {name}", file=sys.stderr)
                if name == "synology_login":
                    return await self._handle_login(arguments)
                elif name == "synology_logout":
                    return await self._handle_logout(arguments)
                elif name == "synology_status":
                    return await self._handle_status(arguments)
                elif name == "list_shares":
                    return await self._handle_list_shares(arguments)
                elif name == "list_directory":
                    return await self._handle_list_directory(arguments)
                elif name == "get_file_info":
                    return await self._handle_get_file_info(arguments)
                elif name == "search_files":
                    return await self._handle_search_files(arguments)
                elif name == "get_file_content":
                    return await self._handle_get_file_content(arguments)
                elif name == "rename_file":
                    return await self._handle_rename_file(arguments)
                elif name == "move_file":
                    return await self._handle_move_file(arguments)
                elif name == "create_file":
                    return await self._handle_create_file(arguments)
                elif name == "create_directory":
                    return await self._handle_create_directory(arguments)
                elif name == "delete":
                    return await self._handle_delete(arguments)
                # Download Station handlers
                elif name == "ds_get_info":
                    return await self._handle_ds_get_info(arguments)
                elif name == "ds_list_tasks":
                    return await self._handle_ds_list_tasks(arguments)
                elif name == "ds_create_task":
                    return await self._handle_ds_create_task(arguments)
                elif name == "ds_pause_tasks":
                    return await self._handle_ds_pause_tasks(arguments)
                elif name == "ds_resume_tasks":
                    return await self._handle_ds_resume_tasks(arguments)
                elif name == "ds_delete_tasks":
                    return await self._handle_ds_delete_tasks(arguments)
                elif name == "ds_get_statistics":
                    return await self._handle_ds_get_statistics(arguments)
                elif name == "ds_list_downloaded_files":
                    return await self._handle_ds_list_downloaded_files(arguments)
                # Docker/Container Manager handlers
                elif name == "docker_list_containers":
                    return await self._handle_docker_list_containers(arguments)
                elif name == "docker_get_container":
                    return await self._handle_docker_get_container(arguments)
                elif name == "docker_start_container":
                    return await self._handle_docker_start_container(arguments)
                elif name == "docker_stop_container":
                    return await self._handle_docker_stop_container(arguments)
                elif name == "docker_restart_container":
                    return await self._handle_docker_restart_container(arguments)
                elif name == "docker_delete_container":
                    return await self._handle_docker_delete_container(arguments)
                elif name == "docker_get_container_logs":
                    return await self._handle_docker_get_container_logs(arguments)
                elif name == "docker_get_container_stats":
                    return await self._handle_docker_get_container_stats(arguments)
                elif name == "docker_list_images":
                    return await self._handle_docker_list_images(arguments)
                elif name == "docker_pull_image":
                    return await self._handle_docker_pull_image(arguments)
                elif name == "docker_delete_image":
                    return await self._handle_docker_delete_image(arguments)
                elif name == "docker_list_projects":
                    return await self._handle_docker_list_projects(arguments)
                elif name == "docker_start_project":
                    return await self._handle_docker_start_project(arguments)
                elif name == "docker_stop_project":
                    return await self._handle_docker_stop_project(arguments)
                elif name == "docker_list_networks":
                    return await self._handle_docker_list_networks(arguments)
                # Surveillance Station handlers
                elif name == "surveillance_list_cameras":
                    return await self._handle_surveillance_list_cameras(arguments)
                elif name == "surveillance_get_camera":
                    return await self._handle_surveillance_get_camera(arguments)
                elif name == "surveillance_enable_camera":
                    return await self._handle_surveillance_enable_camera(arguments)
                elif name == "surveillance_disable_camera":
                    return await self._handle_surveillance_disable_camera(arguments)
                elif name == "surveillance_list_recordings":
                    return await self._handle_surveillance_list_recordings(arguments)
                elif name == "surveillance_take_snapshot":
                    return await self._handle_surveillance_take_snapshot(arguments)
                elif name == "surveillance_get_home_mode":
                    return await self._handle_surveillance_get_home_mode(arguments)
                elif name == "surveillance_set_home_mode":
                    return await self._handle_surveillance_set_home_mode(arguments)
                # Hyper Backup handlers
                elif name == "backup_list_tasks":
                    return await self._handle_backup_list_tasks(arguments)
                elif name == "backup_get_task":
                    return await self._handle_backup_get_task(arguments)
                elif name == "backup_start":
                    return await self._handle_backup_start(arguments)
                elif name == "backup_cancel":
                    return await self._handle_backup_cancel(arguments)
                elif name == "backup_list_versions":
                    return await self._handle_backup_list_versions(arguments)
                elif name == "backup_get_stats":
                    return await self._handle_backup_get_stats(arguments)
                # VMM handlers
                elif name == "vmm_list_guests":
                    return await self._handle_vmm_list_guests(arguments)
                elif name == "vmm_get_guest":
                    return await self._handle_vmm_get_guest(arguments)
                elif name == "vmm_start_guest":
                    return await self._handle_vmm_start_guest(arguments)
                elif name == "vmm_stop_guest":
                    return await self._handle_vmm_stop_guest(arguments)
                elif name == "vmm_restart_guest":
                    return await self._handle_vmm_restart_guest(arguments)
                elif name == "vmm_list_snapshots":
                    return await self._handle_vmm_list_snapshots(arguments)
                elif name == "vmm_create_snapshot":
                    return await self._handle_vmm_create_snapshot(arguments)
                elif name == "vmm_restore_snapshot":
                    return await self._handle_vmm_restore_snapshot(arguments)
                # Drive handlers
                elif name == "drive_list_connections":
                    return await self._handle_drive_list_connections(arguments)
                elif name == "drive_list_team_folders":
                    return await self._handle_drive_list_team_folders(arguments)
                elif name == "drive_list_share_links":
                    return await self._handle_drive_list_share_links(arguments)
                elif name == "drive_create_share_link":
                    return await self._handle_drive_create_share_link(arguments)
                elif name == "drive_get_sync_status":
                    return await self._handle_drive_get_sync_status(arguments)
                elif name == "drive_list_file_versions":
                    return await self._handle_drive_list_file_versions(arguments)
                # System handlers
                elif name == "system_get_info":
                    return await self._handle_system_get_info(arguments)
                elif name == "system_get_utilization":
                    return await self._handle_system_get_utilization(arguments)
                elif name == "storage_list_volumes":
                    return await self._handle_storage_list_volumes(arguments)
                elif name == "storage_list_disks":
                    return await self._handle_storage_list_disks(arguments)
                elif name == "logs_get":
                    return await self._handle_logs_get(arguments)
                elif name == "logs_clear":
                    return await self._handle_logs_clear(arguments)
                elif name == "package_list":
                    return await self._handle_package_list(arguments)
                elif name == "package_start":
                    return await self._handle_package_start(arguments)
                elif name == "package_stop":
                    return await self._handle_package_stop(arguments)
                elif name == "users_list":
                    return await self._handle_users_list(arguments)
                elif name == "users_get":
                    return await self._handle_users_get(arguments)
                elif name == "groups_list":
                    return await self._handle_groups_list(arguments)
                elif name == "system_reboot":
                    return await self._handle_system_reboot(arguments)
                elif name == "system_shutdown":
                    return await self._handle_system_shutdown(arguments)
                # Network handlers
                elif name == "dns_list_zones":
                    return await self._handle_dns_list_zones(arguments)
                elif name == "dns_list_records":
                    return await self._handle_dns_list_records(arguments)
                elif name == "dns_create_record":
                    return await self._handle_dns_create_record(arguments)
                elif name == "dns_delete_record":
                    return await self._handle_dns_delete_record(arguments)
                elif name == "dhcp_get_status":
                    return await self._handle_dhcp_get_status(arguments)
                elif name == "dhcp_list_leases":
                    return await self._handle_dhcp_list_leases(arguments)
                elif name == "dhcp_list_reservations":
                    return await self._handle_dhcp_list_reservations(arguments)
                elif name == "dhcp_create_reservation":
                    return await self._handle_dhcp_create_reservation(arguments)
                elif name == "dhcp_delete_reservation":
                    return await self._handle_dhcp_delete_reservation(arguments)
                elif name == "vpn_get_status":
                    return await self._handle_vpn_get_status(arguments)
                elif name == "vpn_list_connections":
                    return await self._handle_vpn_list_connections(arguments)
                elif name == "vpn_disconnect_client":
                    return await self._handle_vpn_disconnect_client(arguments)
                elif name == "vpn_list_users":
                    return await self._handle_vpn_list_users(arguments)
                elif name == "network_get_info":
                    return await self._handle_network_get_info(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
            except Exception as e:
                return [types.TextContent(
                    type="text",
                    text=f"Error executing {name}: {str(e)}"
                )]
    
    def _get_base_url(self, arguments: dict) -> str:
        """Get base URL from arguments or config."""
        base_url = arguments.get("base_url")
        if not base_url:
            if config.synology_url:
                base_url = config.synology_url
            else:
                raise Exception("No base_url provided and SYNOLOGY_URL not configured in .env")
        return base_url
    
    async def _handle_login(self, arguments: dict) -> list[types.TextContent]:
        """Handle Synology login."""
        base_url = arguments["base_url"]
        username = arguments["username"]
        password = arguments["password"]
        
        # Create or get auth instance
        if base_url not in self.auth_instances:
            self.auth_instances[base_url] = SynologyAuth(base_url)
        
        auth = self.auth_instances[base_url]
        
        # Perform login
        result = auth.login(username, password)
        
        # Store session if successful
        if result.get("success"):
            session_id = result["data"]["sid"]
            self.sessions[base_url] = session_id

            # Clear any existing instances to force recreation with new session
            if base_url in self.filestation_instances:
                del self.filestation_instances[base_url]
            if base_url in self.downloadstation_instances:
                del self.downloadstation_instances[base_url]
            if base_url in self.docker_instances:
                del self.docker_instances[base_url]

            return [types.TextContent(
                type="text",
                text=f"Successfully authenticated with {base_url}\n"
                     f"Session ID: {session_id}\n"
                     f"Response: {json.dumps(result, indent=2)}"
            )]
        else:
            return [types.TextContent(
                type="text",
                text=f"Authentication failed: {json.dumps(result, indent=2)}"
            )]
    
    async def _handle_logout(self, arguments: dict) -> list[types.TextContent]:
        """Handle Synology logout."""
        base_url = self._get_base_url(arguments)
        
        if base_url not in self.sessions:
            return [types.TextContent(
                type="text",
                text=f"No active session found for {base_url}"
            )]
        
        session_id = self.sessions[base_url]
        auth = self.auth_instances[base_url]
        
        # Use the improved logout method
        result = auth.logout(session_id)
        
        # Handle the result and provide detailed feedback
        if result.get('success'):
            # Remove session and all service instances on successful logout
            del self.sessions[base_url]
            if base_url in self.filestation_instances:
                del self.filestation_instances[base_url]
            if base_url in self.downloadstation_instances:
                del self.downloadstation_instances[base_url]
            if base_url in self.docker_instances:
                del self.docker_instances[base_url]

            return [types.TextContent(
                type="text",
                text=f"✅ Successfully logged out from {base_url}\n"
                     f"Session {session_id[:10]}... has been terminated"
            )]
        else:
            error_info = result.get('error', {})
            error_code = error_info.get('code', 'unknown')
            error_msg = error_info.get('message', 'Unknown error')

            # Handle expected session expiration gracefully
            if error_code in ['105', '106', 'no_session']:
                # Still clean up local session data
                del self.sessions[base_url]
                if base_url in self.filestation_instances:
                    del self.filestation_instances[base_url]
                if base_url in self.downloadstation_instances:
                    del self.downloadstation_instances[base_url]
                if base_url in self.docker_instances:
                    del self.docker_instances[base_url]
                
                return [types.TextContent(
                    type="text",
                    text=f"⚠️ Session for {base_url} was already expired or invalid\n"
                         f"Local session data has been cleaned up\n"
                         f"Details: {error_code} - {error_msg}"
                )]
            else:
                return [types.TextContent(
                    type="text",
                    text=f"❌ Logout failed for {base_url}\n"
                         f"Error: {error_code} - {error_msg}\n"
                         f"Full response: {json.dumps(result, indent=2)}"
                )]
    
    async def _handle_status(self, arguments: dict) -> list[types.TextContent]:
        """Handle status check."""
        status_info = []
        
        # Show configuration status
        if config.has_synology_credentials():
            status_info.append(f"✓ Configuration: {config.synology_url} (user: {config.synology_username})")
            status_info.append(f"✓ Auto-login: {'enabled' if config.auto_login else 'disabled'}")
        else:
            status_info.append("⚠ No Synology credentials configured in .env")
        
        # Show active sessions with detailed info
        if self.sessions:
            status_info.append(f"\nActive sessions ({len(self.sessions)}):")
            for base_url, session_id in self.sessions.items():
                auth = self.auth_instances.get(base_url)
                if auth and auth.is_logged_in():
                    session_info = auth.get_session_info()
                    session_type = session_info.get('session_type', 'Unknown')
                    status_info.append(f"• {base_url}: {session_type} session {session_id[:10]}...")
                else:
                    status_info.append(f"• {base_url}: Session {session_id[:10]}... (status unknown)")
                    
            # Show service instances
            if self.filestation_instances:
                status_info.append(f"\nFileStation instances: {len(self.filestation_instances)}")
            if self.downloadstation_instances:
                status_info.append(f"DownloadStation instances: {len(self.downloadstation_instances)}")
            if self.docker_instances:
                status_info.append(f"Docker instances: {len(self.docker_instances)}")
        else:
            status_info.append("\nNo active Synology sessions")
        
        return [types.TextContent(
            type="text",
            text="\n".join(status_info)
        )]
    
    async def _handle_list_shares(self, arguments: dict) -> list[types.TextContent]:
        """Handle listing shares."""
        base_url = self._get_base_url(arguments)
        filestation = self._get_filestation(base_url)
        
        shares = filestation.list_shares()
        
        return [types.TextContent(
            type="text",
            text=json.dumps(shares, indent=2)
        )]
    
    async def _handle_list_directory(self, arguments: dict) -> list[types.TextContent]:
        """Handle listing directory contents."""
        base_url = self._get_base_url(arguments)
        path = arguments["path"]
        
        filestation = self._get_filestation(base_url)
        files = filestation.list_directory(path)
        
        return [types.TextContent(
            type="text",
            text=json.dumps(files, indent=2)
        )]
    
    async def _handle_get_file_info(self, arguments: dict) -> list[types.TextContent]:
        """Handle getting file information."""
        base_url = self._get_base_url(arguments)
        path = arguments["path"]
        
        filestation = self._get_filestation(base_url)
        info = filestation.get_file_info(path)
        
        return [types.TextContent(
            type="text",
            text=json.dumps(info, indent=2)
        )]
    
    async def _handle_search_files(self, arguments: dict) -> list[types.TextContent]:
        """Handle searching files."""
        base_url = self._get_base_url(arguments)
        path = arguments["path"]
        pattern = arguments["pattern"]
        
        filestation = self._get_filestation(base_url)
        results = filestation.search_files(path, pattern)
        
        return [types.TextContent(
            type="text",
            text=json.dumps(results, indent=2)
        )]

    async def _handle_get_file_content(self, arguments: dict) -> list[types.TextContent]:
        """Handle getting file content."""
        base_url = self._get_base_url(arguments)
        path = arguments["path"]
        
        filestation = self._get_filestation(base_url)
        content = filestation.get_file_content(path)
        
        return [types.TextContent(
            type="text",
            text=content
        )]
    
    async def _handle_rename_file(self, arguments: dict) -> list[types.TextContent]:
        """Handle renaming a file or directory."""
        base_url = self._get_base_url(arguments)
        path = arguments["path"]
        new_name = arguments["new_name"]
        
        filestation = self._get_filestation(base_url)
        result = filestation.rename_file(path, new_name)
        
        return [types.TextContent(
            type="text",
            text=f"Rename result: {json.dumps(result, indent=2)}"
        )]
    
    async def _handle_move_file(self, arguments: dict) -> list[types.TextContent]:
        """Handle moving a file or directory."""
        base_url = self._get_base_url(arguments)
        source_path = arguments["source_path"]
        destination_path = arguments["destination_path"]
        overwrite = arguments.get("overwrite", False)  # Default to False if not provided
        
        filestation = self._get_filestation(base_url)
        result = filestation.move_file(source_path, destination_path, overwrite)
        
        return [types.TextContent(
            type="text",
            text=f"Move result: {json.dumps(result, indent=2)}"
        )]
    
    async def _handle_create_file(self, arguments: dict) -> list[types.TextContent]:
        """Handle creating a new file with specified content on the Synology NAS."""
        base_url = self._get_base_url(arguments)
        path = arguments["path"]
        content = arguments.get("content", "")
        overwrite = arguments.get("overwrite", False)
        
        filestation = self._get_filestation(base_url)
        result = filestation.create_file(path, content, overwrite)
        
        return [types.TextContent(
            type="text",
            text=f"Create file result: {json.dumps(result, indent=2)}"
        )]
    
    async def _handle_create_directory(self, arguments: dict) -> list[types.TextContent]:
        """Handle creating a new directory on the Synology NAS."""
        base_url = self._get_base_url(arguments)
        folder_path = arguments["folder_path"]
        name = arguments["name"]
        force_parent = arguments.get("force_parent", False)
        
        filestation = self._get_filestation(base_url)
        result = filestation.create_directory(folder_path, name, force_parent)
        
        return [types.TextContent(
            type="text",
            text=f"Create directory result: {json.dumps(result, indent=2)}"
        )]
    
    async def _handle_delete(self, arguments: dict) -> list[types.TextContent]:
        """Handle deleting a file or directory on the Synology NAS."""
        base_url = self._get_base_url(arguments)
        path = arguments["path"]
        
        filestation = self._get_filestation(base_url)
        result = filestation.delete(path)
        
        return [types.TextContent(
            type="text",
            text=f"Delete result: {json.dumps(result, indent=2)}"
        )]
    
    async def _handle_ds_get_info(self, arguments: dict) -> list[types.TextContent]:
        """Handle getting Download Station information and settings."""
        base_url = self._get_base_url(arguments)
        downloadstation = self._get_downloadstation(base_url)
        
        info = downloadstation.get_info()
        
        return [types.TextContent(
            type="text",
            text=json.dumps(info, indent=2)
        )]
    
    async def _handle_ds_list_tasks(self, arguments: dict) -> list[types.TextContent]:
        """Handle listing all download tasks in Download Station."""
        base_url = self._get_base_url(arguments)
        downloadstation = self._get_downloadstation(base_url)
        
        tasks = downloadstation.list_tasks()
        
        return [types.TextContent(
            type="text",
            text=json.dumps(tasks, indent=2)
        )]
    
    async def _handle_ds_create_task(self, arguments: dict) -> list[types.TextContent]:
        """Handle creating a new download task from URL or magnet link."""
        base_url = self._get_base_url(arguments)
        uri = arguments["uri"]
        destination = arguments.get("destination")
        username = arguments.get("username")
        password = arguments.get("password")
        
        downloadstation = self._get_downloadstation(base_url)
        result = downloadstation.create_task(uri, destination, username, password)
        
        return [types.TextContent(
            type="text",
            text=f"Create task result: {json.dumps(result, indent=2)}"
        )]
    
    async def _handle_ds_pause_tasks(self, arguments: dict) -> list[types.TextContent]:
        """Handle pausing one or more download tasks."""
        base_url = self._get_base_url(arguments)
        task_ids = arguments["task_ids"]
        
        downloadstation = self._get_downloadstation(base_url)
        result = downloadstation.pause_tasks(task_ids)
        
        return [types.TextContent(
            type="text",
            text=f"Pause tasks result: {json.dumps(result, indent=2)}"
        )]
    
    async def _handle_ds_resume_tasks(self, arguments: dict) -> list[types.TextContent]:
        """Handle resuming one or more paused download tasks."""
        base_url = self._get_base_url(arguments)
        task_ids = arguments["task_ids"]
        
        downloadstation = self._get_downloadstation(base_url)
        result = downloadstation.resume_tasks(task_ids)
        
        return [types.TextContent(
            type="text",
            text=f"Resume tasks result: {json.dumps(result, indent=2)}"
        )]
    
    async def _handle_ds_delete_tasks(self, arguments: dict) -> list[types.TextContent]:
        """Handle deleting one or more download tasks."""
        base_url = self._get_base_url(arguments)
        task_ids = arguments["task_ids"]
        force_complete = arguments.get("force_complete", False)
        
        downloadstation = self._get_downloadstation(base_url)
        result = downloadstation.delete_tasks(task_ids, force_complete)
        
        return [types.TextContent(
            type="text",
            text=f"Delete tasks result: {json.dumps(result, indent=2)}"
        )]
    
    async def _handle_ds_get_statistics(self, arguments: dict) -> list[types.TextContent]:
        """Handle getting Download Station download/upload statistics."""
        base_url = self._get_base_url(arguments)
        downloadstation = self._get_downloadstation(base_url)
        
        statistics = downloadstation.get_statistics()
        
        return [types.TextContent(
            type="text",
            text=json.dumps(statistics, indent=2)
        )]

    async def _handle_ds_list_downloaded_files(self, arguments: dict) -> list[types.TextContent]:
        """Handle listing files in the download destination."""
        base_url = self._get_base_url(arguments)
        destination = arguments.get("destination")
        downloadstation = self._get_downloadstation(base_url)

        files = downloadstation.list_downloaded_files(destination)

        return [types.TextContent(
            type="text",
            text=json.dumps(files, indent=2)
        )]

    # ==================== Docker/Container Manager Handlers ====================

    async def _handle_docker_list_containers(self, arguments: dict) -> list[types.TextContent]:
        """Handle listing Docker containers."""
        base_url = self._get_base_url(arguments)
        limit = arguments.get("limit", 50)
        offset = arguments.get("offset", 0)
        docker = self._get_docker(base_url)

        containers = docker.list_containers(limit=limit, offset=offset)

        return [types.TextContent(
            type="text",
            text=json.dumps(containers, indent=2)
        )]

    async def _handle_docker_get_container(self, arguments: dict) -> list[types.TextContent]:
        """Handle getting container details."""
        base_url = self._get_base_url(arguments)
        name = arguments["name"]
        docker = self._get_docker(base_url)

        container = docker.get_container(name)

        return [types.TextContent(
            type="text",
            text=json.dumps(container, indent=2)
        )]

    async def _handle_docker_start_container(self, arguments: dict) -> list[types.TextContent]:
        """Handle starting a container."""
        base_url = self._get_base_url(arguments)
        name = arguments["name"]
        docker = self._get_docker(base_url)

        result = docker.start_container(name)

        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    async def _handle_docker_stop_container(self, arguments: dict) -> list[types.TextContent]:
        """Handle stopping a container."""
        base_url = self._get_base_url(arguments)
        name = arguments["name"]
        docker = self._get_docker(base_url)

        result = docker.stop_container(name)

        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    async def _handle_docker_restart_container(self, arguments: dict) -> list[types.TextContent]:
        """Handle restarting a container."""
        base_url = self._get_base_url(arguments)
        name = arguments["name"]
        docker = self._get_docker(base_url)

        result = docker.restart_container(name)

        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    async def _handle_docker_delete_container(self, arguments: dict) -> list[types.TextContent]:
        """Handle deleting a container."""
        base_url = self._get_base_url(arguments)
        name = arguments["name"]
        force = arguments.get("force", False)
        docker = self._get_docker(base_url)

        result = docker.delete_container(name, force=force)

        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    async def _handle_docker_get_container_logs(self, arguments: dict) -> list[types.TextContent]:
        """Handle getting container logs."""
        base_url = self._get_base_url(arguments)
        name = arguments["name"]
        tail = arguments.get("tail", 100)
        docker = self._get_docker(base_url)

        result = docker.get_container_logs(name, tail=tail)

        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    async def _handle_docker_get_container_stats(self, arguments: dict) -> list[types.TextContent]:
        """Handle getting container stats."""
        base_url = self._get_base_url(arguments)
        name = arguments["name"]
        docker = self._get_docker(base_url)

        result = docker.get_container_stats(name)

        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    async def _handle_docker_list_images(self, arguments: dict) -> list[types.TextContent]:
        """Handle listing Docker images."""
        base_url = self._get_base_url(arguments)
        limit = arguments.get("limit", 50)
        offset = arguments.get("offset", 0)
        docker = self._get_docker(base_url)

        images = docker.list_images(limit=limit, offset=offset)

        return [types.TextContent(
            type="text",
            text=json.dumps(images, indent=2)
        )]

    async def _handle_docker_pull_image(self, arguments: dict) -> list[types.TextContent]:
        """Handle pulling a Docker image."""
        base_url = self._get_base_url(arguments)
        repository = arguments["repository"]
        tag = arguments.get("tag", "latest")
        docker = self._get_docker(base_url)

        result = docker.pull_image(repository, tag=tag)

        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    async def _handle_docker_delete_image(self, arguments: dict) -> list[types.TextContent]:
        """Handle deleting a Docker image."""
        base_url = self._get_base_url(arguments)
        image_id = arguments["image_id"]
        force = arguments.get("force", False)
        docker = self._get_docker(base_url)

        result = docker.delete_image(image_id, force=force)

        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    async def _handle_docker_list_projects(self, arguments: dict) -> list[types.TextContent]:
        """Handle listing Docker Compose projects."""
        base_url = self._get_base_url(arguments)
        docker = self._get_docker(base_url)

        projects = docker.list_projects()

        return [types.TextContent(
            type="text",
            text=json.dumps(projects, indent=2)
        )]

    async def _handle_docker_start_project(self, arguments: dict) -> list[types.TextContent]:
        """Handle starting a Docker Compose project."""
        base_url = self._get_base_url(arguments)
        project_id = arguments["project_id"]
        docker = self._get_docker(base_url)

        result = docker.start_project(project_id)

        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    async def _handle_docker_stop_project(self, arguments: dict) -> list[types.TextContent]:
        """Handle stopping a Docker Compose project."""
        base_url = self._get_base_url(arguments)
        project_id = arguments["project_id"]
        docker = self._get_docker(base_url)

        result = docker.stop_project(project_id)

        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    async def _handle_docker_list_networks(self, arguments: dict) -> list[types.TextContent]:
        """Handle listing Docker networks."""
        base_url = self._get_base_url(arguments)
        docker = self._get_docker(base_url)

        networks = docker.list_networks()

        return [types.TextContent(
            type="text",
            text=json.dumps(networks, indent=2)
        )]

    # ==================== Surveillance Station Handlers ====================

    async def _handle_surveillance_list_cameras(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        surveillance = self._get_surveillance(base_url)
        result = surveillance.list_cameras()
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_surveillance_get_camera(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        surveillance = self._get_surveillance(base_url)
        result = surveillance.get_camera_info(arguments["camera_id"])
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_surveillance_enable_camera(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        surveillance = self._get_surveillance(base_url)
        result = surveillance.enable_camera(arguments["camera_id"])
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_surveillance_disable_camera(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        surveillance = self._get_surveillance(base_url)
        result = surveillance.disable_camera(arguments["camera_id"])
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_surveillance_list_recordings(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        surveillance = self._get_surveillance(base_url)
        result = surveillance.list_recordings(arguments.get("camera_id"), arguments.get("limit", 50))
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_surveillance_take_snapshot(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        surveillance = self._get_surveillance(base_url)
        result = surveillance.take_snapshot(arguments["camera_id"])
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_surveillance_get_home_mode(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        surveillance = self._get_surveillance(base_url)
        result = surveillance.get_home_mode()
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_surveillance_set_home_mode(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        surveillance = self._get_surveillance(base_url)
        result = surveillance.set_home_mode(arguments["enabled"])
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    # ==================== Hyper Backup Handlers ====================

    async def _handle_backup_list_tasks(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        backup = self._get_hyperbackup(base_url)
        result = backup.list_tasks()
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_backup_get_task(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        backup = self._get_hyperbackup(base_url)
        result = backup.get_task_info(arguments["task_id"])
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_backup_start(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        backup = self._get_hyperbackup(base_url)
        result = backup.start_backup(arguments["task_id"])
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_backup_cancel(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        backup = self._get_hyperbackup(base_url)
        result = backup.cancel_backup(arguments["task_id"])
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_backup_list_versions(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        backup = self._get_hyperbackup(base_url)
        result = backup.list_versions(arguments["task_id"])
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_backup_get_stats(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        backup = self._get_hyperbackup(base_url)
        result = backup.get_backup_stats()
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    # ==================== VMM Handlers ====================

    async def _handle_vmm_list_guests(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        vmm = self._get_vmm(base_url)
        result = vmm.list_guests()
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_vmm_get_guest(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        vmm = self._get_vmm(base_url)
        result = vmm.get_guest_info(arguments["guest_id"])
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_vmm_start_guest(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        vmm = self._get_vmm(base_url)
        result = vmm.start_guest(arguments["guest_id"])
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_vmm_stop_guest(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        vmm = self._get_vmm(base_url)
        result = vmm.stop_guest(arguments["guest_id"], arguments.get("force", False))
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_vmm_restart_guest(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        vmm = self._get_vmm(base_url)
        result = vmm.restart_guest(arguments["guest_id"])
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_vmm_list_snapshots(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        vmm = self._get_vmm(base_url)
        result = vmm.list_snapshots(arguments["guest_id"])
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_vmm_create_snapshot(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        vmm = self._get_vmm(base_url)
        result = vmm.create_snapshot(arguments["guest_id"], arguments["name"], arguments.get("description", ""))
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_vmm_restore_snapshot(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        vmm = self._get_vmm(base_url)
        result = vmm.restore_snapshot(arguments["guest_id"], arguments["snapshot_id"])
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    # ==================== Drive Handlers ====================

    async def _handle_drive_list_connections(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        drive = self._get_drive(base_url)
        result = drive.list_connections()
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_drive_list_team_folders(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        drive = self._get_drive(base_url)
        result = drive.list_team_folders()
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_drive_list_share_links(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        drive = self._get_drive(base_url)
        result = drive.list_share_links(arguments.get("limit", 50))
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_drive_create_share_link(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        drive = self._get_drive(base_url)
        result = drive.create_share_link(arguments["path"], arguments.get("password"), arguments.get("expire_days"))
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_drive_get_sync_status(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        drive = self._get_drive(base_url)
        result = drive.get_sync_status()
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_drive_list_file_versions(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        drive = self._get_drive(base_url)
        result = drive.list_file_versions(arguments["path"])
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    # ==================== System Handlers ====================

    async def _handle_system_get_info(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        system = self._get_system(base_url)
        result = system.get_system_info()
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_system_get_utilization(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        system = self._get_system(base_url)
        result = system.get_utilization()
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_storage_list_volumes(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        system = self._get_system(base_url)
        result = system.list_volumes()
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_storage_list_disks(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        system = self._get_system(base_url)
        result = system.list_disks()
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_logs_get(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        system = self._get_system(base_url)
        result = system.get_logs(arguments.get("log_type", "general"), arguments.get("limit", 100))
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_logs_clear(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        system = self._get_system(base_url)
        result = system.clear_logs(arguments.get("log_type", "general"))
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_package_list(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        system = self._get_system(base_url)
        result = system.list_packages()
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_package_start(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        system = self._get_system(base_url)
        result = system.start_package(arguments["package_id"])
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_package_stop(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        system = self._get_system(base_url)
        result = system.stop_package(arguments["package_id"])
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_users_list(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        system = self._get_system(base_url)
        result = system.list_users()
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_users_get(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        system = self._get_system(base_url)
        result = system.get_user(arguments["username"])
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_groups_list(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        system = self._get_system(base_url)
        result = system.list_groups()
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_system_reboot(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        system = self._get_system(base_url)
        result = system.reboot()
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_system_shutdown(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        system = self._get_system(base_url)
        result = system.shutdown()
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    # ==================== Network Handlers ====================

    async def _handle_dns_list_zones(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        network = self._get_network(base_url)
        result = network.list_dns_zones()
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_dns_list_records(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        network = self._get_network(base_url)
        result = network.list_dns_records(arguments["zone_id"])
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_dns_create_record(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        network = self._get_network(base_url)
        result = network.create_dns_record(
            arguments["zone_id"], arguments["name"], arguments["record_type"],
            arguments["value"], arguments.get("ttl", 3600)
        )
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_dns_delete_record(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        network = self._get_network(base_url)
        result = network.delete_dns_record(arguments["zone_id"], arguments["record_id"])
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_dhcp_get_status(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        network = self._get_network(base_url)
        result = network.get_dhcp_status()
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_dhcp_list_leases(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        network = self._get_network(base_url)
        result = network.list_dhcp_leases()
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_dhcp_list_reservations(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        network = self._get_network(base_url)
        result = network.list_dhcp_reservations()
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_dhcp_create_reservation(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        network = self._get_network(base_url)
        result = network.create_dhcp_reservation(arguments["ip"], arguments["mac"], arguments.get("hostname", ""))
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_dhcp_delete_reservation(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        network = self._get_network(base_url)
        result = network.delete_dhcp_reservation(arguments["reservation_id"])
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_vpn_get_status(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        network = self._get_network(base_url)
        result = network.get_vpn_status()
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_vpn_list_connections(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        network = self._get_network(base_url)
        result = network.list_vpn_connections()
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_vpn_disconnect_client(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        network = self._get_network(base_url)
        result = network.disconnect_vpn_client(arguments["connection_id"])
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_vpn_list_users(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        network = self._get_network(base_url)
        result = network.list_vpn_users()
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _handle_network_get_info(self, arguments: dict) -> list[types.TextContent]:
        base_url = self._get_base_url(arguments)
        network = self._get_network(base_url)
        result = network.get_network_info()
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    def _get_tool_definitions(self):
        """Get tool definitions shared between MCP handler and bridge."""
        return [
            types.Tool(
                name="synology_status",
                description="Check authentication status for Synology NAS instances",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            types.Tool(
                name="list_shares",
                description="List all available shares on the Synology NAS",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_url": {
                            "type": "string",
                            "description": "Synology NAS base URL (optional if configured in .env)"
                        }
                    },
                    "required": []
                }
            ),
            types.Tool(
                name="list_directory",
                description="List contents of a directory on the Synology NAS. Returns detailed information about files and folders including name, type, size, and timestamps.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_url": {
                            "type": "string",
                            "description": "Synology NAS base URL (optional if configured in .env)"
                        },
                        "path": {
                            "type": "string",
                            "description": "Directory path to list (must start with /)"
                        }
                    },
                    "required": ["path"]
                }
            ),
            types.Tool(
                name="get_file_info",
                description="Get detailed information about a specific file or directory",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_url": {
                            "type": "string",
                            "description": "Synology NAS base URL (optional if configured in .env)"
                        },
                        "path": {
                            "type": "string",
                            "description": "File or directory path (must start with /)"
                        }
                    },
                    "required": ["path"]
                }
            ),
            types.Tool(
                name="search_files",
                description="Search for files and directories matching a pattern",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_url": {
                            "type": "string",
                            "description": "Synology NAS base URL (optional if configured in .env)"
                        },
                        "path": {
                            "type": "string",
                            "description": "Directory path to search in (must start with /)"
                        },
                        "pattern": {
                            "type": "string",
                            "description": "Search pattern (supports wildcards like *.txt)"
                        }
                    },
                    "required": ["path", "pattern"]
                }
            ),
            types.Tool(
                name="get_file_content",
                description="Get the content of a file",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_url": {
                            "type": "string",
                            "description": "Synology NAS base URL (optional if configured in .env)"
                        },
                        "path": {
                            "type": "string",
                            "description": "File path (must start with /)"
                        }
                    },
                    "required": ["path"]
                }
            ),
            types.Tool(
                name="rename_file",
                description="Rename a file or directory on the Synology NAS",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_url": {
                            "type": "string",
                            "description": "Synology NAS base URL (optional if configured in .env)"
                        },
                        "path": {
                            "type": "string",
                            "description": "Full path to the file/directory to rename (must start with /)"
                        },
                        "new_name": {
                            "type": "string",
                            "description": "New name for the file/directory (just the name, not full path)"
                        }
                    },
                    "required": ["path", "new_name"]
                }
            ),
            types.Tool(
                name="move_file",
                description="Move a file or directory to a new location on the Synology NAS",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_url": {
                            "type": "string",
                            "description": "Synology NAS base URL (optional if configured in .env)"
                        },
                        "source_path": {
                            "type": "string",
                            "description": "Full path to the file/directory to move (must start with /)"
                        },
                        "destination_path": {
                            "type": "string",
                            "description": "Destination path - can be a directory or full path with new name (must start with /)"
                        },
                        "overwrite": {
                            "type": "boolean",
                            "description": "Whether to overwrite existing files at destination (default: false)"
                        }
                    },
                    "required": ["source_path", "destination_path"]
                }
            ),
            types.Tool(
                name="create_file",
                description="Create a new file with specified content on the Synology NAS",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_url": {
                            "type": "string",
                            "description": "Synology NAS base URL (optional if configured in .env)"
                        },
                        "path": {
                            "type": "string",
                            "description": "Full path where the file should be created (must start with /)"
                        },
                        "content": {
                            "type": "string",
                            "description": "Content to write to the file (default: empty string)"
                        },
                        "overwrite": {
                            "type": "boolean",
                            "description": "Whether to overwrite existing file (default: false)"
                        }
                    },
                    "required": ["path"]
                }
            ),
            types.Tool(
                name="create_directory",
                description="Create a new directory on the Synology NAS",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_url": {
                            "type": "string",
                            "description": "Synology NAS base URL (optional if configured in .env)"
                        },
                        "folder_path": {
                            "type": "string",
                            "description": "Parent directory path where the new folder should be created (must start with /)"
                        },
                        "name": {
                            "type": "string",
                            "description": "Name of the new directory to create"
                        },
                        "force_parent": {
                            "type": "boolean",
                            "description": "Whether to create parent directories if they don't exist (default: false)"
                        }
                    },
                    "required": ["folder_path", "name"]
                }
            ),
            types.Tool(
                name="delete",
                description="Delete a file or directory on the Synology NAS (auto-detects type)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_url": {
                            "type": "string",
                            "description": "Synology NAS base URL (optional if configured in .env)"
                        },
                        "path": {
                            "type": "string",
                            "description": "Full path to the file/directory to delete (must start with /)"
                        }
                    },
                    "required": ["path"]
                }
            ),
            # Download Station Tools
            types.Tool(
                name="ds_get_info",
                description="Get Download Station information and settings",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_url": {
                            "type": "string",
                            "description": "Synology NAS base URL (optional if configured in .env)"
                        }
                    },
                    "required": []
                }
            ),
            types.Tool(
                name="ds_list_tasks",
                description="List all download tasks in Download Station",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_url": {
                            "type": "string",
                            "description": "Synology NAS base URL (optional if configured in .env)"
                        },
                        "offset": {
                            "type": "integer",
                            "description": "Starting offset for pagination (default: 0)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of tasks to return (default: -1 for all)"
                        }
                    },
                    "required": []
                }
            ),
            types.Tool(
                name="ds_create_task",
                description="Create a new download task from URL or magnet link",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_url": {
                            "type": "string",
                            "description": "Synology NAS base URL (optional if configured in .env)"
                        },
                        "uri": {
                            "type": "string",
                            "description": "Download URL or magnet link"
                        },
                        "destination": {
                            "type": "string",
                            "description": "Destination folder path (optional)"
                        },
                        "username": {
                            "type": "string",
                            "description": "Username for protected downloads (optional)"
                        },
                        "password": {
                            "type": "string",
                            "description": "Password for protected downloads (optional)"
                        }
                    },
                    "required": ["uri"]
                }
            ),
            types.Tool(
                name="ds_pause_tasks",
                description="Pause one or more download tasks",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_url": {
                            "type": "string",
                            "description": "Synology NAS base URL (optional if configured in .env)"
                        },
                        "task_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of task IDs to pause"
                        }
                    },
                    "required": ["task_ids"]
                }
            ),
            types.Tool(
                name="ds_resume_tasks",
                description="Resume one or more paused download tasks",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_url": {
                            "type": "string",
                            "description": "Synology NAS base URL (optional if configured in .env)"
                        },
                        "task_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of task IDs to resume"
                        }
                    },
                    "required": ["task_ids"]
                }
            ),
            types.Tool(
                name="ds_delete_tasks",
                description="Delete one or more download tasks",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_url": {
                            "type": "string",
                            "description": "Synology NAS base URL (optional if configured in .env)"
                        },
                        "task_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of task IDs to delete"
                        },
                        "force_complete": {
                            "type": "boolean",
                            "description": "Force delete completed tasks (default: false)"
                        }
                    },
                    "required": ["task_ids"]
                }
            ),
            types.Tool(
                name="ds_get_statistics",
                description="Get Download Station download/upload statistics",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_url": {
                            "type": "string",
                            "description": "Synology NAS base URL (optional if configured in .env)"
                        }
                    },
                    "required": []
                }
            ),
            types.Tool(
                name="ds_list_downloaded_files",
                description="List files in the Download Station destination folder",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_url": {
                            "type": "string",
                            "description": "Synology NAS base URL (optional if configured in .env)"
                        },
                        "destination": {
                            "type": "string",
                            "description": "Destination folder to list (optional, defaults to download station's default)"
                        }
                    },
                    "required": []
                }
            ),
            # Docker/Container Manager Tools
            types.Tool(
                name="docker_list_containers",
                description="List all Docker containers on the Synology NAS",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_url": {
                            "type": "string",
                            "description": "Synology NAS base URL (optional if configured in .env)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of containers to return (default: 50)"
                        },
                        "offset": {
                            "type": "integer",
                            "description": "Starting offset for pagination (default: 0)"
                        }
                    },
                    "required": []
                }
            ),
            types.Tool(
                name="docker_get_container",
                description="Get detailed information about a specific Docker container",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_url": {
                            "type": "string",
                            "description": "Synology NAS base URL (optional if configured in .env)"
                        },
                        "name": {
                            "type": "string",
                            "description": "Container name or ID"
                        }
                    },
                    "required": ["name"]
                }
            ),
            types.Tool(
                name="docker_start_container",
                description="Start a stopped Docker container",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_url": {
                            "type": "string",
                            "description": "Synology NAS base URL (optional if configured in .env)"
                        },
                        "name": {
                            "type": "string",
                            "description": "Container name or ID to start"
                        }
                    },
                    "required": ["name"]
                }
            ),
            types.Tool(
                name="docker_stop_container",
                description="Stop a running Docker container",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_url": {
                            "type": "string",
                            "description": "Synology NAS base URL (optional if configured in .env)"
                        },
                        "name": {
                            "type": "string",
                            "description": "Container name or ID to stop"
                        }
                    },
                    "required": ["name"]
                }
            ),
            types.Tool(
                name="docker_restart_container",
                description="Restart a Docker container",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_url": {
                            "type": "string",
                            "description": "Synology NAS base URL (optional if configured in .env)"
                        },
                        "name": {
                            "type": "string",
                            "description": "Container name or ID to restart"
                        }
                    },
                    "required": ["name"]
                }
            ),
            types.Tool(
                name="docker_delete_container",
                description="Delete a Docker container",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_url": {
                            "type": "string",
                            "description": "Synology NAS base URL (optional if configured in .env)"
                        },
                        "name": {
                            "type": "string",
                            "description": "Container name or ID to delete"
                        },
                        "force": {
                            "type": "boolean",
                            "description": "Force delete even if container is running (default: false)"
                        }
                    },
                    "required": ["name"]
                }
            ),
            types.Tool(
                name="docker_get_container_logs",
                description="Get logs from a Docker container",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_url": {
                            "type": "string",
                            "description": "Synology NAS base URL (optional if configured in .env)"
                        },
                        "name": {
                            "type": "string",
                            "description": "Container name or ID"
                        },
                        "tail": {
                            "type": "integer",
                            "description": "Number of log lines to retrieve (default: 100)"
                        }
                    },
                    "required": ["name"]
                }
            ),
            types.Tool(
                name="docker_get_container_stats",
                description="Get resource usage statistics for a Docker container (CPU, memory, network)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_url": {
                            "type": "string",
                            "description": "Synology NAS base URL (optional if configured in .env)"
                        },
                        "name": {
                            "type": "string",
                            "description": "Container name or ID"
                        }
                    },
                    "required": ["name"]
                }
            ),
            types.Tool(
                name="docker_list_images",
                description="List all Docker images on the Synology NAS",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_url": {
                            "type": "string",
                            "description": "Synology NAS base URL (optional if configured in .env)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of images to return (default: 50)"
                        },
                        "offset": {
                            "type": "integer",
                            "description": "Starting offset for pagination (default: 0)"
                        }
                    },
                    "required": []
                }
            ),
            types.Tool(
                name="docker_pull_image",
                description="Pull a Docker image from a registry",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_url": {
                            "type": "string",
                            "description": "Synology NAS base URL (optional if configured in .env)"
                        },
                        "repository": {
                            "type": "string",
                            "description": "Image repository (e.g., 'nginx', 'library/ubuntu', 'ghcr.io/owner/image')"
                        },
                        "tag": {
                            "type": "string",
                            "description": "Image tag (default: 'latest')"
                        }
                    },
                    "required": ["repository"]
                }
            ),
            types.Tool(
                name="docker_delete_image",
                description="Delete a Docker image",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_url": {
                            "type": "string",
                            "description": "Synology NAS base URL (optional if configured in .env)"
                        },
                        "image_id": {
                            "type": "string",
                            "description": "Image ID or name:tag to delete"
                        },
                        "force": {
                            "type": "boolean",
                            "description": "Force delete even if image is in use (default: false)"
                        }
                    },
                    "required": ["image_id"]
                }
            ),
            types.Tool(
                name="docker_list_projects",
                description="List all Docker Compose projects",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_url": {
                            "type": "string",
                            "description": "Synology NAS base URL (optional if configured in .env)"
                        }
                    },
                    "required": []
                }
            ),
            types.Tool(
                name="docker_start_project",
                description="Start a Docker Compose project (all its containers)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_url": {
                            "type": "string",
                            "description": "Synology NAS base URL (optional if configured in .env)"
                        },
                        "project_id": {
                            "type": "string",
                            "description": "Project ID (UUID) to start"
                        }
                    },
                    "required": ["project_id"]
                }
            ),
            types.Tool(
                name="docker_stop_project",
                description="Stop a Docker Compose project (all its containers)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_url": {
                            "type": "string",
                            "description": "Synology NAS base URL (optional if configured in .env)"
                        },
                        "project_id": {
                            "type": "string",
                            "description": "Project ID (UUID) to stop"
                        }
                    },
                    "required": ["project_id"]
                }
            ),
            types.Tool(
                name="docker_list_networks",
                description="List all Docker networks",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_url": {
                            "type": "string",
                            "description": "Synology NAS base URL (optional if configured in .env)"
                        }
                    },
                    "required": []
                }
            )
        ] + get_extended_tool_definitions()

    async def get_tools_list(self):
        """Get the list of available tools (for bridge use)."""
        return self._get_tool_definitions()

    async def call_tool_direct(self, name: str, arguments: dict):
        """Call a tool directly (for bridge use)."""
        # This replicates the logic from the handle_call_tool function
        # but can be called directly from the bridge
        try:
            if name == "synology_login":
                return await self._handle_login(arguments)
            elif name == "synology_logout":
                return await self._handle_logout(arguments)
            elif name == "synology_status":
                return await self._handle_status(arguments)
            elif name == "list_shares":
                return await self._handle_list_shares(arguments)
            elif name == "list_directory":
                return await self._handle_list_directory(arguments)
            elif name == "get_file_info":
                return await self._handle_get_file_info(arguments)
            elif name == "search_files":
                return await self._handle_search_files(arguments)
            elif name == "get_file_content":
                return await self._handle_get_file_content(arguments)
            elif name == "rename_file":
                return await self._handle_rename_file(arguments)
            elif name == "move_file":
                return await self._handle_move_file(arguments)
            elif name == "create_file":
                return await self._handle_create_file(arguments)
            elif name == "create_directory":
                return await self._handle_create_directory(arguments)
            elif name == "delete":
                return await self._handle_delete(arguments)
            # Download Station handlers
            elif name == "ds_get_info":
                return await self._handle_ds_get_info(arguments)
            elif name == "ds_list_tasks":
                return await self._handle_ds_list_tasks(arguments)
            elif name == "ds_create_task":
                return await self._handle_ds_create_task(arguments)
            elif name == "ds_pause_tasks":
                return await self._handle_ds_pause_tasks(arguments)
            elif name == "ds_resume_tasks":
                return await self._handle_ds_resume_tasks(arguments)
            elif name == "ds_delete_tasks":
                return await self._handle_ds_delete_tasks(arguments)
            elif name == "ds_get_statistics":
                return await self._handle_ds_get_statistics(arguments)
            elif name == "ds_list_downloaded_files":
                return await self._handle_ds_list_downloaded_files(arguments)
            # Docker/Container Manager handlers
            elif name == "docker_list_containers":
                return await self._handle_docker_list_containers(arguments)
            elif name == "docker_get_container":
                return await self._handle_docker_get_container(arguments)
            elif name == "docker_start_container":
                return await self._handle_docker_start_container(arguments)
            elif name == "docker_stop_container":
                return await self._handle_docker_stop_container(arguments)
            elif name == "docker_restart_container":
                return await self._handle_docker_restart_container(arguments)
            elif name == "docker_delete_container":
                return await self._handle_docker_delete_container(arguments)
            elif name == "docker_get_container_logs":
                return await self._handle_docker_get_container_logs(arguments)
            elif name == "docker_get_container_stats":
                return await self._handle_docker_get_container_stats(arguments)
            elif name == "docker_list_images":
                return await self._handle_docker_list_images(arguments)
            elif name == "docker_pull_image":
                return await self._handle_docker_pull_image(arguments)
            elif name == "docker_delete_image":
                return await self._handle_docker_delete_image(arguments)
            elif name == "docker_list_projects":
                return await self._handle_docker_list_projects(arguments)
            elif name == "docker_start_project":
                return await self._handle_docker_start_project(arguments)
            elif name == "docker_stop_project":
                return await self._handle_docker_stop_project(arguments)
            elif name == "docker_list_networks":
                return await self._handle_docker_list_networks(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error executing {name}: {str(e)}"
            )]

    async def run(self):
        """Run the MCP server."""
        # Validate configuration first
        config_errors = config.validate_config()
        if config_errors and config.auto_login:
            error_msg = f"Configuration errors: {', '.join(config_errors)}"
            print(f"❌ {error_msg}", file=sys.stderr)
            raise Exception(f"Invalid configuration - stopping server. {error_msg}")
        elif config.debug:
            print(f"Configuration loaded: {config}", file=sys.stderr)
        
        # Attempt auto-login if configured (this will raise exception on failure and stop server)
        print("Attempting auto-login...", file=sys.stderr)
        await self._auto_login_if_configured()
        
        # Only start server if auto-login succeeded (or wasn't required)
        try:
            print("Starting MCP server on stdio...", file=sys.stderr)
            async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name=config.server_name,
                        server_version=config.server_version,
                        capabilities=self.server.get_capabilities(
                            notification_options=NotificationOptions(),
                            experimental_capabilities={},
                        ),
                    ),
                )
        except KeyboardInterrupt:
            print("\n🔄 Received shutdown signal, cleaning up sessions...", file=sys.stderr)
        except Exception as e:
            print(f"❌ Server runtime error: {e}", file=sys.stderr)
            if config.debug:
                import traceback
                traceback.print_exc(file=sys.stderr)
            raise
        finally:
            # Always attempt session cleanup on shutdown
            if self.sessions:
                print("🧹 Cleaning up active sessions...", file=sys.stderr)
                cleanup_results = await self.cleanup_sessions()
                
                if cleanup_results:
                    print("📋 Session cleanup summary:", file=sys.stderr)
                    for result in cleanup_results:
                        print(f"  {result}", file=sys.stderr)
                
                print("✅ Session cleanup completed", file=sys.stderr)
            else:
                print("✅ No active sessions to clean up", file=sys.stderr)

    async def cleanup_sessions(self):
        """Clean up all active sessions during shutdown."""
        cleanup_results = []
        
        for base_url, session_id in list(self.sessions.items()):
            try:
                auth = self.auth_instances.get(base_url)
                if auth:
                    print(f"🔄 Cleaning up session for {base_url}...", file=sys.stderr)
                    result = auth.logout(session_id)
                    
                    if result.get('success'):
                        print(f"✅ Session {session_id[:10]}... logged out successfully", file=sys.stderr)
                        cleanup_results.append(f"✅ {base_url}: Logged out successfully")
                    else:
                        error_info = result.get('error', {})
                        error_code = error_info.get('code', 'unknown')
                        
                        if error_code in ['105', '106', 'no_session']:
                            print(f"⚠️ Session {session_id[:10]}... was already expired", file=sys.stderr)
                            cleanup_results.append(f"⚠️ {base_url}: Session already expired")
                        else:
                            print(f"❌ Failed to logout {session_id[:10]}...: {error_code}", file=sys.stderr)
                            cleanup_results.append(f"❌ {base_url}: Logout failed - {error_code}")
                
                # Always clear local data
                del self.sessions[base_url]
                if base_url in self.filestation_instances:
                    del self.filestation_instances[base_url]
                if base_url in self.downloadstation_instances:
                    del self.downloadstation_instances[base_url]
                if base_url in self.docker_instances:
                    del self.docker_instances[base_url]

            except Exception as e:
                print(f"❌ Exception during cleanup for {base_url}: {e}", file=sys.stderr)
                cleanup_results.append(f"❌ {base_url}: Exception - {str(e)}")

        return cleanup_results


async def main():
    """Main entry point."""
    server = SynologyMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main()) 