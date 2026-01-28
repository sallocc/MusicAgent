"""
Basic usage examples for the MusicAgent Discogs API client.
"""

from musicagent.client.http_client import DiscogsHTTPClient
from musicagent.client.request_builder import RequestBuilder
from musicagent.config.settings import settings

def main():
    """Demonstrate basic API usage."""
    
    # Initialize client
    client = DiscogsHTTPClient()
    
    print("=== Basic Artist Search ===")
    
    # Search for an artist
    builder = RequestBuilder()
    search_url = builder.search(
        query="Miles Davis",
        search_type="artist"
    ).build()
    
    # Extract endpoint from full URL
    endpoint = search_url.replace(settings.DISCOGS_BASE_URL, "")
    response = client.get(endpoint)
    
    # Display results
    for result in response['results'][:5]:  # First 5 results
        print(f"- {result['title']} (ID: {result['id']})")
    
    print("\n=== Get Artist Details ===")
    
    # Get specific artist
    artist_id = 97784  # Miles Davis ID
    artist_response = client.get(f"artists/{artist_id}")
    
    print(f"Name: {artist_response['name']}")
    print(f"Profile: {artist_response['profile'][:100]}...")
    print(f"URLs: {artist_response.get('urls', [])}")
    
    print("\n=== Search for Releases ===")
    
    # Search for releases
    release_url = builder.reset().search(
        query="Kind of Blue",
        search_type="release"
    ).paginate(page=1, per_page=10).build()
    
    endpoint = release_url.replace(settings.DISCOGS_BASE_URL, "")
    releases = client.get(endpoint)
    
    print(f"Found {releases['pagination']['items']} releases")
    for release in releases['results'][:3]:
        print(f"- {release['title']} ({release.get('year', 'N/A')})")

if __name__ == "__main__":
    main()
