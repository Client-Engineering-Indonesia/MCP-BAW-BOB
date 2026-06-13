"""
IBM Business Automation Workflow MCP Server - Production Version

Production-ready FastMCP server with enhanced error handling, logging,
configuration management, and monitoring capabilities.
"""

import sys
import re
import os
from typing import Any, Optional
from fastmcp import FastMCP
from src.core.config import get_config
from src.utils.logger import setup_logging, get_logger
from src.core.ibm_baw_auth import IBMBAWAuthenticator
from src.api.ibm_baw_client import IBMBAWClient

# Initialize configuration
try:
    config = get_config()
except Exception as e:
    print(f"FATAL: Configuration error: {e}", file=sys.stderr)
    print("Please ensure .env file exists with required variables.", file=sys.stderr)
    sys.exit(1)

# Setup logging
setup_logging(
    log_level=config.log_level,
    log_file_path="logs/ibm_baw_mcp.log",
    enable_colors=True
)

logger = get_logger(__name__)

# Initialize FastMCP server
mcp = FastMCP("IBM BAW Workflow Server")

# Global client instance
_client: Optional[IBMBAWClient] = None
_authenticator: Optional[IBMBAWAuthenticator] = None


def get_client() -> IBMBAWClient:
    """
    Get or create the BAW client instance with production configuration.
    
    Returns:
        Configured IBMBAWClient instance
        
    Raises:
        RuntimeError: If client initialization fails
    """
    global _client, _authenticator
    
    if _client is None:
        try:
            logger.info(f"Initializing IBM BAW client for {config.cp4ba_base_url}")
            
            # Create authenticator with production settings
            _authenticator = IBMBAWAuthenticator(
                base_url=config.cp4ba_base_url,
                username=config.cp4ba_username,
                password=config.cp4ba_password,
                token_lifetime=config.token_lifetime,
                verify_ssl=config.verify_ssl,
                request_timeout=config.get_timeout(),
                max_retries=config.max_retries
            )
            
            # Perform initial authentication
            _authenticator.authenticate()
            logger.info("Initial authentication successful")
            
            # Create client
            _client = IBMBAWClient(_authenticator)
            
            logger.info("IBM BAW client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize IBM BAW client: {e}", exc_info=True)
            raise RuntimeError(f"Client initialization failed: {e}")
    
    return _client


def format_error(error: Exception, context: str = "") -> str:
    """
    Format error message for user-friendly output.
    
    Args:
        error: Exception that occurred
        context: Additional context about the error
        
    Returns:
        Formatted error message
    """
    error_type = type(error).__name__
    error_msg = str(error)
    
    if context:
        return f"❌ Error in {context}: {error_type} - {error_msg}"
    else:
        return f"❌ Error: {error_type} - {error_msg}"


def _normalize_text(value: Any) -> str:
    """
    Normalize text value for consistent MCP output.
    
    Args:
        value: Value to normalize (any type)
        
    Returns:
        Normalized string representation
    """
    if value is None:
        return "N/A"
    if isinstance(value, bool):
        return "true" if value else "false"
    
    text = str(value).strip()
    if not text:
        return "N/A"
    
    # Remove HTML tags and normalize whitespace
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    
    return text or "N/A"


def _format_field(output_lines: list[str], field_label: str, field_value: Any) -> None:
    """
    Append a formatted field to output lines.
    
    Args:
        output_lines: List to append formatted field to
        field_label: Label for the field
        field_value: Value of the field
    """
    output_lines.append(f"   {field_label}: {_normalize_text(field_value)}")


