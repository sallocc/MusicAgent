# Discogs MCP Server

A Model Context Protocol (MCP) server that provides tools for interacting with the Discogs API through the local DiscogsHttpClient.

## Features

This MCP server exposes 6 powerful tools for working with Discogs:

### 1. **get_collection_releases**
Retrieves all releases in your Discogs collection with pagination and sorting support.

**Use cases:**
- Browse your entire music collection
- Find specific items you own
- Sort by artist, title, year, or date added

**Parameters:**
- `username` (required): Your Discogs username
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page, max 100 (default: 50)
- `sort` (optional): Sort field - 'artist', 'title', 'year', 'added' (default: 'added')
- `sort_order` (optional): 'asc' or 'desc' (default: 'desc')

### 2. **add_release_to_collection**
Adds a release to your Discogs collection.

**Use cases:**
- Add newly discovered releases to your collection
- Build your collection programmatically
- Organize items into folders

**Parameters:**
- `username` (required): Your Discogs username
- `release_id` (required): The Discogs release ID to add
- `folder_id` (optional): Collection folder ID (default: 1 - Uncategorized)

### 3. **create_user_list**
Creates a custom list for organizing releases.

**Use cases:**
- Create thematic lists (e.g., "Favorites", "To Sell", "Summer Vibes")
- Organize your collection beyond standard folders
- Share curated lists with the community

**Parameters:**
- `username` (required): Your Discogs username
- `name` (required): Name for the new list
- `description` (optional): Description for the list
- `public` (optional): Whether the list should be public (default: true)

### 4. **search_by_artist**
Search the Discogs database for releases by artist name.

**Use cases:**
- Explore an artist's complete discography
- Find specific releases by an artist
- Discover collaborations and side projects

**Parameters:**
- `artist_name` (required): The artist name to search for
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Results per page, max 100 (default: 50)

### 5. **search_by_title**
Search the Discogs database by song or album title.

**Use cases:**
- Find releases when you remember the title but not the artist
- Search for different versions/pressings of the same album
- Discover covers and remixes

**Parameters:**
- `title` (required): The song or album title to search for
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Results per page, max 100 (default: 50)

### 6. **search_by_genre**
Search the Discogs database filtered by genre.

**Use cases:**
- Explore music within specific genres
- Discover new artists in your favorite genre
- Browse genre-specific releases

**Parameters:**
- `genre` (required): The genre to filter by (e.g., 'Rock', 'Jazz', 'Electronic', 'Hip Hop', 'Classical')
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Results per page, max 100 (default: 50)

## Output Format

All tools return data formatted in **Markdown**, not JSON objects. This makes the responses:
- More readable for humans
- Easier to parse and display in chat interfaces
- Better formatted for AI tools and workflows

## Setup

### Prerequisites

1. **Discogs API Token**: You need a Discogs API token set in your `.env` file:
   ```
   DISCOGS_API_TOKEN=your_token_here
   DISCOGS_USER_AGENT=YourAppName/1.0
   ```

2. **Python Dependencies**: The server uses the local MusicAgent package which must be installed:
   ```bash
   pip install -e .
   ```

3. **MCP Package**: The MCP SDK must be installed:
   ```bash
   pip install mcp
   ```

### Running the Server

The server runs via the MCP settings configuration. Add it to your MCP settings file:

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

### Testing the Server

Once configured, you can test the tools:

1. **Get your collection:**
   ```
   Use the get_collection_releases tool with your username
   ```

2. **Search for an artist:**
   ```
   Use the search_by_artist tool to find "Miles Davis"
   ```

3. **Search by genre:**
   ```
   Use the search_by_genre tool to explore "Jazz" releases
   ```

## Integration with Other Tools

This MCP server can be referenced and used by:
- AI assistants and chatbots
- Automation workflows
- Music discovery applications
- Collection management tools
- Any MCP-compatible client

## Architecture

The server:
1. Imports and uses the local [`DiscogsHTTPClient`](../src/musicagent/client/http_client.py)
2. Leverages existing authentication, rate limiting, and error handling
3. Formats all responses as Markdown for better readability
4. Provides comprehensive tool descriptions for AI understanding

## Error Handling

The server includes robust error handling:
- API errors are caught and returned as formatted Markdown
- Authentication issues are clearly reported
- Rate limit errors include relevant information
- Network errors are handled gracefully

## Rate Limiting

The server respects Discogs API rate limits through the underlying DiscogsHTTPClient:
- Default: 60 requests per minute
- Configurable via environment variables
- Automatic rate limiting prevents API throttling

## Logging

All API interactions are logged through the MusicAgent logging system:
- Request/response logging
- Error tracking
- Performance metrics

## License

This MCP server is part of the MusicAgent project and follows the same license.
