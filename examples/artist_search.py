"""
Artist search example for the MusicAgent Discogs API client.

This script takes an artist name as input, searches the Discogs API,
and displays the results in both raw JSON and markdown format.
"""

import json
from typing import Dict, Any, List

from musicagent.client.http_client import DiscogsHTTPClient
from musicagent.client.request_builder import RequestBuilder
from musicagent.config.settings import settings


def format_markdown_artist_info(artist_data: Dict[str, Any]) -> str:
    """
    Format artist information as markdown.
    
    Args:
        artist_data: Artist data from Discogs API
        
    Returns:
        Markdown formatted string
    """
    md = []
    md.append(f"## Artist: {artist_data.get('name', 'Unknown')}")
    md.append("")
    
    if 'profile' in artist_data and artist_data['profile']:
        profile = artist_data['profile']
        # Truncate long profiles
        if len(profile) > 500:
            profile = profile[:500] + "..."
        md.append(f"**Profile:** {profile}")
        md.append("")
    
    if 'id' in artist_data:
        md.append(f"**Discogs ID:** {artist_data['id']}")
    
    if 'resource_url' in artist_data:
        md.append(f"**Resource URL:** {artist_data['resource_url']}")
    
    if 'uri' in artist_data:
        md.append(f"**URI:** {artist_data['uri']}")
    
    if 'urls' in artist_data and artist_data['urls']:
        md.append("")
        md.append("**External URLs:**")
        for url in artist_data['urls'][:5]:  # Limit to first 5
            md.append(f"- {url}")
    
    if 'members' in artist_data and artist_data['members']:
        md.append("")
        md.append("**Members:**")
        for member in artist_data['members'][:10]:  # Limit to first 10
            md.append(f"- {member.get('name', 'Unknown')}")
    
    return "\n".join(md)


def format_markdown_releases(releases_data: Dict[str, Any]) -> str:
    """
    Format releases information as markdown.
    
    Args:
        releases_data: Releases data from Discogs API
        
    Returns:
        Markdown formatted string
    """
    md = []
    md.append("## Releases")
    md.append("")
    
    if 'pagination' in releases_data:
        pagination = releases_data['pagination']
        md.append(f"**Total Releases:** {pagination.get('items', 0)}")
        md.append(f"**Page:** {pagination.get('page', 1)} of {pagination.get('pages', 1)}")
        md.append(f"**Per Page:** {pagination.get('per_page', 0)}")
        md.append("")
    
    if 'releases' in releases_data:
        releases = releases_data['releases']
        md.append("### Release List")
        md.append("")
        
        for idx, release in enumerate(releases[:20], 1):  # Limit to first 20
            title = release.get('title', 'Unknown Title')
            year = release.get('year', 'N/A')
            release_id = release.get('id', 'N/A')
            format_info = release.get('format', 'Unknown Format')
            
            md.append(f"**{idx}. {title}** ({year})")
            md.append(f"   - ID: {release_id}")
            md.append(f"   - Format: {format_info}")
            
            if 'label' in release:
                md.append(f"   - Label: {release['label']}")
            
            if 'role' in release:
                md.append(f"   - Role: {release['role']}")
            
            if 'resource_url' in release:
                md.append(f"   - URL: {release['resource_url']}")
            
            md.append("")
    
    return "\n".join(md)


