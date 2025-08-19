# Copyright (c) 2025 Jonathan Piette
# This file is part of TheOpenMusicBox and is licensed for non-commercial use only.
# See the LICENSE file for details.
"""Service for mDNS advertisement of API endpoints using zeroconf.

This service will publish a HTTP service on the local network with mDNS/Bonjour/Zeroconf, making it discoverable by other devices on the LAN without knowing the exact IP.

Args: None

Returns: None
"""

import socket
from typing import Optional

from zeroconf import IPVersion, ServiceInfo, Zeroconf

from app.src.monitoring.improved_logger import ImprovedLogger, LogLevel

logger = ImprovedLogger(__name__)


class MDNSService:
    """Advertises the API via mDNS/Bonjour/Zeroconf on the local network.

    All service metadata is sourced from the config system.
    """

    def __init__(self):
        """Initialize the mDNS service using the global app configuration."""
        from app.src.config import config

        self.config = config
        self.zeroconf_instance: Optional[Zeroconf] = None
        self.service_info: Optional[ServiceInfo] = None
        self._is_registered = False

    def register_service(self) -> bool:
        """Register the API service on mDNS/Bonjour network.

        Returns:
            bool: True if registration was successful, False otherwise.
        """
        try:
            # Get the host IP (non-loopback)
            ip = self._get_local_ip()
            if not ip:
                logger.log(
                    LogLevel.ERROR,
                    "Could not determine local IP address for mDNS registration. Aborting registration.",
                )
                return False

            # Create zeroconf instance if it doesn't exist
            if not self.zeroconf_instance:
                self.zeroconf_instance = Zeroconf(ip_version=IPVersion.V4)

            # Use port from config (no fallback)
            port = self.config.socketio_port

            # Create an mDNS service
            self.service_info = ServiceInfo(
                self.config.mdns_service_type,
                self.config.mdns_service_name,
                addresses=[socket.inet_aton(ip)],
                port=port,
                weight=0,
                priority=0,
                properties={
                    "path": self.config.mdns_service_path,
                    "version": self.config.mdns_service_version,
                    "name": self.config.mdns_service_friendly_name,
                },
                server=self.config.mdns_service_hostname,  # This is the mDNS hostname
            )

            # Register the service
            self.zeroconf_instance.register_service(self.service_info)
            self._is_registered = True

            logger.log(
                LogLevel.INFO,
                f"mDNS service registered successfully at {ip}:{port}",
            )
            return True
        except Exception as e:
            logger.log(LogLevel.ERROR, f"mDNS service registration failed: {str(e)}")
            self._cleanup_zeroconf()
            return False

    def unregister_service(self) -> bool:
        """Unregister the mDNS service from the network.

        Returns:
            bool: True if unregistration was successful or no service was registered, False if an error occurred.
        """
        if not self._is_registered or not self.zeroconf_instance:
            return True
        try:
            if self.service_info:
                self.zeroconf_instance.unregister_service(self.service_info)
            self._cleanup_zeroconf()
            logger.log(LogLevel.INFO, "mDNS service unregistered successfully")
            return True
        except Exception as e:
            logger.log(LogLevel.ERROR, f"Failed to unregister mDNS service: {str(e)}")
            return False
        finally:
            self._is_registered = False
            self.service_info = None

    def _cleanup_zeroconf(self) -> None:
        """Close and clean up the zeroconf instance.

        Args: None

        Returns: None
        """
        if self.zeroconf_instance:
            try:
                self.zeroconf_instance.close()
            except Exception as e:
                logger.log(LogLevel.ERROR, f"Error closing zeroconf: {str(e)}")
            finally:
                self.zeroconf_instance = None

    def _get_local_ip(self) -> Optional[str]:
        """Get the local non-loopback IP address of this device.

        Returns:
            str or None: The IP address as a string or None if no suitable IP is found.
        """
        try:
            # Create a temporary socket to get local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                # Connecting to an arbitrary public IP (doesn't actually send packets)
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                return local_ip
            finally:
                s.close()
        except Exception as e:
            logger.log(LogLevel.WARNING, f"Error getting local IP: {str(e)}")
            return None
