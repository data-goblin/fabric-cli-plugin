#!/usr/bin/env python3
"""
Build Power BI Modeling MCP bundle (.mcpb) from VS Marketplace VSIX.

This script:
1. Checks VS Marketplace for the latest version
2. Downloads the VSIX if newer than current
3. Extracts and repackages as .mcpb for Claude Desktop
"""

import gzip
import json
import os
import shutil
import tempfile
import zipfile
from pathlib import Path

import requests

# Configuration
EXTENSION_ID = "analysis-services.powerbi-modeling-mcp"
PUBLISHER = "analysis-services"
EXTENSION_NAME = "powerbi-modeling-mcp"
OUTPUT_DIR = Path("claude-desktop")
OUTPUT_FILE = OUTPUT_DIR / "powerbi-modeling-mcp.mcpb"
VERSION_FILE = Path(".powerbi-modeling-mcp-version")

# VS Marketplace API
MARKETPLACE_API = "https://marketplace.visualstudio.com/_apis/public/gallery/extensionquery"
VSIX_URL_TEMPLATE = "https://marketplace.visualstudio.com/_apis/public/gallery/publishers/{publisher}/vsextensions/{name}/{version}/vspackage"

# Platform targets to check (add darwin-arm64, darwin-x64 when available)
PLATFORMS = {
    "win32-x64": {
        "url_param": "?targetPlatform=win32-x64",
        "binary_name": "powerbi-modeling-mcp.exe",
    },
    # Uncomment when Mac support is released:
    # "darwin-arm64": {
    #     "url_param": "?targetPlatform=darwin-arm64",
    #     "binary_name": "powerbi-modeling-mcp",
    # },
    # "darwin-x64": {
    #     "url_param": "?targetPlatform=darwin-x64",
    #     "binary_name": "powerbi-modeling-mcp",
    # },
}


def get_latest_version() -> str:
    """Query VS Marketplace for the latest extension version."""
    payload = {
        "filters": [{"criteria": [{"filterType": 7, "value": EXTENSION_ID}]}],
        "flags": 914,
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json;api-version=3.0-preview.1",
    }

    response = requests.post(MARKETPLACE_API, json=payload, headers=headers)
    response.raise_for_status()

    data = response.json()
    version = data["results"][0]["extensions"][0]["versions"][0]["version"]
    return version


def get_current_version() -> str | None:
    """Read the currently installed version from version file."""
    if VERSION_FILE.exists():
        return VERSION_FILE.read_text().strip()
    return None


