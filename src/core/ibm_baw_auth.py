"""
IBM Business Automation Workflow Authentication Module

Handles authentication and token management for IBM CP4BA REST API.
"""

import time
import httpx
from typing import Optional, Dict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class IBMBAWAuthenticator:
    """Manages authentication tokens for IBM Business Automation Workflow."""
    
    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        token_lifetime: int = 7200,
        verify_ssl: bool = False,
        request_timeout: float = 30.0,
        max_retries: int = 3
    ):
        """
        Initialize the authenticator.
        
        Args:
            base_url: Base URL of the CP4BA instance
            username: CP4BA username
            password: CP4BA password
            token_lifetime: Token lifetime in seconds (default: 7200)
            verify_ssl: Verify SSL certificates
            request_timeout: HTTP request timeout in seconds
            max_retries: Maximum retry attempts for transient failures
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.token_lifetime = token_lifetime
        self.verify_ssl = verify_ssl
        self.request_timeout = request_timeout
        self.max_retries = max_retries

        self.access_token: Optional[str] = None
        self.csrf_token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None

        self.client = httpx.Client(
            verify=self.verify_ssl,
            timeout=self.request_timeout
        )
        
    def _is_token_valid(self) -> bool:
        """Check if current tokens are still valid."""
        if not self.access_token or not self.csrf_token:
            return False
        
        if not self.token_expiry:
            return False
            
        # Add 60 second buffer before expiry
        return datetime.now() < (self.token_expiry - timedelta(seconds=60))
    
    def _request_with_retry(self, method: str, url: str, **kwargs) -> httpx.Response:
        """
        Execute HTTP request with exponential backoff retry for transient failures.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            **kwargs: Additional request parameters
            
        Returns:
            HTTP response object
            
        Raises:
            httpx.HTTPError: If request fails after all retries
        """
        last_exception: Optional[Exception] = None
        max_attempts = self.max_retries + 1
        retryable_status_codes = {429, 500, 502, 503, 504}

        for attempt_number in range(1, max_attempts + 1):
            try:
                response = self.client.request(method=method, url=url, **kwargs)

                # Check for retryable status codes
                if response.status_code in retryable_status_codes:
                    if attempt_number < max_attempts:
                        retry_delay = min(2 ** (attempt_number - 1), 10)
                        logger.warning(
                            "Transient auth error %d on attempt %d/%d to %s; retrying in %ds",
                            response.status_code,
                            attempt_number,
                            max_attempts,
                            url,
                            retry_delay
                        )
                        time.sleep(retry_delay)
                        continue

                response.raise_for_status()
                return response
                
            except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as exc:
                last_exception = exc
                
                # Determine if error is retryable
                is_retryable = isinstance(exc, (httpx.TimeoutException, httpx.NetworkError))
                if isinstance(exc, httpx.HTTPStatusError) and exc.response:
                    is_retryable = exc.response.status_code in retryable_status_codes

                if is_retryable and attempt_number < max_attempts:
                    retry_delay = min(2 ** (attempt_number - 1), 10)
                    logger.warning(
                        "Auth request attempt %d/%d failed for %s: %s; retrying in %ds",
                        attempt_number,
                        max_attempts,
                        url,
                        exc,
                        retry_delay
                    )
                    time.sleep(retry_delay)
                    continue
                raise

        if last_exception:
            raise last_exception
        raise RuntimeError("HTTP request failed without captured exception")

    def _get_access_token(self) -> str:
        """
        Authenticate and retrieve access token from CP4BA.
        
        Returns:
            Access token string
            
        Raises:
            httpx.HTTPError: If authentication request fails
            ValueError: If no token in response
        """
        auth_endpoint = f"{self.base_url}/icp4d-api/v1/authorize"
        
        auth_payload = {
            "username": self.username,
            "password": self.password
        }
        
        logger.info(f"Authenticating to {auth_endpoint}")
        
        response = self._request_with_retry(
            "POST",
            auth_endpoint,
            json=auth_payload,
            headers={"Content-Type": "application/json"}
        )
        
        response_data = response.json()
        access_token = response_data.get("token")
        
        if not access_token:
            raise ValueError("No token received from authentication endpoint")
        
        logger.info("Successfully obtained access token")
        return access_token
    
    def _get_csrf_token(self, access_token: str) -> str:
        """
        Retrieve CSRF token using the access token.
        
        Args:
            access_token: Valid access token
            
        Returns:
            CSRF token string
            
        Raises:
            httpx.HTTPError: If CSRF token request fails
            ValueError: If no CSRF token in response
        """
        csrf_endpoint = f"{self.base_url}/bas/bpm/system/login"
        
        csrf_payload = {
            "refresh-groups": False,
            "requested-lifetime": self.token_lifetime
        }
        
        logger.info(f"Requesting CSRF token from {csrf_endpoint}")
        
        response = self._request_with_retry(
            "POST",
            csrf_endpoint,
            json=csrf_payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}"
            }
        )
        
        response_data = response.json()
        csrf_token = response_data.get("csrf_token")
        
        if not csrf_token:
            raise ValueError("No CSRF token received from login endpoint")
        
        logger.info("Successfully obtained CSRF token")
        return csrf_token
    
    def authenticate(self) -> Dict[str, str]:
        """
        Perform full authentication flow and return tokens.
        
        Returns:
            Dictionary with 'access_token' and 'csrf_token'
            
        Raises:
            httpx.HTTPError: If authentication fails
        """
        logger.info("Starting authentication flow")
        
        # Get access token
        self.access_token = self._get_access_token()
        
        # Get CSRF token
        self.csrf_token = self._get_csrf_token(self.access_token)
        
        # Set expiry time
        self.token_expiry = datetime.now() + timedelta(seconds=self.token_lifetime)
        
        logger.info(f"Authentication complete. Tokens valid until {self.token_expiry}")
        
        return {
            "access_token": self.access_token,
            "csrf_token": self.csrf_token
        }
    
    def get_tokens(self) -> Dict[str, str]:
        """
        Get valid tokens, refreshing if necessary.
        
        Returns:
            Dictionary with 'access_token' and 'csrf_token'
        """
        if not self._is_token_valid():
            logger.info("Tokens expired or missing, re-authenticating")
            self.authenticate()
        
        if self.access_token is None or self.csrf_token is None:
            raise RuntimeError("Authentication completed without valid tokens")

        return {
            "access_token": self.access_token,
            "csrf_token": self.csrf_token
        }
    
    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for API requests.
        
        Returns:
            Dictionary of headers including Authorization and BPMCSRFToken
        """
        tokens = self.get_tokens()
        
        return {
            "Authorization": f"Bearer {tokens['access_token']}",
            "BPMCSRFToken": tokens['csrf_token'],
            "Accept": "application/json"
        }
    
    def close(self):
        """Close the HTTP client."""
        self.client.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

# Made with Bob