def format_markdown_search_results(search_data: Dict[str, Any]) -> str:
    """
    Format search results as markdown.
    
    Args:
        search_data: Search results from Discogs API
        
    Returns:
        Markdown formatted string
    """
    md = []
    md.append("## Artist Search Results")
    md.append("")
    
    if 'pagination' in search_data:
        pagination = search_data['pagination']
        md.append(f"**Total Results:** {pagination.get('items', 0)}")
        md.append("")
    
    if 'results' in search_data:
        results = search_data['results']
        
        for idx, result in enumerate(results[:10], 1):  # Limit to first 10
            title = result.get('title', 'Unknown')
            result_type = result.get('type', 'Unknown')
            result_id = result.get('id', 'N/A')
            
            md.append(f"**{idx}. {title}**")
            md.append(f"   - Type: {result_type}")
            md.append(f"   - ID: {result_id}")
            
            if 'country' in result:
                md.append(f"   - Country: {result['country']}")
            
            if 'year' in result:
                md.append(f"   - Year: {result['year']}")
            
            if 'thumb' in result:
                md.append(f"   - Thumbnail: {result['thumb']}")
            
            md.append("")
    
    return "\n".join(md)


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def main():
    """Main function to search for an artist and display results."""
    
    # Get artist name from user
    artist_name = input("Enter artist name to search: ").strip()
    
    if not artist_name:
        print("Error: Artist name cannot be empty.")
        return
    
    # Initialize client
    print(f"\nSearching for artist: {artist_name}")
    client = DiscogsHTTPClient()
    builder = RequestBuilder()
    
    try:
        # Step 1: Search for the artist
        print_section("STEP 1: SEARCHING FOR ARTIST")
        
        search_url = builder.search(
            query=artist_name,
            search_type="artist"
        ).paginate(page=1, per_page=10).build()
        
        endpoint = search_url.replace(settings.DISCOGS_BASE_URL, "")
        search_response = client.get(endpoint)
        
        # Display raw JSON for search results
        print("RAW JSON RESPONSE (Search):")
        print("-" * 80)
        print(json.dumps(search_response, indent=2))
        print("-" * 80)
        
        # Display markdown formatted search results
        print("\nMARKDOWN FORMATTED OUTPUT (Search):")
        print("-" * 80)
        print(format_markdown_search_results(search_response))
        print("-" * 80)
        
        # Check if we found any results
        if not search_response.get('results'):
            print(f"\nNo artists found matching '{artist_name}'")
            return
        
        # Get the first artist result
        first_result = search_response['results'][0]
        artist_id = first_result['id']
        
        # Step 2: Get detailed artist information
        print_section(f"STEP 2: GETTING DETAILS FOR ARTIST ID {artist_id}")
        
        artist_response = client.get(f"artists/{artist_id}")
        
        # Display raw JSON for artist details
        print("RAW JSON RESPONSE (Artist Details):")
        print("-" * 80)
        print(json.dumps(artist_response, indent=2))
        print("-" * 80)
        
        # Display markdown formatted artist details
        print("\nMARKDOWN FORMATTED OUTPUT (Artist Details):")
        print("-" * 80)
        print(format_markdown_artist_info(artist_response))
        print("-" * 80)
        
        # Step 3: Get artist's releases
        print_section(f"STEP 3: GETTING RELEASES FOR {artist_response.get('name', 'ARTIST')}")
        
        releases_response = client.get(
            f"artists/{artist_id}/releases",
            params={"page": 1, "per_page": 20, "sort": "year", "sort_order": "desc"}
        )
        
        # Display raw JSON for releases
        print("RAW JSON RESPONSE (Releases):")
        print("-" * 80)
        print(json.dumps(releases_response, indent=2))
        print("-" * 80)
        
        # Display markdown formatted releases
        print("\nMARKDOWN FORMATTED OUTPUT (Releases):")
        print("-" * 80)
        print(format_markdown_releases(releases_response))
        print("-" * 80)
        
        # Summary
        print_section("SUMMARY")
        print(f"Artist: {artist_response.get('name', 'Unknown')}")
        print(f"Total Releases Found: {releases_response.get('pagination', {}).get('items', 0)}")
        print(f"Displayed: {len(releases_response.get('releases', []))} releases")
        
        # Show rate limit status
        rate_status = client.get_rate_limit_status()
        print(f"\nRate Limit Status:")
        print(f"  Requests made: {rate_status.get('requests_made', 0)}")
        print(f"  Requests remaining: {rate_status.get('remaining_capacity', 0)}")
        
    except Exception as e:
        print(f"\nError occurred: {type(e).__name__}: {str(e)}")
        raise
    
    finally:
        # Clean up
        client.close()
        print("\n" + "=" * 80)
        print("Search completed.")
        print("=" * 80)


if __name__ == "__main__":
    main()