def _format_snapshot_details(output_lines: list[str], snapshots: Any) -> None:
    """
    Format and append snapshot details to output.
    
    Args:
        output_lines: List to append snapshot details to
        snapshots: List of snapshot dictionaries
    """
    if not snapshots:
        output_lines.append("   Installed Snapshots: none")
        return

    output_lines.append(f"   Installed Snapshots ({len(snapshots)}):")
    for idx, snapshot in enumerate(snapshots, 1):
        output_lines.append(f"      {idx}. {_normalize_text(snapshot.get('name'))}")
        output_lines.append(f"         ID: {_normalize_text(snapshot.get('ID'))}")
        output_lines.append(f"         Acronym: {_normalize_text(snapshot.get('acronym'))}")
        output_lines.append(f"         Active: {_normalize_text(snapshot.get('active'))}")
        output_lines.append(f"         Active Since: {_normalize_text(snapshot.get('activeSince'))}")
        output_lines.append(f"         Created On: {_normalize_text(snapshot.get('createdOn'))}")
        output_lines.append(f"         Snapshot Tip: {_normalize_text(snapshot.get('snapshotTip'))}")
        output_lines.append(f"         Branch ID: {_normalize_text(snapshot.get('branchID'))}")
        output_lines.append(f"         Branch Name: {_normalize_text(snapshot.get('branchName'))}")


@mcp.tool()
def list_workflows() -> str:
    """
    List all available workflows (exposed processes) in IBM BAW.

    Returns detailed workflow metadata including process app, snapshot,
    branch information, and launch URLs.
    
    Returns:
        Formatted string with workflow details or error message
    """
    try:
        logger.info("Listing workflows")
        client = get_client()
        response_data = client.list_exposed_processes()

        if "data" not in response_data or "exposedItemsList" not in response_data["data"]:
            logger.warning(f"Unexpected response format: {response_data}")
            return "⚠️ Unexpected response format. Please check logs."

        workflows = response_data["data"]["exposedItemsList"]

        if not workflows:
            logger.info("No workflows found")
            return "No workflows found."

        logger.info(f"Found {len(workflows)} workflow(s)")

        output_lines = [f"✅ Found {len(workflows)} workflow(s):"]

        for idx, workflow in enumerate(workflows, 1):
            output_lines.append(f"\n{idx}. {_normalize_text(workflow.get('display'))}")
            _format_field(output_lines, "Exposed Item ID", workflow.get("ID"))
            _format_field(output_lines, "Item ID", workflow.get("itemID"))
            _format_field(output_lines, "Item Reference", workflow.get("itemReference"))
            _format_field(output_lines, "Type", workflow.get("type"))
            _format_field(output_lines, "Subtype", workflow.get("subtype"))
            _format_field(output_lines, "Title", workflow.get("title"))
            _format_field(output_lines, "Tip", workflow.get("tip"))
            _format_field(output_lines, "Default", workflow.get("isDefault"))
            _format_field(output_lines, "Mobile Ready", workflow.get("isMobileReady"))

            _format_field(output_lines, "Process App Name", workflow.get("processAppName"))
            _format_field(output_lines, "Process App Acronym", workflow.get("processAppAcronym"))
            _format_field(output_lines, "Process App ID", workflow.get("processAppID"))

            _format_field(output_lines, "Snapshot Name", workflow.get("snapshotName"))
            _format_field(output_lines, "Snapshot ID", workflow.get("snapshotID"))
            _format_field(output_lines, "Snapshot Created On", workflow.get("snapshotCreatedOn"))

            _format_field(output_lines, "Branch Name", workflow.get("branchName"))
            _format_field(output_lines, "Branch ID", workflow.get("branchID"))

            _format_field(output_lines, "Item Description", workflow.get("itemDescription"))
            _format_field(output_lines, "Top Toolkit Name", workflow.get("topLevelToolkitName"))
            _format_field(output_lines, "Top Toolkit Acronym", workflow.get("topLevelToolkitAcronym"))
            _format_field(output_lines, "Start URL", workflow.get("startUrl"))
            _format_field(output_lines, "Run URL", workflow.get("runURL"))

        return "\n".join(output_lines)

    except Exception as e:
        logger.error(f"Error listing workflows: {e}", exc_info=True)
        return format_error(e, "list_workflows")


