#!/usr/bin/env python3
"""
HUEY_P Comprehensive Security Architecture

Provides a complete security framework for the HUEY_P system, addressing
authentication, authorization, encryption, network security, and credential
management across all system components.
"""

import hashlib
import hmac
import json
import logging
import os
import secrets
import socket
import ssl
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import jwt
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """Enumeration for data and component security classification levels."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class ComponentType(Enum):
    """Enumeration for the different types of system components."""
    PYTHON_SERVICE = "python_service"
    CPP_BRIDGE = "cpp_bridge"
    MT4_EA = "mt4_ea"
    DATABASE = "database"
    API_GATEWAY = "api_gateway"


class PermissionType(Enum):
    """Enumeration for operation permissions."""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"


class SecurityPolicy:
    """
    Defines a security policy for a resource.

    Attributes:
        resource_name: The name of the resource this policy applies to.
        required_permissions: List of permissions needed to access the resource.
        encryption_required: Whether data in transit must be encrypted.
        audit_required: Whether access to this resource should be audited.
    """
    def __init__(self, resource_name: str, required_permissions: List[PermissionType], encryption_required: bool = True, audit_required: bool = True):
        self.resource_name = resource_name
        self.required_permissions = required_permissions
        self.encryption_required = encryption_required
        self.audit_required = audit_required


class CryptographyManager:
    """Handles all cryptographic operations for the system."""

    def __init__(self, master_key: Optional[str] = None):
        """
        Initializes the CryptographyManager.

        Args:
            master_key: An optional master key for symmetric encryption.
                        If not provided, a new one is generated.
        """
        self.master_key = master_key or Fernet.generate_key().decode()
        self.fernet = Fernet(self.master_key.encode())
        self.private_key, self.public_key = self._generate_rsa_keys()

    def _generate_rsa_keys(self) -> Tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
        """Generates a new RSA key pair for asymmetric encryption."""
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        return private_key, private_key.public_key()

    def encrypt_data(self, data: str) -> str:
        """Symmetrically encrypts data using Fernet."""
        return self.fernet.encrypt(data.encode()).decode()

    def decrypt_data(self, encrypted_data: str) -> Optional[str]:
        """Symmetrically decrypts data using Fernet."""
        try:
            return self.fernet.decrypt(encrypted_data.encode()).decode()
        except InvalidToken:
            logger.error("Failed to decrypt data due to invalid token.")
            return None


class AuthenticationManager:
    """Manages component authentication using JWTs and API keys."""

    def __init__(self, secret_key: str, credential_store: "SecureCredentialStore"):
        """
        Initializes the AuthenticationManager.

        Args:
            secret_key: A secret key for signing JWTs.
            credential_store: An instance of SecureCredentialStore.
        """
        self.secret_key = secret_key
        self.credential_store = credential_store

    def authenticate_component(
        self, component_id: str, api_key: str, component_type: ComponentType
    ) -> Optional[str]:
        """
        Authenticates a component and returns a JWT.

        Args:
            component_id: The ID of the component to authenticate.
            api_key: The API key provided by the component.
            component_type: The type of the component.

        Returns:
            A JWT string on successful authentication, otherwise None.
        """
        if not self._verify_api_key(component_id, api_key):
            logger.warning(f"Authentication failed for component {component_id}")
            return None

        payload = {
            "component_id": component_id,
            "component_type": component_type.value,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=1),
        }
        token = jwt.encode(payload, self.secret_key, algorithm="HS256")
        logger.info(f"Component {component_id} authenticated successfully.")
        return token

    def _verify_api_key(self, component_id: str, api_key: str) -> bool:
        """Verifies an API key against the credential store."""
        expected_key = self.credential_store.retrieve_credential(f"{component_id}_api_key")
        if not expected_key:
            return False
        return hmac.compare_digest(api_key, expected_key)


class AuthorizationManager:
    """Manages component permissions and access control based on policies."""

    def __init__(self):
        """Initializes the AuthorizationManager with default policies."""
        self.policies: Dict[str, SecurityPolicy] = {
            "trading_signals": SecurityPolicy("trading_signals", [PermissionType.READ, PermissionType.WRITE]),
            "market_data": SecurityPolicy("market_data", [PermissionType.READ], encryption_required=False),
            "risk_metrics": SecurityPolicy("risk_metrics", [PermissionType.READ, PermissionType.WRITE]),
        }
        self.component_permissions: Dict[str, List[PermissionType]] = {
            "python_signal_service": [PermissionType.READ, PermissionType.WRITE],
            "risk_service": [PermissionType.READ, PermissionType.WRITE],
        }

    def check_permission(self, component_id: str, resource: str, operation: PermissionType) -> bool:
        """
        Checks if a component has permission to perform an operation on a resource.

        Args:
            component_id: The ID of the component.
            resource: The name of the resource being accessed.
            operation: The permission type being requested.

        Returns:
            True if authorized, False otherwise.
        """
        policy = self.policies.get(resource)
        if not policy:
            logger.warning(f"No security policy found for resource: {resource}")
            return False

        if operation not in policy.required_permissions:
            return False
        
        return operation in self.component_permissions.get(component_id, [])


class SecurityAuditor:
    """Audits security events and maintains security logs."""

    def __init__(self, audit_log_path: str = "security_audit.log"):
        """
        Initializes the SecurityAuditor.

        Args:
            audit_log_path: Path to the audit log file.
        """
        self.log_path = Path(audit_log_path)
        self.lock = threading.Lock()

    def log_event(self, event_type: str, details: Dict[str, Any]):
        """
        Logs a security-related event.

        Args:
            event_type: The type of event (e.g., "authentication", "authorization").
            details: A dictionary containing event details.
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            **details,
        }
        with self.lock:
            try:
                with open(self.log_path, "a") as f:
                    f.write(json.dumps(log_entry) + "\n")
            except IOError as e:
                logger.error(f"Failed to write to audit log: {e}")