def download_vsix(version: str, platform: str, platform_config: dict) -> Path | None:
    """Download VSIX for a specific platform."""
    url = VSIX_URL_TEMPLATE.format(
        publisher=PUBLISHER, name=EXTENSION_NAME, version=version
    )
    url += platform_config["url_param"]

    print(f"Downloading {platform} VSIX from {url}")
    response = requests.get(url, stream=True)

    # Check if platform is supported
    if response.status_code == 404:
        print(f"  Platform {platform} not available")
        return None

    # Check for JSON error response
    content_type = response.headers.get("content-type", "")
    if "application/json" in content_type:
        error = response.json()
        print(f"  Platform {platform} not available: {error.get('message', 'Unknown error')}")
        return None

    response.raise_for_status()

    # Save to temp file
    temp_path = Path(tempfile.mktemp(suffix=".vsix.gz"))
    with open(temp_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    return temp_path


def extract_vsix(vsix_path: Path, output_dir: Path) -> Path:
    """Extract VSIX to directory (handles both gzipped and plain zip)."""
    # Check if gzipped by reading magic bytes
    with open(vsix_path, "rb") as f:
        magic = f.read(2)

    if magic == b'\x1f\x8b':  # Gzip magic bytes
        # Decompress gzip first
        decompressed_path = vsix_path.with_suffix(".vsix")
        with gzip.open(vsix_path, "rb") as f_in:
            with open(decompressed_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        vsix_path.unlink()
        vsix_path = decompressed_path

    # Extract zip
    with zipfile.ZipFile(vsix_path, "r") as z:
        z.extractall(output_dir)

    # Cleanup
    vsix_path.unlink()

    return output_dir


def create_manifest(version: str, platforms: list[str]) -> dict:
    """Create mcpb manifest.json."""
    # Determine command based on platform
    if "win32-x64" in platforms:
        command = "${__dirname}/server/powerbi-modeling-mcp.exe"
    else:
        command = "${__dirname}/server/powerbi-modeling-mcp"

    return {
        "manifest_version": "0.3",
        "name": "powerbi-modeling-mcp",
        "display_name": "Power BI Modeling MCP",
        "version": version,
        "description": "MCP server for Power BI semantic model operations - create, modify, and query Power BI models with AI",
        "long_description": (
            "The Power BI Modeling MCP Server brings Power BI semantic modeling capabilities to your AI agents. "
            "Build and modify semantic models with natural language, execute bulk operations at scale, "
            "apply modeling best practices, and run DAX queries against your models."
        ),
        "author": {
            "name": "Microsoft",
            "url": "https://github.com/microsoft/powerbi-modeling-mcp",
        },
        "license": "MIT",
        "homepage": "https://github.com/microsoft/powerbi-modeling-mcp",
        "keywords": [
            "powerbi",
            "dax",
            "semantic-model",
            "analysis-services",
            "tabular",
            "mcp",
            "fabric",
        ],
        "server": {
            "type": "binary",
            "entry_point": "server/powerbi-modeling-mcp.exe",
            "mcp_config": {
                "command": command,
                "args": ["--start", "--skipconfirmation"],
                "env": {},
            },
        },
    }


def build_mcpb(version: str) -> bool:
    """Build the mcpb bundle."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        bundle_dir = temp_path / "bundle"
        bundle_dir.mkdir()

        available_platforms = []

        for platform, config in PLATFORMS.items():
            print(f"\nProcessing {platform}...")

            # Download VSIX
            vsix_path = download_vsix(version, platform, config)
            if vsix_path is None:
                continue

            # Extract VSIX
            extract_dir = temp_path / f"extract-{platform}"
            extract_vsix(vsix_path, extract_dir)

            # Copy server files
            server_src = extract_dir / "extension" / "server"
            server_dst = bundle_dir / "server"

            if server_src.exists():
                if server_dst.exists():
                    # Merge server directories for multi-platform
                    for item in server_src.iterdir():
                        dst_item = server_dst / item.name
                        if not dst_item.exists():
                            if item.is_dir():
                                shutil.copytree(item, dst_item)
                            else:
                                shutil.copy2(item, dst_item)
                else:
                    shutil.copytree(server_src, server_dst)

                available_platforms.append(platform)
                print(f"  Added {platform} server files")

        if not available_platforms:
            print("ERROR: No platforms available")
            return False

        # Create manifest
        manifest = create_manifest(version, available_platforms)
        manifest_path = bundle_dir / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)
        print(f"\nCreated manifest.json")

        # Package as mcpb (zip)
        OUTPUT_DIR.mkdir(exist_ok=True)
        with zipfile.ZipFile(OUTPUT_FILE, "w", zipfile.ZIP_DEFLATED) as z:
            for file_path in bundle_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(bundle_dir)
                    z.write(file_path, arcname)

        print(f"\nCreated {OUTPUT_FILE}")

        # Update version file
        VERSION_FILE.write_text(version)

        return True


def set_output(name: str, value: str):
    """Set GitHub Actions output."""
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"{name}={value}\n")
    print(f"Output: {name}={value}")


def main():
    print("=" * 60)
    print("Power BI Modeling MCP Bundle Builder")
    print("=" * 60)

    # Check latest version
    print("\nChecking VS Marketplace for latest version...")
    latest_version = get_latest_version()
    print(f"Latest version: {latest_version}")

    # Check current version
    current_version = get_current_version()
    print(f"Current version: {current_version or 'None'}")

    # Check if update needed
    force_update = os.environ.get("FORCE_UPDATE", "false").lower() == "true"
    if current_version == latest_version and not force_update:
        print("\nAlready up to date!")
        set_output("updated", "false")
        return

    print(f"\nUpdating to version {latest_version}...")

    # Build mcpb
    success = build_mcpb(latest_version)

    if success:
        print("\n" + "=" * 60)
        print(f"Successfully built mcpb for version {latest_version}")
        print("=" * 60)
        set_output("updated", "true")
        set_output("version", latest_version)
    else:
        print("\nBuild failed!")
        set_output("updated", "false")
        exit(1)


if __name__ == "__main__":
    main()
