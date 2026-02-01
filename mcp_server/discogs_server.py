#!/usr/bin/env python3
"""
Discogs MCP Server - Provides tools for interacting with the Discogs API.

This MCP server exposes tools to search, browse, and manage Discogs collections
using the local DiscogsHttpClient implementation. All tools return markdown-formatted
responses for better readability.
"""

import sys
import os
import asyncio
from typing import Any, Dict, List, Optional

# Add parent directory to path to import musicagent
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio

from src.musicagent.client.http_client import DiscogsHTTPClient
from src.musicagent.config.settings import settings


# Initialize Discogs client (will be reused across requests)
_client: Optional[DiscogsHTTPClient] = None


def get_client() -> DiscogsHTTPClient:
    """Get or create the Discogs HTTP client."""
    global _client
    if _client is None:
        _client = DiscogsHTTPClient()
    return _client


def format_collection_releases(data: Dict[str, Any]) -> str:
    """
    Format collection releases as markdown.
    
    Args:
        data: Collection releases data from Discogs API
        
    Returns:
        Markdown formatted string
    """
    md = []
    md.append("# Your Discogs Collection\n")
    
    if 'pagination' in data:
        pagination = data['pagination']
        md.append(f"**Total Items:** {pagination.get('items', 0)}")
        md.append(f"**Page:** {pagination.get('page', 1)} of {pagination.get('pages', 1)}")
        md.append(f"**Per Page:** {pagination.get('per_page', 0)}\n")
    
    if 'releases' in data:
        releases = data['releases']
        md.append("## Releases\n")
        
        for idx, item in enumerate(releases, 1):
            release_info = item.get('basic_information', {})
            title = release_info.get('title', 'Unknown Title')
            artists = release_info.get('artists', [])
            artist_names = ', '.join([a.get('name', 'Unknown') for a in artists])
            year = release_info.get('year', 'N/A')
            release_id = release_info.get('id', 'N/A')
            formats = release_info.get('formats', [])
            format_str = ', '.join([f"{fmt.get('name', 'Unknown')} ({fmt.get('qty', 1)})" for fmt in formats]) if formats else 'Unknown Format'
            
            md.append(f"### {idx}. {artist_names} - {title}")
            md.append(f"- **Year:** {year}")
            md.append(f"- **Release ID:** {release_id}")
            md.append(f"- **Format:** {format_str}")
            
            if 'labels' in release_info and release_info['labels']:
                label_names = ', '.join([l.get('name', 'Unknown') for l in release_info['labels']])
                md.append(f"- **Label:** {label_names}")
            
            if 'date_added' in item:
                md.append(f"- **Date Added:** {item['date_added']}")
            
            md.append("")
    
    return "\n".join(md)


def format_search_results(data: Dict[str, Any], search_type: str = "general") -> str:
    """
    Format search results as markdown.
    
    Args:
        data: Search results from Discogs API
        search_type: Type of search performed
        
    Returns:
        Markdown formatted string
    """
    md = []
    md.append(f"# Discogs {search_type.title()} Search Results\n")
    
    if 'pagination' in data:
        pagination = data['pagination']
        md.append(f"**Total Results:** {pagination.get('items', 0)}")
        md.append(f"**Page:** {pagination.get('page', 1)} of {pagination.get('pages', 1)}\n")
    
    if 'results' in data and data['results']:
        results = data['results']
        
        for idx, result in enumerate(results, 1):
            title = result.get('title', 'Unknown')
            result_type = result.get('type', 'Unknown')
            result_id = result.get('id', 'N/A')
            
            md.append(f"### {idx}. {title}")
            md.append(f"- **Type:** {result_type}")
            md.append(f"- **ID:** {result_id}")
            
            if 'country' in result and result['country']:
                md.append(f"- **Country:** {result['country']}")
            
            if 'year' in result and result['year']:
                md.append(f"- **Year:** {result['year']}")
            
            if 'genre' in result and result['genre']:
                md.append(f"- **Genre:** {', '.join(result['genre'])}")
            
            if 'style' in result and result['style']:
                md.append(f"- **Style:** {', '.join(result['style'])}")
            
            if 'label' in result and result['label']:
                labels = ', '.join(result['label']) if isinstance(result['label'], list) else result['label']
                md.append(f"- **Label:** {labels}")
            
            if 'format' in result and result['format']:
                formats = ', '.join(result['format']) if isinstance(result['format'], list) else result['format']
                md.append(f"- **Format:** {formats}")
            
            if 'thumb' in result and result['thumb']:
                md.append(f"- **Thumbnail:** {result['thumb']}")
            
            md.append("")
    else:
        md.append("_No results found._")
    
    return "\n".join(md)


