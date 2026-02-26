"""
MCP Server for Discogs API integration.

This module provides an MCP (Model Context Protocol) server that exposes
Discogs API functionality through standardized tools for collection management
and database searching.
"""

import json
import os
from typing import Any, Dict, Optional

from mcp.server import Server
from mcp.types import Tool, TextContent

from src.musicagent.client.http_client import DiscogsHTTPClient


# Initialize the MCP server
app = Server("discogs")


def get_client() -> DiscogsHTTPClient:
    """Get or create a DiscogsHTTPClient instance."""
    return DiscogsHTTPClient()


def format_release_markdown(releases: list[Dict[str, Any]]) -> str:
    """Format releases as markdown for readability."""
    if not releases:
        return "No releases found."
    
    lines = []
    for release in releases:
        basic_info = release.get("basic_information", {})
        artist_name = ", ".join([a.get("name", "Unknown") for a in basic_info.get("artists", [])])
        title = basic_info.get("title", "Unknown")
        year = basic_info.get("year", "N/A")
        formats = basic_info.get("formats", [])
        format_str = ", ".join([f.get("name", "Unknown") for f in formats]) if formats else "N/A"
        labels = basic_info.get("labels", [])
        label_str = ", ".join([l.get("name", "Unknown") for l in labels]) if labels else "N/A"
        date_added = release.get("date_added", "N/A")
        release_id = release.get("id", "N/A")
        
        lines.append(f"**{artist_name} - {title}**")
        lines.append(f"- Release ID: {release_id}")
        lines.append(f"- Year: {year}")
        lines.append(f"- Format: {format_str}")
        lines.append(f"- Label: {label_str}")
        lines.append(f"- Date Added: {date_added}")
        lines.append("")
    
    return "\n".join(lines)


