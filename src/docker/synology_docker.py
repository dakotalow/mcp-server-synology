# Docker/Container Manager module for DSM 7.0+ using SYNO.Docker APIs

import requests
import json
from typing import Dict, List, Any, Optional
import sys


class SynologyDocker:
    """Handles Synology Docker/Container Manager API operations."""

    def __init__(self, base_url: str, session_id: str, verify_ssl: bool = False):
        self.base_url = base_url.rstrip('/')
        self.session_id = session_id
        self.verify_ssl = verify_ssl

        # API endpoints
        self.api_url = f"{self.base_url}/webapi/entry.cgi"

        # Container API
        self.container_api = "SYNO.Docker.Container"
        self.container_version = "1"

        # Project API (docker-compose)
        self.project_api = "SYNO.Docker.Project"
        self.project_version = "1"

        # Image API
        self.image_api = "SYNO.Docker.Image"
        self.image_version = "1"

        # Registry API
        self.registry_api = "SYNO.Docker.Registry"
        self.registry_version = "1"

        # Network API
        self.network_api = "SYNO.Docker.Network"
        self.network_version = "1"

    def _make_request(self, api: str, version: str, method: str, use_post: bool = False, **params) -> Dict[str, Any]:
        """Make a request to Synology Docker API."""
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
                error_msg = self._get_error_message(error_code)
                raise Exception(f"Docker API error {error_code}: {error_msg}")

            return data.get('data', {})

        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {e}")

    def _get_error_message(self, error_code: str) -> str:
        """Get human-readable error message for error codes."""
        error_messages = {
            '100': 'Unknown error',
            '101': 'Invalid parameter',
            '102': 'The requested API does not exist',
            '103': 'The requested method does not exist',
            '104': 'The requested version does not support the functionality',
            '105': 'The logged in session does not have permission',
            '106': 'Session timeout',
            '107': 'Session interrupted by duplicate login',
            '400': 'Container operation failed',
            '401': 'Container not found',
            '402': 'Image not found',
            '403': 'Container already running',
            '404': 'Container already stopped',
            '405': 'Invalid container configuration',
            '406': 'Network not found',
            '407': 'Volume not found',
            '408': 'Project not found',
            '409': 'Container name already exists',
            '410': 'Image pull failed'
        }
        return error_messages.get(str(error_code), f'Unknown error: {error_code}')

    # ==================== Container Operations ====================

    def list_containers(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """List all Docker containers.

        Returns:
            Dict containing container list with details like name, status, image, etc.
        """
        try:
            data = self._make_request(
                self.container_api,
                self.container_version,
                'list',
                limit=limit,
                offset=offset
            )

            containers = []
            for container in data.get('containers', []):
                container_info = {
                    'id': container.get('id'),
                    'name': container.get('name'),
                    'image': container.get('image'),
                    'status': container.get('status'),
                    'state': container.get('state'),
                    'created': container.get('created'),
                    'ports': container.get('ports', []),
                    'memory_limit': container.get('memory_limit'),
                    'cpu_priority': container.get('cpu_priority'),
                    'enable_restart_policy': container.get('enable_restart_policy'),
                    'is_package': container.get('is_package', False)
                }
                containers.append(container_info)

            return {
                'total': data.get('total', len(containers)),
                'offset': offset,
                'containers': containers
            }

        except Exception as e:
            # Try alternative API format
            try:
                data = self._make_request(
                    self.container_api,
                    "2",
                    'list',
                    limit=limit,
                    offset=offset
                )
                return data
            except Exception:
                raise Exception(f"Failed to list containers: {e}")

    def get_container(self, name: str) -> Dict[str, Any]:
        """Get detailed information about a specific container.

        Args:
            name: Container name or ID

        Returns:
            Dict with detailed container information
        """
        data = self._make_request(
            self.container_api,
            self.container_version,
            'get',
            name=name
        )
        return data

    def start_container(self, name: str) -> Dict[str, Any]:
        """Start a stopped container.

        Args:
            name: Container name or ID

        Returns:
            Dict with operation result
        """
        print(f"🚀 Starting container: {name}", file=sys.stderr)
        data = self._make_request(
            self.container_api,
            self.container_version,
            'start',
            use_post=True,
            name=name
        )
        print(f"✅ Container {name} started", file=sys.stderr)
        return {'success': True, 'container': name, 'action': 'started'}

    def stop_container(self, name: str) -> Dict[str, Any]:
        """Stop a running container.

        Args:
            name: Container name or ID

        Returns:
            Dict with operation result
        """
        print(f"🛑 Stopping container: {name}", file=sys.stderr)
        data = self._make_request(
            self.container_api,
            self.container_version,
            'stop',
            use_post=True,
            name=name
        )
        print(f"✅ Container {name} stopped", file=sys.stderr)
        return {'success': True, 'container': name, 'action': 'stopped'}

    def restart_container(self, name: str) -> Dict[str, Any]:
        """Restart a container.

        Args:
            name: Container name or ID

        Returns:
            Dict with operation result
        """
        print(f"🔄 Restarting container: {name}", file=sys.stderr)
        data = self._make_request(
            self.container_api,
            self.container_version,
            'restart',
            use_post=True,
            name=name
        )
        print(f"✅ Container {name} restarted", file=sys.stderr)
        return {'success': True, 'container': name, 'action': 'restarted'}

    def delete_container(self, name: str, force: bool = False) -> Dict[str, Any]:
        """Delete a container.

        Args:
            name: Container name or ID
            force: Force delete even if running

        Returns:
            Dict with operation result
        """
        print(f"🗑️ Deleting container: {name}", file=sys.stderr)
        data = self._make_request(
            self.container_api,
            self.container_version,
            'delete',
            use_post=True,
            name=name,
            force=force
        )
        print(f"✅ Container {name} deleted", file=sys.stderr)
        return {'success': True, 'container': name, 'action': 'deleted'}

    def get_container_logs(self, name: str, tail: int = 100) -> Dict[str, Any]:
        """Get container logs.

        Args:
            name: Container name or ID
            tail: Number of log lines to retrieve

        Returns:
            Dict with container logs
        """
        try:
            data = self._make_request(
                self.container_api,
                self.container_version,
                'get_log',
                name=name,
                tail=tail
            )
            return {
                'container': name,
                'logs': data.get('logs', ''),
                'tail': tail
            }
        except Exception as e:
            # Alternative method name
            try:
                data = self._make_request(
                    self.container_api,
                    self.container_version,
                    'log',
                    name=name,
                    tail=tail
                )
                return {
                    'container': name,
                    'logs': data.get('logs', data.get('log', '')),
                    'tail': tail
                }
            except Exception:
                raise Exception(f"Failed to get logs for {name}: {e}")

    def get_container_stats(self, name: str) -> Dict[str, Any]:
        """Get container resource usage statistics.

        Args:
            name: Container name or ID

        Returns:
            Dict with CPU, memory, network stats
        """
        data = self._make_request(
            self.container_api,
            self.container_version,
            'get_status',
            name=name
        )
        return {
            'container': name,
            'cpu_percent': data.get('cpu_percent', 0),
            'memory_usage': data.get('memory_usage', 0),
            'memory_limit': data.get('memory_limit', 0),
            'memory_percent': data.get('memory_percent', 0),
            'network_rx': data.get('network_rx', 0),
            'network_tx': data.get('network_tx', 0)
        }

    # ==================== Image Operations ====================

    def list_images(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """List all Docker images.

        Returns:
            Dict containing image list with details
        """
        try:
            data = self._make_request(
                self.image_api,
                self.image_version,
                'list',
                limit=limit,
                offset=offset
            )

            images = []
            for image in data.get('images', []):
                image_info = {
                    'id': image.get('id'),
                    'repository': image.get('repository'),
                    'tag': image.get('tag'),
                    'size': image.get('size'),
                    'created': image.get('created'),
                    'in_use': image.get('in_use', False)
                }
                images.append(image_info)

            return {
                'total': data.get('total', len(images)),
                'offset': offset,
                'images': images
            }
        except Exception as e:
            raise Exception(f"Failed to list images: {e}")

    def pull_image(self, repository: str, tag: str = 'latest') -> Dict[str, Any]:
        """Pull a Docker image from registry.

        Args:
            repository: Image repository (e.g., 'nginx', 'library/ubuntu')
            tag: Image tag (default: 'latest')

        Returns:
            Dict with pull operation result
        """
        print(f"📥 Pulling image: {repository}:{tag}", file=sys.stderr)
        data = self._make_request(
            self.image_api,
            self.image_version,
            'pull',
            use_post=True,
            repository=repository,
            tag=tag
        )
        print(f"✅ Image {repository}:{tag} pulled", file=sys.stderr)
        return {
            'success': True,
            'repository': repository,
            'tag': tag,
            'action': 'pulled'
        }

    def delete_image(self, image_id: str, force: bool = False) -> Dict[str, Any]:
        """Delete a Docker image.

        Args:
            image_id: Image ID or name:tag
            force: Force delete even if in use

        Returns:
            Dict with operation result
        """
        print(f"🗑️ Deleting image: {image_id}", file=sys.stderr)
        data = self._make_request(
            self.image_api,
            self.image_version,
            'delete',
            use_post=True,
            id=image_id,
            force=force
        )
        print(f"✅ Image {image_id} deleted", file=sys.stderr)
        return {'success': True, 'image': image_id, 'action': 'deleted'}

    # ==================== Project Operations (Docker Compose) ====================

    def list_projects(self) -> Dict[str, Any]:
        """List all Docker Compose projects.

        Returns:
            Dict containing project list with details
        """
        try:
            data = self._make_request(
                self.project_api,
                self.project_version,
                'list'
            )

            projects = []
            for project in data if isinstance(data, list) else data.get('projects', []):
                project_info = {
                    'id': project.get('id'),
                    'name': project.get('name'),
                    'status': project.get('status'),
                    'path': project.get('path'),
                    'services': project.get('services', []),
                    'created': project.get('created')
                }
                projects.append(project_info)

            return {
                'total': len(projects),
                'projects': projects
            }
        except Exception as e:
            raise Exception(f"Failed to list projects: {e}")

    def start_project(self, project_id: str) -> Dict[str, Any]:
        """Start a Docker Compose project.

        Args:
            project_id: Project ID (UUID)

        Returns:
            Dict with operation result
        """
        print(f"🚀 Starting project: {project_id}", file=sys.stderr)
        data = self._make_request(
            self.project_api,
            self.project_version,
            'start',
            use_post=True,
            id=f'"{project_id}"'  # Project IDs need to be quoted
        )
        print(f"✅ Project {project_id} started", file=sys.stderr)
        return {'success': True, 'project': project_id, 'action': 'started'}

    def stop_project(self, project_id: str) -> Dict[str, Any]:
        """Stop a Docker Compose project.

        Args:
            project_id: Project ID (UUID)

        Returns:
            Dict with operation result
        """
        print(f"🛑 Stopping project: {project_id}", file=sys.stderr)
        data = self._make_request(
            self.project_api,
            self.project_version,
            'stop',
            use_post=True,
            id=f'"{project_id}"'
        )
        print(f"✅ Project {project_id} stopped", file=sys.stderr)
        return {'success': True, 'project': project_id, 'action': 'stopped'}

    def get_project(self, project_id: str) -> Dict[str, Any]:
        """Get detailed information about a Docker Compose project.

        Args:
            project_id: Project ID (UUID)

        Returns:
            Dict with project details
        """
        data = self._make_request(
            self.project_api,
            self.project_version,
            'get',
            id=f'"{project_id}"'
        )
        return data

    # ==================== Network Operations ====================

    def list_networks(self) -> Dict[str, Any]:
        """List all Docker networks.

        Returns:
            Dict containing network list
        """
        try:
            data = self._make_request(
                self.network_api,
                self.network_version,
                'list'
            )

            networks = []
            for network in data.get('networks', []):
                network_info = {
                    'id': network.get('id'),
                    'name': network.get('name'),
                    'driver': network.get('driver'),
                    'scope': network.get('scope'),
                    'internal': network.get('internal', False),
                    'containers': network.get('containers', [])
                }
                networks.append(network_info)

            return {
                'total': len(networks),
                'networks': networks
            }
        except Exception as e:
            raise Exception(f"Failed to list networks: {e}")

    # ==================== Registry Operations ====================

    def list_registries(self) -> Dict[str, Any]:
        """List configured Docker registries.

        Returns:
            Dict containing registry list
        """
        try:
            data = self._make_request(
                self.registry_api,
                self.registry_version,
                'list'
            )
            return data
        except Exception as e:
            raise Exception(f"Failed to list registries: {e}")