@mcp.tool()
def list_process_apps() -> str:
    """
    List all process applications available in IBM BAW.

    Returns detailed application metadata including identifiers, descriptions,
    branch information, and installed snapshots.
    
    Returns:
        Formatted string with process app details or error message
    """
    try:
        logger.info("Listing process applications")
        client = get_client()
        response_data = client.list_process_apps()

        if "data" not in response_data or "processAppsList" not in response_data["data"]:
            logger.warning(f"Unexpected response format: {response_data}")
            return "⚠️ Unexpected response format. Please check logs."

        process_apps = response_data["data"]["processAppsList"]

        if not process_apps:
            logger.info("No process applications found")
            return "No process applications found."

        logger.info(f"Found {len(process_apps)} process application(s)")

        output_lines = [f"✅ Found {len(process_apps)} process application(s):"]

        for idx, app in enumerate(process_apps, 1):
            output_lines.append(f"\n{idx}. {_normalize_text(app.get('name'))}")
            _format_field(output_lines, "ID", app.get("ID"))
            _format_field(output_lines, "Short Name", app.get("shortName"))
            _format_field(output_lines, "Acronym", app.get("acronym"))
            _format_field(output_lines, "Description", app.get("description"))
            _format_field(output_lines, "Rich Description", app.get("richDescription"))
            _format_field(output_lines, "Default Version", app.get("defaultVersion"))
            _format_field(output_lines, "Default Branch ID", app.get("defaultBranchID"))
            _format_field(output_lines, "Last Modified By", app.get("lastModifiedBy"))
            _format_field(output_lines, "Last Modified On", app.get("lastModified_on"))
            _format_snapshot_details(output_lines, app.get("installedSnapshots"))

        return "\n".join(output_lines)

    except Exception as e:
        logger.error(f"Error listing process apps: {e}", exc_info=True)
        return format_error(e, "list_process_apps")


@mcp.tool()
def export_process_app(
    acronym: str,
    version: str,
    output_path: Optional[str] = None,
    workspace_path: Optional[str] = None
) -> str:
    """
    Export a process application to a TWX file.
    
    The AI assistant (Bob) should automatically provide the workspace_path from the
    current workspace directory in the environment details.
    
    Args:
        acronym: Process application acronym (e.g., 'LC1')
        version: Snapshot version name (e.g., '1')
        output_path: Optional filename or relative path (default: {acronym}_Export.twx)
        workspace_path: Workspace directory path (provided by AI assistant from environment)
    
    Returns:
        Formatted string with export status and file information
    """
    try:
        logger.info(f"Exporting process app: {acronym} version {version}")
        client = get_client()
        
        # Determine the final output path
        if output_path is None:
            # Use default filename
            filename = f"{acronym}_Export.twx"
        else:
            filename = output_path
        
        # Determine target directory
        if workspace_path:
            # Use workspace path provided by AI assistant
            target_dir = os.path.abspath(workspace_path)
            logger.info(f"Using workspace directory: {target_dir}")
        else:
            # Fallback to current working directory
            target_dir = os.getcwd()
            logger.info(f"No workspace path provided, using current directory: {target_dir}")
        
        # Construct full path
        if os.path.isabs(filename):
            # Absolute path provided - use as is
            final_path = filename
        else:
            # Relative path or filename - combine with target directory
            final_path = os.path.join(target_dir, filename)
        
        logger.info(f"Export destination: {final_path}")
        
        export_result = client.export_process_app(
            acronym=acronym,
            version=version,
            output_path=final_path
        )
        
        logger.info(f"Export successful: {export_result['file_path']}")
        
        file_size_bytes = export_result['file_size']
        file_size_mb = file_size_bytes / 1024 / 1024
        
        output_lines = [
            "✅ Process application exported successfully!",
            "",
            f"   Acronym: {export_result['acronym']}",
            f"   Version: {export_result['version']}",
            f"   File Path: {export_result['file_path']}",
            f"   File Size: {file_size_bytes:,} bytes ({file_size_mb:.2f} MB)"
        ]
        
        return "\n".join(output_lines)
        
    except Exception as e:
        logger.error(f"Error exporting process app: {e}", exc_info=True)
        return format_error(e, "export_process_app")


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("IBM BAW MCP Server - Production Version")
    logger.info("=" * 60)
    logger.info(f"Configuration loaded from: .env")
    logger.info(f"Server URL: {config.cp4ba_base_url}")
    logger.info(f"Log Level: {config.log_level}")
    logger.info("=" * 60)
    
    try:
        # Run the MCP server
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # Cleanup
        if _client:
            _client.close()
        if _authenticator:
            _authenticator.close()
        logger.info("Server stopped")

# Made with Bob
