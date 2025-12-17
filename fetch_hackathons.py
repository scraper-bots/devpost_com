#!/usr/bin/env python3
"""
Fetch all hackathons from Devpost API and save to CSV (Improved Async version with retry logic)
"""
import aiohttp
import asyncio
import csv
from typing import Dict, List, Optional
import sys

async def fetch_page_with_retry(session: aiohttp.ClientSession, page_num: int,
                                  semaphore: asyncio.Semaphore, max_retries: int = 3) -> Optional[Dict]:
    """Fetch a single page of hackathons with retry logic"""
    url = f"https://devpost.com/api/hackathons?page={page_num}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json',
    }

    async with semaphore:  # Limit concurrent requests
        for attempt in range(max_retries):
            try:
                async with session.get(url, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        if attempt < max_retries - 1:
                            # Wait a bit before retrying
                            await asyncio.sleep(1 * (attempt + 1))
                            continue
                        else:
                            return None
                    else:
                        response.raise_for_status()
            except asyncio.TimeoutError:
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 * (attempt + 1))
                    continue
                else:
                    print(f"Timeout fetching page {page_num} after {max_retries} attempts",
                          file=sys.stderr, flush=True)
                    return None
            except Exception as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 * (attempt + 1))
                    continue
                else:
                    print(f"Error fetching page {page_num} after {max_retries} attempts: {e}",
                          file=sys.stderr, flush=True)
                    return None

    return None

def flatten_hackathon(hackathon: Dict) -> Dict:
    """Flatten hackathon data for CSV export"""
    themes = ', '.join([theme['name'] for theme in hackathon.get('themes', [])])

    return {
        'id': hackathon.get('id'),
        'title': hackathon.get('title'),
        'url': hackathon.get('url'),
        'organization_name': hackathon.get('organization_name'),
        'location': hackathon.get('displayed_location', {}).get('location'),
        'open_state': hackathon.get('open_state'),
        'submission_period_dates': hackathon.get('submission_period_dates'),
        'time_left_to_submission': hackathon.get('time_left_to_submission'),
        'prize_amount': hackathon.get('prize_amount', '').replace('<span data-currency-value>', '').replace('</span>', ''),
        'cash_prizes_count': hackathon.get('prizes_counts', {}).get('cash', 0),
        'other_prizes_count': hackathon.get('prizes_counts', {}).get('other', 0),
        'registrations_count': hackathon.get('registrations_count'),
        'themes': themes,
        'featured': hackathon.get('featured'),
        'winners_announced': hackathon.get('winners_announced'),
        'invite_only': hackathon.get('invite_only'),
        'managed_by_devpost': hackathon.get('managed_by_devpost_badge'),
        'thumbnail_url': 'https:' + hackathon.get('thumbnail_url', '') if hackathon.get('thumbnail_url') else '',
        'submission_gallery_url': hackathon.get('submission_gallery_url'),
    }

async def fetch_all_hackathons(total_pages: int, first_page_hackathons: List[Dict]) -> List[Dict]:
    """Fetch all pages concurrently with controlled concurrency"""
    all_hackathons = []

    # Add hackathons from first page
    for hackathon in first_page_hackathons:
        all_hackathons.append(flatten_hackathon(hackathon))

    # Limit concurrent requests to avoid overwhelming the server
    max_concurrent = 10  # Reduced from 50
    semaphore = asyncio.Semaphore(max_concurrent)

    async with aiohttp.ClientSession() as session:
        # Create tasks for all remaining pages
        tasks = []
        for page_num in range(2, total_pages + 1):
            task = fetch_page_with_retry(session, page_num, semaphore)
            tasks.append((page_num, task))

        # Fetch all pages concurrently with progress updates
        print(f"Fetching pages 2-{total_pages} with {max_concurrent} concurrent requests...", flush=True)

        completed = 0
        failed_pages = []

        for page_num, coro in tasks:
            data = await coro
            completed += 1

            if completed % 100 == 0 or completed == len(tasks):
                print(f"Progress: {completed}/{len(tasks)} pages fetched ({completed*100//len(tasks)}%)", flush=True)

            if data and 'hackathons' in data:
                for hackathon in data['hackathons']:
                    all_hackathons.append(flatten_hackathon(hackathon))
            else:
                failed_pages.append(page_num)

        if failed_pages:
            print(f"\nWarning: {len(failed_pages)} pages failed to fetch", flush=True)
            print(f"Failed pages (first 20): {failed_pages[:20]}", flush=True)

    return all_hackathons

async def main():
    print("Fetching hackathon data from Devpost API (Improved Async)...", flush=True)

    # Fetch first page to get total count
    print("Fetching page 1 to determine total pages...", flush=True)

    async with aiohttp.ClientSession() as session:
        url = "https://devpost.com/api/hackathons?page=1"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json',
        }

        async with session.get(url, headers=headers) as response:
            first_page = await response.json()

    if not first_page:
        print("Failed to fetch first page. Exiting.", flush=True)
        sys.exit(1)

    total_count = first_page['meta']['total_count']
    per_page = first_page['meta']['per_page']
    total_pages = (total_count + per_page - 1) // per_page

    print(f"Total hackathons: {total_count}", flush=True)
    print(f"Per page: {per_page}", flush=True)
    print(f"Total pages: {total_pages}", flush=True)

    # Fetch all hackathons
    all_hackathons = await fetch_all_hackathons(total_pages, first_page['hackathons'])

    print(f"\nFetched {len(all_hackathons)} hackathons total", flush=True)

    # Write to CSV
    output_file = 'devpost_hackathons.csv'
    print(f"Writing to {output_file}...", flush=True)

    if all_hackathons:
        fieldnames = all_hackathons[0].keys()

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_hackathons)

        print(f"Successfully saved {len(all_hackathons)} hackathons to {output_file}", flush=True)
    else:
        print("No hackathons to save", flush=True)

if __name__ == '__main__':
    asyncio.run(main())