def format_search_results_markdown(results: list[Dict[str, Any]]) -> str:
    """Format search results as markdown for readability."""
    if not results:
        return "No results found."
    
    lines = []
    for item in results:
        title = item.get("title", "Unknown")
        item_type = item.get("type", "Unknown")
        year = item.get("year", "N/A")
        formats = item.get("format", [])
        format_str = ", ".join(formats) if formats else "N/A"
        labels = item.get("label", [])
        label_str = ", ".join(labels) if labels else "N/A"
        country = item.get("country", "N/A")
        item_id = item.get("id", "N/A")
        genre = ", ".join(item.get("genre", [])) if item.get("genre") else "N/A"
        style = ", ".join(item.get("style", [])) if item.get("style") else "N/A"
        
        lines.append(f"**{title}**")
        lines.append(f"- ID: {item_id}")
        lines.append(f"- Type: {item_type}")
        lines.append(f"- Year: {year}")
        lines.append(f"- Format: {format_str}")
        lines.append(f"- Label: {label_str}")
        lines.append(f"- Country: {country}")
        lines.append(f"- Genre: {genre}")
        lines.append(f"- Style: {style}")
        lines.append("")
    
    return "\n".join(lines)


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available Discogs API tools."""
    return [
        Tool(
            name="get_collection_releases",
            description=(
                "Get all releases in your Discogs collection. This tool retrieves your personal collection "
                "of releases with pagination support. Returns a markdown-formatted list showing artist, title, format, "
                "year, label, and date added for each release. Useful for browsing your collection or finding specific "
                "items you own. By default the user's username is simonallocca6."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "Your Discogs username",
                    },
                    "page": {
                        "type": "number",
                        "description": "Page number for pagination (default: 1)",
                        "default": 1,
                    },
                    "per_page": {
                        "type": "number",
                        "description": "Number of items per page (max 100, default: 50)",
                        "default": 50,
                    },
                    "sort": {
                        "type": "string",
                        "description": "Sort field (e.g., 'artist', 'title', 'year', 'added')",
                        "default": "added",
                    },
                    "sort_order": {
                        "type": "string",
                        "description": "Sort order: 'asc' or 'desc'",
                        "enum": ["asc", "desc"],
                        "default": "desc",
                    },
                },
                "required": ["username"],
            },
        ),
        Tool(
            name="add_release_to_collection",
            description=(
                "Add a release to your Discogs collection. Provide the release ID of the item you want "
                "to add. You can optionally specify which folder to add it to (default is folder 1 - 'Uncategorized'). "
                "Returns confirmation with the instance ID and collection details in markdown format. This is useful "
                "when you discover a release through search and want to add it to your personal collection."
                "\nBy default the user's username is simonallocca6."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "Your Discogs username",
                    },
                    "release_id": {
                        "type": "number",
                        "description": "The Discogs release ID to add to your collection",
                    },
                    "folder_id": {
                        "type": "number",
                        "description": "Collection folder ID (1 = Uncategorized, default: 1)",
                        "default": 1,
                    },
                },
                "required": ["username", "release_id"],
            },
        ),
        Tool(
            name="create_collection_folder",
            description=(
                "Create a new folder in your Discogs collection to organize your releases. Collection folders"
                "\nhelp you categorize your music (e.g., 'Vinyl', 'CDs', 'Want List', 'For Sale'). Specify a name for the folder."
                "\nReturns the created folder details including the folder ID in markdown format. After creating a folder, you can"
                "\nadd releases to it using the add_release_to_collection tool by specifying the folder_id parameter."  
                "\nBy default the user's username is simonallocca6."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "Your Discogs username",
                    },
                    "name": {
                        "type": "string",
                        "description": "Name for the new collection folder",
                    },
                },
                "required": ["username", "name"],
            },
        ),
        Tool(
            name="search_by_artist",
            description=(
                "Search the Discogs database for releases by a specific artist name. This searches across "
                "the entire Discogs database (not just your collection). Returns a markdown-formatted list of matching "
                "releases, artists, and related items showing title, year, format, label, and other details. Great for "
                "discovering an artist's discography or finding specific releases. Use this when you want to explore "
                "what music an artist has released."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "artist_name": {
                        "type": "string",
                        "description": "The artist name to search for",
                    },
                    "page": {
                        "type": "number",
                        "description": "Page number for pagination (default: 1)",
                        "default": 1,
                    },
                    "per_page": {
                        "type": "number",
                        "description": "Number of results per page (max 100, default: 50)",
                        "default": 50,
                    },
                },
                "required": ["artist_name"],
            },
        ),
        Tool(
            name="search_by_title",
            description=(
                "Search the Discogs database by song or album title. This searches for releases with "
                "matching titles across the entire database. Returns a markdown-formatted list showing matching releases "
                "with details like artist, year, format, and label. Useful when you remember the title of a release but "
                "not the artist, or when searching for different versions/pressings of the same album. The search looks "
                "for titles containing your query."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "The song or album title to search for",
                    },
                    "page": {
                        "type": "number",
                        "description": "Page number for pagination (default: 1)",
                        "default": 1,
                    },
                    "per_page": {
                        "type": "number",
                        "description": "Number of results per page (max 100, default: 50)",
                        "default": 50,
                    },
                },
                "required": ["title"],
            },
        ),
        Tool(
            name="search_by_genre",
            description=(
                "Search the Discogs database filtered by genre. Returns releases that match the specified "
                "genre (e.g., 'Rock', 'Jazz', 'Electronic', 'Hip Hop', 'Classical'). Results are in markdown format "
                "showing title, artist, year, format, and style details. This is perfect for discovering music within "
                "a specific genre or exploring what's available in your favorite musical category. You can combine this "
                "with pagination to browse through large result sets."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "genre": {
                        "type": "string",
                        "description": "The genre to filter by (e.g., 'Rock', 'Jazz', 'Electronic', 'Hip Hop')",
                    },
                    "page": {
                        "type": "number",
                        "description": "Page number for pagination (default: 1)",
                        "default": 1,
                    },
                    "per_page": {
                        "type": "number",
                        "description": "Number of results per page (max 100, default: 50)",
                        "default": 50,
                    },
                },
                "required": ["genre"],
            },
        ),
        Tool(
            name="search_by_artist_and_title",
            description=(
                "Search the Discogs database by both artist name and song/album title. This provides more "
                "precise results when you know both the artist and title. Returns a markdown-formatted list showing "
                "matching releases with full details. Ideal for finding specific releases when you have both pieces of "
                "information, or for disambiguating titles that might appear across multiple artists. Combines artist "
                "and title filters for targeted search results."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "artist_name": {
                        "type": "string",
                        "description": "The artist name to search for",
                    },
                    "title": {
                        "type": "string",
                        "description": "The song or album title to search for",
                    },
                    "page": {
                        "type": "number",
                        "description": "Page number for pagination (default: 1)",
                        "default": 1,
                    },
                    "per_page": {
                        "type": "number",
                        "description": "Number of results per page (max 100, default: 50)",
                        "default": 50,
                    },
                },
                "required": ["artist_name", "title"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls for Discogs API operations."""
    
    try:
        client = get_client()
        
        if name == "get_collection_releases":
            username = arguments["username"]
            page = arguments.get("page", 1)
            per_page = arguments.get("per_page", 50)
            sort = arguments.get("sort", "added")
            sort_order = arguments.get("sort_order", "desc")
            
            endpoint = f"users/{username}/collection/folders/0/releases"
            params = {
                "page": page,
                "per_page": per_page,
                "sort": sort,
                "sort_order": sort_order,
            }
            
            response = client.get(endpoint, params=params)
            releases = response.get("releases", [])
            pagination = response.get("pagination", {})
            
            markdown = f"# Collection Releases for {username}\n\n"
            markdown += f"Page {pagination.get('page', 1)} of {pagination.get('pages', 1)} "
            markdown += f"({pagination.get('items', 0)} total items)\n\n"
            markdown += format_release_markdown(releases)
            
            return [
                TextContent(
                    type="text",
                    text=markdown,
                ),
                TextContent(
                    type="text",
                    text=f"\n\n**JSON Data:**\n```json\n{json.dumps(response, indent=2)}\n```",
                ),
            ]
        
        elif name == "add_release_to_collection":
            username = arguments["username"]
            release_id = arguments["release_id"]
            folder_id = arguments.get("folder_id", 1)
            
            endpoint = f"users/{username}/collection/folders/{folder_id}/releases/{release_id}"
            response = client.post(endpoint)
            
            instance_id = response.get("instance_id", "N/A")
            resource_url = response.get("resource_url", "N/A")
            
            markdown = f"# Release Added to Collection\n\n"
            markdown += f"**Instance ID:** {instance_id}\n"
            markdown += f"**Resource URL:** {resource_url}\n"
            markdown += f"**Release ID:** {release_id}\n"
            markdown += f"**Folder ID:** {folder_id}\n"
            markdown += f"**Username:** {username}\n"
            
            return [
                TextContent(
                    type="text",
                    text=markdown,
                ),
                TextContent(
                    type="text",
                    text=f"\n\n**JSON Data:**\n```json\n{json.dumps(response, indent=2)}\n```",
                ),
            ]
        
        elif name == "create_collection_folder":
            username = arguments["username"]
            folder_name = arguments["name"]
            
            endpoint = f"users/{username}/collection/folders"
            data = {"name": folder_name}
            response = client.post(endpoint, json=data)
            
            folder_id = response.get("id", "N/A")
            name = response.get("name", "N/A")
            count = response.get("count", 0)
            resource_url = response.get("resource_url", "N/A")
            
            markdown = f"# Collection Folder Created\n\n"
            markdown += f"**Folder ID:** {folder_id}\n"
            markdown += f"**Name:** {name}\n"
            markdown += f"**Item Count:** {count}\n"
            markdown += f"**Resource URL:** {resource_url}\n"
            markdown += f"**Username:** {username}\n"
            
            return [
                TextContent(
                    type="text",
                    text=markdown,
                ),
                TextContent(
                    type="text",
                    text=f"\n\n**JSON Data:**\n```json\n{json.dumps(response, indent=2)}\n```",
                ),
            ]
        
        elif name == "search_by_artist":
            artist_name = arguments["artist_name"]
            page = arguments.get("page", 1)
            per_page = arguments.get("per_page", 50)
            
            endpoint = "database/search"
            params = {
                "artist": artist_name,
                "page": page,
                "per_page": per_page,
            }
            
            response = client.get(endpoint, params=params)
            results = response.get("results", [])
            pagination = response.get("pagination", {})
            
            markdown = f"# Search Results for Artist: {artist_name}\n\n"
            markdown += f"Page {pagination.get('page', 1)} of {pagination.get('pages', 1)} "
            markdown += f"({pagination.get('items', 0)} total results)\n\n"
            markdown += format_search_results_markdown(results)
            
            return [
                TextContent(
                    type="text",
                    text=markdown,
                ),
                TextContent(
                    type="text",
                    text=f"\n\n**JSON Data:**\n```json\n{json.dumps(response, indent=2)}\n```",
                ),
            ]
        
        elif name == "search_by_title":
            title = arguments["title"]
            page = arguments.get("page", 1)
            per_page = arguments.get("per_page", 50)
            
            endpoint = "database/search"
            params = {
                "title": title,
                "page": page,
                "per_page": per_page,
            }
            
            response = client.get(endpoint, params=params)
            results = response.get("results", [])
            pagination = response.get("pagination", {})
            
            markdown = f"# Search Results for Title: {title}\n\n"
            markdown += f"Page {pagination.get('page', 1)} of {pagination.get('pages', 1)} "
            markdown += f"({pagination.get('items', 0)} total results)\n\n"
            markdown += format_search_results_markdown(results)
            
            return [
                TextContent(
                    type="text",
                    text=markdown,
                ),
                TextContent(
                    type="text",
                    text=f"\n\n**JSON Data:**\n```json\n{json.dumps(response, indent=2)}\n```",
                ),
            ]
        
        elif name == "search_by_genre":
            genre = arguments["genre"]
            page = arguments.get("page", 1)
            per_page = arguments.get("per_page", 50)
            
            endpoint = "database/search"
            params = {
                "genre": genre,
                "page": page,
                "per_page": per_page,
            }
            
            response = client.get(endpoint, params=params)
            results = response.get("results", [])
            pagination = response.get("pagination", {})
            
            markdown = f"# Search Results for Genre: {genre}\n\n"
            markdown += f"Page {pagination.get('page', 1)} of {pagination.get('pages', 1)} "
            markdown += f"({pagination.get('items', 0)} total results)\n\n"
            markdown += format_search_results_markdown(results)
            
            return [
                TextContent(
                    type="text",
                    text=markdown,
                ),
                TextContent(
                    type="text",
                    text=f"\n\n**JSON Data:**\n```json\n{json.dumps(response, indent=2)}\n```",
                ),
            ]
        
        elif name == "search_by_artist_and_title":
            artist_name = arguments["artist_name"]
            title = arguments["title"]
            page = arguments.get("page", 1)
            per_page = arguments.get("per_page", 50)
            
            endpoint = "database/search"
            params = {
                "artist": artist_name,
                "title": title,
                "page": page,
                "per_page": per_page,
            }
            
            response = client.get(endpoint, params=params)
            results = response.get("results", [])
            pagination = response.get("pagination", {})
            
            markdown = f"# Search Results for Artist: {artist_name}, Title: {title}\n\n"
            markdown += f"Page {pagination.get('page', 1)} of {pagination.get('pages', 1)} "
            markdown += f"({pagination.get('items', 0)} total results)\n\n"
            markdown += format_search_results_markdown(results)
            
            return [
                TextContent(
                    type="text",
                    text=markdown,
                ),
                TextContent(
                    type="text",
                    text=f"\n\n**JSON Data:**\n```json\n{json.dumps(response, indent=2)}\n```",
                ),
            ]
        
        else:
            return [
                TextContent(
                    type="text",
                    text=f"Unknown tool: {name}",
                )
            ]
    
    except Exception as e:
        return [
            TextContent(
                type="text",
                text=f"Error executing {name}: {str(e)}",
            )
        ]


async def main():
    """Run the MCP server."""
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