class SecureCredentialStore:
    """Provides secure, encrypted storage for credentials."""

    def __init__(self, store_path: str, crypto_manager: CryptographyManager):
        """
        Initializes the SecureCredentialStore.

        Args:
            store_path: Path to the encrypted credential store file.
            crypto_manager: An instance of CryptographyManager.
        """
        self.store_path = Path(store_path)
        self.crypto = crypto_manager
        self.credentials: Dict[str, str] = self._load_credentials()

    def store_credential(self, key: str, value: str):
        """Encrypts and stores a credential."""
        encrypted_value = self.crypto.encrypt_data(value)
        self.credentials[key] = encrypted_value
        self._save_credentials()

    def retrieve_credential(self, key: str) -> Optional[str]:
        """Retrieves and decrypts a credential."""
        encrypted_value = self.credentials.get(key)
        if encrypted_value:
            return self.crypto.decrypt_data(encrypted_value)
        return None

    def _load_credentials(self) -> Dict[str, str]:
        """Loads and decrypts credentials from the store file."""
        if not self.store_path.exists():
            return {}
        try:
            with open(self.store_path, "r") as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load credential store: {e}")
            return {}

    def _save_credentials(self):
        """Saves the encrypted credentials to the store file."""
        try:
            with open(self.store_path, "w") as f:
                json.dump(self.credentials, f)
        except IOError as e:
            logger.error(f"Failed to save credential store: {e}")


class SecurityManager:
    """Main security orchestrator for the HUEY_P system."""

    def __init__(self):
        """Initializes all security components."""
        self.crypto_manager = CryptographyManager()
        self.secret_key = secrets.token_urlsafe(32)
        self.credential_store = SecureCredentialStore(
            "credentials.enc", self.crypto_manager
        )
        self.auth_manager = AuthenticationManager(self.secret_key, self.credential_store)
        self.authz_manager = AuthorizationManager()
        self.auditor = SecurityAuditor()
        self._initialize_credentials()

    def _initialize_credentials(self):
        """Initializes default credentials if they don't exist."""
        if not self.credential_store.retrieve_credential("python_signal_service_api_key"):
            api_key = secrets.token_hex(16)
            self.credential_store.store_credential("python_signal_service_api_key", api_key)
            logger.info("Initialized API key for python_signal_service.")

    @contextmanager
    def secure_operation(self, component_id: str, resource: str, operation: PermissionType):
        """
        A context manager for performing secure, authorized operations.

        Args:
            component_id: The ID of the component performing the operation.
            resource: The resource being accessed.
            operation: The permission being requested.

        Yields:
            None if authorization is successful.

        Raises:
            PermissionError: If the component is not authorized.
        """
        is_authorized = self.authz_manager.check_permission(component_id, resource, operation)
        self.auditor.log_event(
            "authorization",
            {
                "component_id": component_id, "resource": resource,
                "operation": operation.value, "granted": is_authorized
            }
        )
        if not is_authorized:
            raise PermissionError(f"Component '{component_id}' not authorized for '{operation.value}' on '{resource}'.")
        yield


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    sec_mgr = SecurityManager()
    
    # Example: Authenticate and perform a secure operation
    comp_id = "python_signal_service"
    key = sec_mgr.credential_store.retrieve_credential(f"{comp_id}_api_key")
    
    token = sec_mgr.auth_manager.authenticate_component(comp_id, key, ComponentType.PYTHON_SERVICE)
    
    if token:
        logger.info(f"Authentication successful for {comp_id}.")
        try:
            with sec_mgr.secure_operation(comp_id, "trading_signals", PermissionType.WRITE):
                logger.info("Secure operation: Writing trading signals authorized and successful.")
        except PermissionError as e:
            logger.error(f"Authorization check failed: {e}")