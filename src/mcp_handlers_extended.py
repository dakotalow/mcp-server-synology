# Extended MCP handlers for additional Synology services
# This file contains handler methods and tool definitions for:
# - Surveillance Station
# - Hyper Backup
# - Virtual Machine Manager
# - Synology Drive
# - System Management (Resource Monitor, Storage, Logs, Packages, Users)
# - Network Services (DNS, DHCP, VPN)

import json
import mcp.types as types
from typing import List


def get_extended_tool_definitions() -> List[types.Tool]:
    """Get tool definitions for extended Synology services."""
    return [
        # ==================== Surveillance Station ====================
        types.Tool(
            name="surveillance_list_cameras",
            description="List all cameras in Surveillance Station",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"}
                },
                "required": []
            }
        ),
        types.Tool(
            name="surveillance_get_camera",
            description="Get detailed info for a specific camera",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"},
                    "camera_id": {"type": "integer", "description": "Camera ID"}
                },
                "required": ["camera_id"]
            }
        ),
        types.Tool(
            name="surveillance_enable_camera",
            description="Enable a camera",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"},
                    "camera_id": {"type": "integer", "description": "Camera ID to enable"}
                },
                "required": ["camera_id"]
            }
        ),
        types.Tool(
            name="surveillance_disable_camera",
            description="Disable a camera",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"},
                    "camera_id": {"type": "integer", "description": "Camera ID to disable"}
                },
                "required": ["camera_id"]
            }
        ),
        types.Tool(
            name="surveillance_list_recordings",
            description="List recordings from Surveillance Station",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"},
                    "camera_id": {"type": "integer", "description": "Filter by camera ID (optional)"},
                    "limit": {"type": "integer", "description": "Max recordings to return (default: 50)"}
                },
                "required": []
            }
        ),
        types.Tool(
            name="surveillance_take_snapshot",
            description="Take a snapshot from a camera",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"},
                    "camera_id": {"type": "integer", "description": "Camera ID"}
                },
                "required": ["camera_id"]
            }
        ),
        types.Tool(
            name="surveillance_get_home_mode",
            description="Get Surveillance Station home mode status",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"}
                },
                "required": []
            }
        ),
        types.Tool(
            name="surveillance_set_home_mode",
            description="Enable or disable home mode",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"},
                    "enabled": {"type": "boolean", "description": "True to enable, False to disable"}
                },
                "required": ["enabled"]
            }
        ),

        # ==================== Hyper Backup ====================
        types.Tool(
            name="backup_list_tasks",
            description="List all Hyper Backup tasks",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"}
                },
                "required": []
            }
        ),
        types.Tool(
            name="backup_get_task",
            description="Get details for a specific backup task",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"},
                    "task_id": {"type": "integer", "description": "Backup task ID"}
                },
                "required": ["task_id"]
            }
        ),
        types.Tool(
            name="backup_start",
            description="Start a backup task",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"},
                    "task_id": {"type": "integer", "description": "Backup task ID to start"}
                },
                "required": ["task_id"]
            }
        ),
        types.Tool(
            name="backup_cancel",
            description="Cancel a running backup task",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"},
                    "task_id": {"type": "integer", "description": "Backup task ID to cancel"}
                },
                "required": ["task_id"]
            }
        ),
        types.Tool(
            name="backup_list_versions",
            description="List backup versions for a task",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"},
                    "task_id": {"type": "integer", "description": "Backup task ID"}
                },
                "required": ["task_id"]
            }
        ),
        types.Tool(
            name="backup_get_stats",
            description="Get overall backup statistics",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"}
                },
                "required": []
            }
        ),

        # ==================== Virtual Machine Manager ====================
        types.Tool(
            name="vmm_list_guests",
            description="List all virtual machines",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"}
                },
                "required": []
            }
        ),
        types.Tool(
            name="vmm_get_guest",
            description="Get details for a specific VM",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"},
                    "guest_id": {"type": "string", "description": "VM guest ID"}
                },
                "required": ["guest_id"]
            }
        ),
        types.Tool(
            name="vmm_start_guest",
            description="Start a virtual machine",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"},
                    "guest_id": {"type": "string", "description": "VM guest ID to start"}
                },
                "required": ["guest_id"]
            }
        ),
        types.Tool(
            name="vmm_stop_guest",
            description="Stop a virtual machine",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"},
                    "guest_id": {"type": "string", "description": "VM guest ID to stop"},
                    "force": {"type": "boolean", "description": "Force power off (default: false, graceful shutdown)"}
                },
                "required": ["guest_id"]
            }
        ),
        types.Tool(
            name="vmm_restart_guest",
            description="Restart a virtual machine",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"},
                    "guest_id": {"type": "string", "description": "VM guest ID to restart"}
                },
                "required": ["guest_id"]
            }
        ),
        types.Tool(
            name="vmm_list_snapshots",
            description="List snapshots for a VM",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"},
                    "guest_id": {"type": "string", "description": "VM guest ID"}
                },
                "required": ["guest_id"]
            }
        ),
        types.Tool(
            name="vmm_create_snapshot",
            description="Create a VM snapshot",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"},
                    "guest_id": {"type": "string", "description": "VM guest ID"},
                    "name": {"type": "string", "description": "Snapshot name"},
                    "description": {"type": "string", "description": "Snapshot description (optional)"}
                },
                "required": ["guest_id", "name"]
            }
        ),
        types.Tool(
            name="vmm_restore_snapshot",
            description="Restore a VM to a snapshot",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"},
                    "guest_id": {"type": "string", "description": "VM guest ID"},
                    "snapshot_id": {"type": "string", "description": "Snapshot ID to restore"}
                },
                "required": ["guest_id", "snapshot_id"]
            }
        ),

        # ==================== Synology Drive ====================
        types.Tool(
            name="drive_list_connections",
            description="List all connected Drive clients",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"}
                },
                "required": []
            }
        ),
        types.Tool(
            name="drive_list_team_folders",
            description="List all team folders",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"}
                },
                "required": []
            }
        ),
        types.Tool(
            name="drive_list_share_links",
            description="List all share links",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"},
                    "limit": {"type": "integer", "description": "Max links to return (default: 50)"}
                },
                "required": []
            }
        ),
        types.Tool(
            name="drive_create_share_link",
            description="Create a share link for a file or folder",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"},
                    "path": {"type": "string", "description": "Path to file or folder"},
                    "password": {"type": "string", "description": "Optional password protection"},
                    "expire_days": {"type": "integer", "description": "Days until link expires (optional)"}
                },
                "required": ["path"]
            }
        ),
        types.Tool(
            name="drive_get_sync_status",
            description="Get Drive sync status",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"}
                },
                "required": []
            }
        ),
        types.Tool(
            name="drive_list_file_versions",
            description="List version history for a file",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"},
                    "path": {"type": "string", "description": "File path"}
                },
                "required": ["path"]
            }
        ),

        # ==================== System - Resource Monitor ====================
        types.Tool(
            name="system_get_info",
            description="Get NAS system information (model, firmware, uptime, etc.)",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"}
                },
                "required": []
            }
        ),
        types.Tool(
            name="system_get_utilization",
            description="Get current CPU, memory, network, and disk utilization",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"}
                },
                "required": []
            }
        ),

        # ==================== System - Storage Manager ====================
        types.Tool(
            name="storage_list_volumes",
            description="List all storage volumes",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"}
                },
                "required": []
            }
        ),
        types.Tool(
            name="storage_list_disks",
            description="List all physical disks",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"}
                },
                "required": []
            }
        ),

        # ==================== System - Log Center ====================
        types.Tool(
            name="logs_get",
            description="Get system logs",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"},
                    "log_type": {"type": "string", "description": "Log type: general, connection, file_transfer (default: general)"},
                    "limit": {"type": "integer", "description": "Max log entries (default: 100)"}
                },
                "required": []
            }
        ),
        types.Tool(
            name="logs_clear",
            description="Clear system logs",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"},
                    "log_type": {"type": "string", "description": "Log type to clear (default: general)"}
                },
                "required": []
            }
        ),

        # ==================== System - Package Center ====================
        types.Tool(
            name="package_list",
            description="List installed packages",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"}
                },
                "required": []
            }
        ),
        types.Tool(
            name="package_start",
            description="Start a package/service",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"},
                    "package_id": {"type": "string", "description": "Package ID to start"}
                },
                "required": ["package_id"]
            }
        ),
        types.Tool(
            name="package_stop",
            description="Stop a package/service",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"},
                    "package_id": {"type": "string", "description": "Package ID to stop"}
                },
                "required": ["package_id"]
            }
        ),

        # ==================== System - Users & Groups ====================
        types.Tool(
            name="users_list",
            description="List all users",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"}
                },
                "required": []
            }
        ),
        types.Tool(
            name="users_get",
            description="Get details for a specific user",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"},
                    "username": {"type": "string", "description": "Username"}
                },
                "required": ["username"]
            }
        ),
        types.Tool(
            name="groups_list",
            description="List all groups",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"}
                },
                "required": []
            }
        ),

        # ==================== System - Power ====================
        types.Tool(
            name="system_reboot",
            description="Reboot the NAS (use with caution!)",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"}
                },
                "required": []
            }
        ),
        types.Tool(
            name="system_shutdown",
            description="Shutdown the NAS (use with caution!)",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"}
                },
                "required": []
            }
        ),

        # ==================== Network - DNS Server ====================
        types.Tool(
            name="dns_list_zones",
            description="List all DNS zones",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"}
                },
                "required": []
            }
        ),
        types.Tool(
            name="dns_list_records",
            description="List DNS records for a zone",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"},
                    "zone_id": {"type": "string", "description": "DNS zone ID"}
                },
                "required": ["zone_id"]
            }
        ),
        types.Tool(
            name="dns_create_record",
            description="Create a DNS record",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"},
                    "zone_id": {"type": "string", "description": "DNS zone ID"},
                    "name": {"type": "string", "description": "Record name"},
                    "record_type": {"type": "string", "description": "Record type (A, AAAA, CNAME, MX, TXT, etc.)"},
                    "value": {"type": "string", "description": "Record value"},
                    "ttl": {"type": "integer", "description": "TTL in seconds (default: 3600)"}
                },
                "required": ["zone_id", "name", "record_type", "value"]
            }
        ),
        types.Tool(
            name="dns_delete_record",
            description="Delete a DNS record",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"},
                    "zone_id": {"type": "string", "description": "DNS zone ID"},
                    "record_id": {"type": "string", "description": "Record ID to delete"}
                },
                "required": ["zone_id", "record_id"]
            }
        ),

        # ==================== Network - DHCP Server ====================
        types.Tool(
            name="dhcp_get_status",
            description="Get DHCP server status",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"}
                },
                "required": []
            }
        ),
        types.Tool(
            name="dhcp_list_leases",
            description="List all DHCP leases",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"}
                },
                "required": []
            }
        ),
        types.Tool(
            name="dhcp_list_reservations",
            description="List all DHCP reservations (static leases)",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"}
                },
                "required": []
            }
        ),
        types.Tool(
            name="dhcp_create_reservation",
            description="Create a DHCP reservation (static lease)",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"},
                    "ip": {"type": "string", "description": "IP address to reserve"},
                    "mac": {"type": "string", "description": "MAC address"},
                    "hostname": {"type": "string", "description": "Hostname (optional)"}
                },
                "required": ["ip", "mac"]
            }
        ),
        types.Tool(
            name="dhcp_delete_reservation",
            description="Delete a DHCP reservation",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"},
                    "reservation_id": {"type": "string", "description": "Reservation ID to delete"}
                },
                "required": ["reservation_id"]
            }
        ),

        # ==================== Network - VPN Server ====================
        types.Tool(
            name="vpn_get_status",
            description="Get VPN server status",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"}
                },
                "required": []
            }
        ),
        types.Tool(
            name="vpn_list_connections",
            description="List active VPN connections",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"}
                },
                "required": []
            }
        ),
        types.Tool(
            name="vpn_disconnect_client",
            description="Disconnect a VPN client",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"},
                    "connection_id": {"type": "string", "description": "Connection ID to disconnect"}
                },
                "required": ["connection_id"]
            }
        ),
        types.Tool(
            name="vpn_list_users",
            description="List VPN users and their permissions",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"}
                },
                "required": []
            }
        ),

        # ==================== Network - General ====================
        types.Tool(
            name="network_get_info",
            description="Get network interface information",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {"type": "string", "description": "Synology NAS base URL (optional)"}
                },
                "required": []
            }
        ),
    ]