def format_list_creation(data: Dict[str, Any]) -> str:
    """
    Format list creation response as markdown.
    
    Args:
        data: Response from list creation API
        
    Returns:
        Markdown formatted string
    """
    md = []
    md.append("# List Created Successfully\n")
    
    if 'id' in data:
        md.append(f"**List ID:** {data['id']}")
    
    if 'name' in data:
        md.append(f"**Name:** {data['name']}")
    
    if 'description' in data:
        md.append(f"**Description:** {data['description']}")
    
    if 'public' in data:
        md.append(f"**Public:** {data['public']}")
    
    if 'resource_url' in data:
        md.append(f"**Resource URL:** {data['resource_url']}")
    
    return "\n".join(md)


def format_add_to_collection(data: Dict[str, Any], release_id: int) -> str:
    """
    Format add to collection response as markdown.
    
    Args:
        data: Response from add to collection API
        release_id: The release ID that was added
        
    Returns:
        Markdown formatted string
    """
    md = []
    md.append("# Release Added to Collection\n")
    md.append(f"**Release ID:** {release_id}")
    
    if 'instance_id' in data:
        md.append(f"**Instance ID:** {data['instance_id']}")
    
    if 'rating' in data:
        md.append(f"**Rating:** {data['rating']}")
    
    if 'folder_id' in data:
        md.append(f"**Folder ID:** {data['folder_id']}")
    
    if 'resource_url' in data:
        md.append(f"**Resource URL:** {data['resource_url']}")
    
    md.append("\n✅ Successfully added to your collection!")
    
    return "\n".join(md)


