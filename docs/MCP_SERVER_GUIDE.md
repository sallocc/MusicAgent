# Discogs MCP Server Integration Guide

This guide explains how to use the Discogs MCP server that interfaces with your DiscogsHttpClient for AI tools and workflows.

## Overview

The Discogs MCP server provides 6 powerful tools for interacting with the Discogs API, all returning beautifully formatted Markdown responses instead of raw JSON.

## Server Location

The MCP server is located at: [`mcp_server/discogs_server.py`](../mcp_server/discogs_server.py)

## Available Tools

### 1. `get_collection_releases`

Get all releases in your Discogs collection with pagination support.

**Example Usage:**
```
Get my collection sorted by artist name in ascending order
```

**Parameters:**
- `username` (required): Your Discogs username
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page, max 100 (default: 50)
- `sort` (optional): Sort field - 'artist', 'title', 'year', 'added' (default: 'added')
- `sort_order` (optional): 'asc' or 'desc' (default: 'desc')

**Returns:** Markdown-formatted list with:
- Artist and title
- Year and format
- Label information
- Date added to collection

---

### 2. `add_release_to_collection`

Add a release to your Discogs collection.

**Example Usage:**
```
Add release ID 123456 to my collection
```

**Parameters:**
- `username` (required): Your Discogs username
- `release_id` (required): The Discogs release ID to add
- `folder_id` (optional): Collection folder ID (default: 1 - Uncategorized)

**Returns:** Markdown confirmation with:
- Release ID added
- Instance ID
- Folder information

---

### 3. `create_user_list`

Create a custom list for organizing releases.

**Example Usage:**
```
Create a public list called "Jazz Favorites" with description "My favorite jazz albums"
```

**Parameters:**
- `username` (required): Your Discogs username
- `name` (required): Name for the new list
- `description` (optional): Description for the list
- `public` (optional): Whether the list should be public (default: true)

**Returns:** Markdown details including:
- List ID
- Name and description
- Public/private status
- Resource URL

---

### 4. `search_by_artist`

Search the Discogs database for releases by artist name.

**Example Usage:**
```
Search for Miles Davis releases
```

**Parameters:**
- `artist_name` (required): The artist name to search for
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Results per page, max 100 (default: 50)

**Returns:** Markdown-formatted search results with:
- Title and artist
- Release type and ID
- Year and country
- Genre, style, format
- Label and thumbnail

---

### 5. `search_by_title`

Search the Discogs database by song or album title.

**Example Usage:**
```
Search for "Kind of Blue" album
```

**Parameters:**
- `title` (required): The song or album title to search for
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Results per page, max 100 (default: 50)

**Returns:** Markdown-formatted search results with complete release details

---

### 6. `search_by_genre`

Search the Discogs database filtered by genre.

**Example Usage:**
```
Find Jazz releases in the Discogs database
```

**Parameters:**
- `genre` (required): The genre to filter by (e.g., 'Rock', 'Jazz', 'Electronic', 'Hip Hop', 'Classical')
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Results per page, max 100 (default: 50)

**Returns:** Markdown-formatted genre-filtered results

---

## Setup Instructions

### 1. Prerequisites

Ensure you have a Discogs API token configured in your `.env` file:

```env
DISCOGS_API_TOKEN=your_token_here
DISCOGS_USER_AGENT=YourAppName/1.0
```

### 2. Installation

The MCP server is already configured in your MCP settings at:
```
c:/Users/simon/AppData/Roaming/Code/User/globalStorage/rooveterinaryinc.roo-cline/settings/mcp_settings.json
```

Configuration:
```json
{
  "mcpServers": {
    "discogs": {
      "command": "python",
      "args": ["c:/Users/simon/OneDrive/Post-School/Music Agent/MusicAgent/mcp_server/discogs_server.py"],
      "disabled": false,
      "alwaysAllow": [],
      "disabledTools": []
    }
  }
}
```

### 3. Verify Installation

After restarting your IDE or reloading the MCP servers, you should see the Discogs server listed in the "Connected MCP Servers" section with all 6 tools available.

## Example Workflows

### Building Your Collection

1. **Discover new music:**
   ```
   Search for Electronic genre releases
   ```

2. **Find specific release:**
   ```
   Search for artist "Daft Punk"
   ```

3. **Add to collection:**
   ```
   Add release ID 123456 to my collection
   ```

4. **Organize with lists:**
   ```
   Create a list called "Electronic Favorites"
   ```

### Exploring Your Collection

1. **Browse collection:**
   ```
   Get my collection sorted by date added
   ```

2. **Find specific items:**
   ```
   Get my collection sorted by artist ascending
   ```

## Integration with AI Workflows

The MCP server can be used by AI assistants to:

- **Music Discovery**: "Find me some Jazz albums from the 1960s"
- **Collection Management**: "Add the top-rated Miles Davis albums to my collection"
- **Data Analysis**: "What genres are most represented in my collection?"
- **Recommendations**: "Find releases similar to albums in my collection"

## Architecture

```
AI Tool/Workflow
       ↓
   MCP Server (discogs_server.py)
       ↓
   DiscogsHTTPClient (http_client.py)
       ↓
   Discogs API
```

The server:
1. Receives tool calls via MCP protocol
2. Uses the existing [`DiscogsHTTPClient`](../src/musicagent/client/http_client.py) for all API interactions
3. Leverages built-in rate limiting, authentication, and error handling
4. Formats responses as Markdown for readability

## Benefits

### ✅ Markdown Formatting
- Human-readable output
- Easy to display in chat interfaces
- Better for AI processing and understanding

### ✅ Integrated Error Handling
- Uses existing MusicAgent error handling
- Clear error messages in Markdown format
- Graceful degradation on failures

### ✅ Rate Limit Protection
- Automatic rate limiting via DiscogsHTTPClient
- Prevents API throttling
- Configurable limits

### ✅ Comprehensive Logging
- All requests logged via MusicAgent logger
- Performance metrics tracked
- Error tracking and debugging support

## Troubleshooting

### Server Not Starting

**Issue:** Server doesn't appear in connected MCP servers

**Solutions:**
1. Verify Python is in your PATH
2. Check that the MCP package is installed: `pip install mcp`
3. Ensure the MusicAgent package is installed: `pip install -e .`
4. Verify the `.env` file has your Discogs API token
5. Restart your IDE

### Authentication Errors

**Issue:** "Discogs API token is required" error

**Solutions:**
1. Check your `.env` file has `DISCOGS_API_TOKEN` set
2. Verify the token is valid on Discogs.com
3. Ensure the `.env` file is in the project root directory

### Rate Limit Errors

**Issue:** "Rate limit exceeded" errors

**Solutions:**
1. The server automatically handles rate limiting
2. Wait a minute before retrying
3. Reduce `per_page` parameters to make fewer requests
4. Adjust `RATE_LIMIT_REQUESTS` in settings if needed

## Further Documentation

- **MCP Server README**: [`mcp_server/README.md`](../mcp_server/README.md)
- **DiscogsHTTPClient**: [`src/musicagent/client/http_client.py`](../src/musicagent/client/http_client.py)
- **API Settings**: [`src/musicagent/config/settings.py`](../src/musicagent/config/settings.py)
- **Main Project README**: [`README.md`](../README.md)

## Contributing

To add new tools to the MCP server:

1. Add the tool definition in `list_tools()`
2. Add the tool handler in `call_tool()`
3. Create a formatting function for Markdown output
4. Update this documentation

## License

Part of the MusicAgent project - see main LICENSE file.
