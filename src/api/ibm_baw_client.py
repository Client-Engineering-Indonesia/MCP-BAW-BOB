"""
IBM Business Automation Workflow Client

Provides high-level API for interacting with IBM BAW workflows.
"""

import os
import time
import httpx
import logging
from typing import Dict, Optional, Any
from src.core.ibm_baw_auth import IBMBAWAuthenticator

logger = logging.getLogger(__name__)


class IBMBAWClient:
    """Client for IBM Business Automation Workflow REST API."""
    
    def __init__(self, authenticator: IBMBAWAuthenticator):
        """
        Initialize the BAW client.
        
        Args:
            authenticator: Configured IBMBAWAuthenticator instance
        """
        self.authenticator = authenticator
        self.base_url = authenticator.base_url

        self.client = httpx.Client(
            verify=authenticator.verify_ssl,
            timeout=authenticator.request_timeout
        )
    
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
        max_attempts = self.authenticator.max_retries + 1
        retryable_status_codes = {429, 500, 502, 503, 504}

        for attempt_number in range(1, max_attempts + 1):
            try:
                response = self.client.request(method=method, url=url, **kwargs)

                # Check for retryable status codes
                if response.status_code in retryable_status_codes:
                    if attempt_number < max_attempts:
                        retry_delay = min(2 ** (attempt_number - 1), 10)
                        logger.warning(
                            "Transient API error %d on attempt %d/%d to %s; retrying in %ds",
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
                        "API request attempt %d/%d failed for %s: %s; retrying in %ds",
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

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make an authenticated request to the BAW API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            json_data: JSON body data
            
        Returns:
            Response JSON data
            
        Raises:
            httpx.HTTPError: If request fails
        """
        url = f"{self.base_url}{endpoint}"
        headers = self.authenticator.get_auth_headers()
        
        logger.info(f"Making {method} request to {url}")
        
        response = self._request_with_retry(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=json_data
        )
        return response.json()
    
    def get_process_app(
        self,
        app_acronym: str,
        parts: str = "all"
    ) -> Dict[str, Any]:
        """
        Get details about a specific process application.
        
        Args:
            app_acronym: Process application acronym (e.g., 'LC1')
            parts: Parts to include in response (default: 'all')
            
        Returns:
            Process application details
        """
        endpoint = f"/bas/rest/bpm/wle/v1/processApp/{app_acronym}"
        params = {"parts": parts}
        
        logger.info(f"Fetching process app: {app_acronym}")
        return self._make_request("GET", endpoint, params=params)
    
    def list_process_apps(
        self,
        parts: str = "all"
    ) -> Dict[str, Any]:
        """
        List all process applications.
        
        Args:
            parts: Parts to include in response (default: 'all')
            
        Returns:
            List of process applications
        """
        endpoint = "/bas/rest/bpm/wle/v1/processApps"
        params = {"parts": parts}
        
        logger.info("Fetching all process apps")
        return self._make_request("GET", endpoint, params=params)
    
    def list_exposed_processes(
        self,
        process_app_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List exposed processes (workflows).
        
        Args:
            process_app_id: Optional process app ID to filter by
            
        Returns:
            List of exposed processes
        """
        endpoint = "/bas/rest/bpm/wle/v1/exposed/process"
        params = {}
        
        if process_app_id:
            params["processAppId"] = process_app_id
        
        logger.info("Fetching exposed processes")
        return self._make_request("GET", endpoint, params=params)
    
    
    def export_process_app(
        self,
        acronym: str,
        version: str,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Export a process application to a TWX file.
        
        Args:
            acronym: Process application acronym (e.g., 'LC1')
            version: Snapshot version name (e.g., '1')
            output_path: Optional path to save the exported file (default: {acronym}_Export.twx)
            
        Returns:
            Dictionary containing:
                - status: Export status ('success')
                - file_path: Path to exported file
                - file_size: File size in bytes
                - acronym: Process app acronym
                - version: Snapshot version
            
        Raises:
            httpx.HTTPError: If export request fails
            IOError: If file write fails
        """
        endpoint = f"/bas/ops/std/bpm/containers/{acronym}/versions/{version}/export"
        url = f"{self.base_url}{endpoint}"
        auth_headers = self.authenticator.get_auth_headers()
        
        # Add Accept header for binary content
        auth_headers['Accept'] = 'application/octet-stream, application/zip, */*'
        
        logger.info(f"Exporting process app: {acronym} version {version}")
        
        # Ensure output_path is absolute
        if output_path is None:
            output_path = os.path.abspath(f"{acronym}_Export.twx")
        else:
            output_path = os.path.abspath(output_path)
        
        logger.info(f"Export destination: {output_path}")
        
        try:
            # Make the request to get binary content
            response = self._request_with_retry(
                method="GET",
                url=url,
                headers=auth_headers
            )
            
            # Ensure directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                logger.info(f"Created directory: {output_dir}")
            
            # Write binary content to file
            with open(output_path, 'wb') as file_handle:
                file_handle.write(response.content)
            
            file_size_bytes = len(response.content)
            logger.info(f"Successfully exported {acronym} to {output_path} ({file_size_bytes} bytes)")
            
            return {
                "status": "success",
                "file_path": output_path,
                "file_size": file_size_bytes,
                "acronym": acronym,
                "version": version
            }
            
        except Exception as e:
            logger.error(f"Failed to export process app {acronym}: {e}")
            raise
    
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
