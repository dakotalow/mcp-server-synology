# Network Services module for DSM 7.0+
# Includes: DNS Server, DHCP Server, VPN Server

import requests
import json
from typing import Dict, List, Any, Optional
import sys


class SynologyNetwork:
    """Handles Synology Network Services API operations."""

    def __init__(self, base_url: str, session_id: str, verify_ssl: bool = False):
        self.base_url = base_url.rstrip('/')
        self.session_id = session_id
        self.api_url = f"{self.base_url}/webapi/entry.cgi"
        self.verify_ssl = verify_ssl

        # API definitions
        # DNS Server
        self.dns_zone_api = "SYNO.DNSServer.Zone"
        self.dns_record_api = "SYNO.DNSServer.Record"

        # DHCP Server
        self.dhcp_server_api = "SYNO.DHCPServer.Server"
        self.dhcp_lease_api = "SYNO.DHCPServer.Lease"
        self.dhcp_reservation_api = "SYNO.DHCPServer.Reservation"

        # VPN Server
        self.vpn_settings_api = "SYNO.VPNServer.Settings"
        self.vpn_connection_api = "SYNO.VPNServer.Connection"
        self.vpn_user_api = "SYNO.VPNServer.User"

        # Network config
        self.network_api = "SYNO.Core.Network"

    def _make_request(self, api: str, version: str, method: str, use_post: bool = False, **params) -> Dict[str, Any]:
        """Make a request to Network Services API."""
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
                raise Exception(f"Network Services API error {error_code}")

            return data.get('data', {})

        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {e}")

    # ==================== Network Information ====================

    def get_network_info(self) -> Dict[str, Any]:
        """Get network interface information."""
        try:
            data = self._make_request(self.network_api, "1", "list")
            interfaces = []
            for iface in data.get('interfaces', []):
                interfaces.append({
                    'id': iface.get('id'),
                    'name': iface.get('name'),
                    'type': iface.get('type'),
                    'ip': iface.get('ip'),
                    'netmask': iface.get('mask'),
                    'gateway': iface.get('gateway'),
                    'mac': iface.get('mac'),
                    'status': iface.get('status')
                })
            return {'interfaces': interfaces}
        except Exception as e:
            raise Exception(f"Failed to get network info: {e}")

    # ==================== DNS Server ====================

    def list_dns_zones(self) -> Dict[str, Any]:
        """List all DNS zones."""
        try:
            data = self._make_request(self.dns_zone_api, "1", "list")
            zones = []
            for zone in data.get('zones', []):
                zones.append({
                    'id': zone.get('zone_id'),
                    'name': zone.get('domain'),
                    'type': zone.get('zone_type'),
                    'serial': zone.get('serial'),
                    'ttl': zone.get('ttl')
                })
            return {'total': len(zones), 'zones': zones}
        except Exception as e:
            raise Exception(f"Failed to list DNS zones: {e}")

    def list_dns_records(self, zone_id: str) -> Dict[str, Any]:
        """List DNS records for a zone."""
        try:
            data = self._make_request(self.dns_record_api, "1", "list", zone_id=zone_id)
            records = []
            for rec in data.get('records', []):
                records.append({
                    'id': rec.get('record_id'),
                    'name': rec.get('name'),
                    'type': rec.get('type'),
                    'value': rec.get('rdata'),
                    'ttl': rec.get('ttl')
                })
            return {'zone_id': zone_id, 'total': len(records), 'records': records}
        except Exception as e:
            raise Exception(f"Failed to list DNS records: {e}")

    def create_dns_record(self, zone_id: str, name: str, record_type: str, value: str, ttl: int = 3600) -> Dict[str, Any]:
        """Create a DNS record."""
        print(f"📝 Creating DNS record {name} ({record_type}) = {value}", file=sys.stderr)
        self._make_request(
            self.dns_record_api, "1", "create",
            use_post=True,
            zone_id=zone_id,
            name=name,
            type=record_type,
            rdata=value,
            ttl=ttl
        )
        return {'success': True, 'name': name, 'type': record_type, 'value': value, 'action': 'created'}

    def delete_dns_record(self, zone_id: str, record_id: str) -> Dict[str, Any]:
        """Delete a DNS record."""
        print(f"🗑️ Deleting DNS record {record_id}", file=sys.stderr)
        self._make_request(
            self.dns_record_api, "1", "delete",
            use_post=True,
            zone_id=zone_id,
            record_id=record_id
        )
        return {'success': True, 'zone_id': zone_id, 'record_id': record_id, 'action': 'deleted'}

    # ==================== DHCP Server ====================

    def get_dhcp_status(self) -> Dict[str, Any]:
        """Get DHCP server status."""
        try:
            data = self._make_request(self.dhcp_server_api, "1", "get")
            return data
        except Exception as e:
            raise Exception(f"Failed to get DHCP status: {e}")

    def list_dhcp_leases(self) -> Dict[str, Any]:
        """List all DHCP leases."""
        try:
            data = self._make_request(self.dhcp_lease_api, "1", "list")
            leases = []
            for lease in data.get('leases', []):
                leases.append({
                    'ip': lease.get('ip'),
                    'mac': lease.get('mac'),
                    'hostname': lease.get('hostname'),
                    'expire_time': lease.get('expire'),
                    'interface': lease.get('interface')
                })
            return {'total': len(leases), 'leases': leases}
        except Exception as e:
            raise Exception(f"Failed to list DHCP leases: {e}")

    def list_dhcp_reservations(self) -> Dict[str, Any]:
        """List all DHCP reservations (static leases)."""
        try:
            data = self._make_request(self.dhcp_reservation_api, "1", "list")
            reservations = []
            for res in data.get('reservations', []):
                reservations.append({
                    'id': res.get('id'),
                    'ip': res.get('ip'),
                    'mac': res.get('mac'),
                    'hostname': res.get('hostname'),
                    'enabled': res.get('enabled')
                })
            return {'total': len(reservations), 'reservations': reservations}
        except Exception as e:
            raise Exception(f"Failed to list DHCP reservations: {e}")

    def create_dhcp_reservation(self, ip: str, mac: str, hostname: str = "") -> Dict[str, Any]:
        """Create a DHCP reservation (static lease)."""
        print(f"📝 Creating DHCP reservation {ip} -> {mac}", file=sys.stderr)
        self._make_request(
            self.dhcp_reservation_api, "1", "create",
            use_post=True,
            ip=ip,
            mac=mac,
            hostname=hostname
        )
        return {'success': True, 'ip': ip, 'mac': mac, 'hostname': hostname, 'action': 'created'}

    def delete_dhcp_reservation(self, reservation_id: str) -> Dict[str, Any]:
        """Delete a DHCP reservation."""
        print(f"🗑️ Deleting DHCP reservation {reservation_id}", file=sys.stderr)
        self._make_request(
            self.dhcp_reservation_api, "1", "delete",
            use_post=True,
            id=reservation_id
        )
        return {'success': True, 'reservation_id': reservation_id, 'action': 'deleted'}

    # ==================== VPN Server ====================

    def get_vpn_status(self) -> Dict[str, Any]:
        """Get VPN server status."""
        try:
            data = self._make_request(self.vpn_settings_api, "1", "get")
            return {
                'enabled': data.get('enabled', False),
                'pptp_enabled': data.get('pptp_enable', False),
                'openvpn_enabled': data.get('openvpn_enable', False),
                'l2tp_enabled': data.get('l2tp_enable', False)
            }
        except Exception as e:
            raise Exception(f"Failed to get VPN status: {e}")

    def list_vpn_connections(self) -> Dict[str, Any]:
        """List active VPN connections."""
        try:
            data = self._make_request(self.vpn_connection_api, "1", "list")
            connections = []
            for conn in data.get('connections', []):
                connections.append({
                    'id': conn.get('id'),
                    'username': conn.get('user'),
                    'protocol': conn.get('protocol'),
                    'ip_address': conn.get('ip'),
                    'client_ip': conn.get('client_ip'),
                    'connected_time': conn.get('connected_time'),
                    'bytes_in': conn.get('bytes_in'),
                    'bytes_out': conn.get('bytes_out')
                })
            return {'total': len(connections), 'connections': connections}
        except Exception as e:
            raise Exception(f"Failed to list VPN connections: {e}")

    def disconnect_vpn_client(self, connection_id: str) -> Dict[str, Any]:
        """Disconnect a VPN client."""
        print(f"🔌 Disconnecting VPN client {connection_id}", file=sys.stderr)
        self._make_request(
            self.vpn_connection_api, "1", "disconnect",
            use_post=True,
            id=connection_id
        )
        return {'success': True, 'connection_id': connection_id, 'action': 'disconnected'}

    def list_vpn_users(self) -> Dict[str, Any]:
        """List VPN users/permissions."""
        try:
            data = self._make_request(self.vpn_user_api, "1", "list")
            users = []
            for user in data.get('users', []):
                users.append({
                    'username': user.get('name'),
                    'pptp_enabled': user.get('pptp_enable'),
                    'openvpn_enabled': user.get('openvpn_enable'),
                    'l2tp_enabled': user.get('l2tp_enable')
                })
            return {'total': len(users), 'users': users}
        except Exception as e:
            raise Exception(f"Failed to list VPN users: {e}")

    def enable_vpn_user(self, username: str, protocol: str = "openvpn") -> Dict[str, Any]:
        """Enable VPN access for a user."""
        print(f"✅ Enabling {protocol} VPN for user {username}", file=sys.stderr)
        params = {'name': username}
        if protocol == "openvpn":
            params['openvpn_enable'] = True
        elif protocol == "pptp":
            params['pptp_enable'] = True
        elif protocol == "l2tp":
            params['l2tp_enable'] = True

        self._make_request(self.vpn_user_api, "1", "set", use_post=True, **params)
        return {'success': True, 'username': username, 'protocol': protocol, 'action': 'enabled'}

    def disable_vpn_user(self, username: str, protocol: str = "openvpn") -> Dict[str, Any]:
        """Disable VPN access for a user."""
        print(f"❌ Disabling {protocol} VPN for user {username}", file=sys.stderr)
        params = {'name': username}
        if protocol == "openvpn":
            params['openvpn_enable'] = False
        elif protocol == "pptp":
            params['pptp_enable'] = False
        elif protocol == "l2tp":
            params['l2tp_enable'] = False

        self._make_request(self.vpn_user_api, "1", "set", use_post=True, **params)
        return {'success': True, 'username': username, 'protocol': protocol, 'action': 'disabled'}