# Create the MCP server
app = Server("discogs-server")


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available Discogs tools."""
    return [
        Tool(
            name="get_collection_releases",
            description="""Get all releases in your Discogs collection. This tool retrieves your personal collection 
            of releases with pagination support. Returns a markdown-formatted list showing artist, title, format, 
            year, label, and date added for each release. Useful for browsing your collection or finding specific 
            items you own.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "Your Discogs username"
                    },
                    "page": {
                        "type": "number",
                        "description": "Page number for pagination (default: 1)",
                        "default": 1
                    },
                    "per_page": {
                        "type": "number",
                        "description": "Number of items per page (max 100, default: 50)",
                        "default": 50
                    },
                    "sort": {
                        "type": "string",
                        "description": "Sort field (e.g., 'artist', 'title', 'year', 'added')",
                        "default": "added"
                    },
                    "sort_order": {
                        "type": "string",
                        "description": "Sort order: 'asc' or 'desc'",
                        "enum": ["asc", "desc"],
                        "default": "desc"
                    }
                },
                "required": ["username"]
            }
        ),
        Tool(
            name="add_release_to_collection",
            description="""Add a release to your Discogs collection. Provide the release ID of the item you want 
            to add. You can optionally specify which folder to add it to (default is folder 1 - 'Uncategorized'). 
            Returns confirmation with the instance ID and collection details in markdown format. This is useful 
            when you discover a release through search and want to add it to your personal collection.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "Your Discogs username"
                    },
                    "release_id": {
                        "type": "number",
                        "description": "The Discogs release ID to add to your collection"
                    },
                    "folder_id": {
                        "type": "number",
                        "description": "Collection folder ID (1 = Uncategorized, default: 1)",
                        "default": 1
                    }
                },
                "required": ["username", "release_id"]
            }
        ),
        Tool(
            name="create_user_list",
            description="""Create a new custom list for organizing releases in your Discogs account. Lists can be 
            used to group releases thematically (e.g., 'Favorites', 'To Sell', 'Summer Vibes'). Specify a name and 
            optional description. You can set the list as public or private. Returns the created list details including 
            the list ID in markdown format. After creating a list, you can add items to it using the Discogs web interface.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "Your Discogs username"
                    },
                    "name": {
                        "type": "string",
                        "description": "Name for the new list"
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional description for the list",
                        "default": ""
                    },
                    "public": {
                        "type": "boolean",
                        "description": "Whether the list should be public (default: true)",
                        "default": True
                    }
                },
                "required": ["username", "name"]
            }
        ),
        Tool(
            name="search_by_artist",
            description="""Search the Discogs database for releases by a specific artist name. This searches across 
            the entire Discogs database (not just your collection). Returns a markdown-formatted list of matching 
            releases, artists, and related items showing title, year, format, label, and other details. Great for 
            discovering an artist's discography or finding specific releases. Use this when you want to explore 
            what music an artist has released.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "artist_name": {
                        "type": "string",
                        "description": "The artist name to search for"
                    },
                    "page": {
                        "type": "number",
                        "description": "Page number for pagination (default: 1)",
                        "default": 1
                    },
                    "per_page": {
                        "type": "number",
                        "description": "Number of results per page (max 100, default: 50)",
                        "default": 50
                    }
                },
                "required": ["artist_name"]
            }
        ),
        Tool(
            name="search_by_title",
            description="""Search the Discogs database by song or album title. This searches for releases with 
            matching titles across the entire database. Returns a markdown-formatted list showing matching releases 
            with details like artist, year, format, and label. Useful when you remember the title of a release but 
            not the artist, or when searching for different versions/pressings of the same album. The search looks 
            for titles containing your query.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "The song or album title to search for"
                    },
                    "page": {
                        "type": "number",
                        "description": "Page number for pagination (default: 1)",
                        "default": 1
                    },
                    "per_page": {
                        "type": "number",
                        "description": "Number of results per page (max 100, default: 50)",
                        "default": 50
                    }
                },
                "required": ["title"]
            }
        ),
        Tool(
            name="search_by_genre",
            description="""Search the Discogs database filtered by genre. Returns releases that match the specified 
            genre (e.g., 'Rock', 'Jazz', 'Electronic', 'Hip Hop', 'Classical'). Results are in markdown format 
            showing title, artist, year, format, and style details. This is perfect for discovering music within 
            a specific genre or exploring what's available in your favorite musical category. You can combine this 
            with pagination to browse through large result sets.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "genre": {
                        "type": "string",
                        "description": "The genre to filter by (e.g., 'Rock', 'Jazz', 'Electronic', 'Hip Hop')"
                    },
                    "page": {
                        "type": "number",
                        "description": "Page number for pagination (default: 1)",
                        "default": 1
                    },
                    "per_page": {
                        "type": "number",
                        "description": "Number of results per page (max 100, default: 50)",
                        "default": 50
                    }
                },
                "required": ["genre"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Handle tool calls."""
    client = get_client()
    
    try:
        if name == "get_collection_releases":
            username = arguments["username"]
            page = arguments.get("page", 1)
            per_page = arguments.get("per_page", 50)
            sort = arguments.get("sort", "added")
            sort_order = arguments.get("sort_order", "desc")
            
            # Get collection releases
            response = client.get(
                f"users/{username}/collection/folders/0/releases",
                params={
                    "page": page,
                    "per_page": min(per_page, 100),
                    "sort": sort,
                    "sort_order": sort_order
                }
            )
            
            markdown_output = format_collection_releases(response)
            return [TextContent(type="text", text=markdown_output)]
        
        elif name == "add_release_to_collection":
            username = arguments["username"]
            release_id = arguments["release_id"]
            folder_id = arguments.get("folder_id", 1)
            
            # Add release to collection
            response = client.post(
                f"users/{username}/collection/folders/{folder_id}/releases/{release_id}"
            )
            
            markdown_output = format_add_to_collection(response, release_id)
            return [TextContent(type="text", text=markdown_output)]
        
        elif name == "create_user_list":
            username = arguments["username"]
            name_arg = arguments["name"]
            description = arguments.get("description", "")
            public = arguments.get("public", True)
            
            # Create list
            response = client.post(
                f"users/{username}/lists",
                json={
                    "name": name_arg,
                    "description": description,
                    "public": public
                }
            )
            
            markdown_output = format_list_creation(response)
            return [TextContent(type="text", text=markdown_output)]
        
        elif name == "search_by_artist":
            artist_name = arguments["artist_name"]
            page = arguments.get("page", 1)
            per_page = arguments.get("per_page", 50)
            
            # Search by artist
            response = client.get(
                "database/search",
                params={
                    "q": artist_name,
                    "type": "artist",
                    "page": page,
                    "per_page": min(per_page, 100)
                }
            )
            
            markdown_output = format_search_results(response, "artist")
            return [TextContent(type="text", text=markdown_output)]
        
        elif name == "search_by_title":
            title = arguments["title"]
            page = arguments.get("page", 1)
            per_page = arguments.get("per_page", 50)
            
            # Search by title
            response = client.get(
                "database/search",
                params={
                    "q": title,
                    "type": "release",
                    "page": page,
                    "per_page": min(per_page, 100)
                }
            )
            
            markdown_output = format_search_results(response, "title")
            return [TextContent(type="text", text=markdown_output)]
        
        elif name == "search_by_genre":
            genre = arguments["genre"]
            page = arguments.get("page", 1)
            per_page = arguments.get("per_page", 50)
            
            # Search by genre
            response = client.get(
                "database/search",
                params={
                    "genre": genre,
                    "page": page,
                    "per_page": min(per_page, 100)
                }
            )
            
            markdown_output = format_search_results(response, f"genre '{genre}'")
            return [TextContent(type="text", text=markdown_output)]
        
        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]
            
    except Exception as e:
        error_msg = f"# Error\n\nAn error occurred while executing the tool:\n\n```\n{type(e).__name__}: {str(e)}\n```"
        return [TextContent(type="text", text=error_msg)]


async def main():
    """Main entry point for the MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
