"""Dispatcher script

Detect the site (EHF or IHF) and call the appropriate scraper module.
"""
import argparse
from urllib.parse import urlparse

def main():
    parser = argparse.ArgumentParser(description='Scrape team player lists (EHF/IHF)')
    parser.add_argument('-u', '--url', required=True, help='Team page URL')
    parser.add_argument('-o', '--output', default='player_roster.csv', help='Output CSV filename')
    parser.add_argument('--debug', action='store_true', help='Save fetched HTML as debug.html when no data')
    args = parser.parse_args()

    url = args.url
    parsed = urlparse(url)
    netloc = parsed.netloc.lower()

    # Import locally to avoid circular imports when running modules directly
    data = []
    if 'eurohandball.com' in netloc:
        import ihf
        # user probably wants EHF, but our ihf.py is for ihf.info; try to import ehf module
        try:
            import ehf
            data = ehf.scrape_player_data(url)
            save = ehf.save_to_csv
        except Exception:
            print('EHF parser not available or failed')
            data = []
            save = None

    elif 'ihf.info' in netloc:
        import ihf
        data = ihf.scrape_player_data(url)
        # reuse ehf.save_to_csv if available for consistent CSV output
        try:
            import ehf
            save = ehf.save_to_csv
        except Exception:
            save = None

    else:
        # Generic fallback: try to use ehf scraper if present
        try:
            import ehf
            data = ehf.scrape_player_data(url)
            save = ehf.save_to_csv
        except Exception:
            print('No suitable parser for this domain.')
            return

    if not data:
        print('No player data found.')
        if args.debug:
            # save fetched HTML for inspection
            try:
                import requests
                resp = requests.get(url, timeout=10)
                with open('debug.html', 'wb') as f:
                    f.write(resp.content)
                print('Saved fetched HTML to debug.html')
            except Exception as e:
                print(f'Could not fetch/save debug HTML: {e}')
        return

    if save:
        save(data, args.output)
    else:
        # Minimal CSV write if no save function available
        import csv
        keys = []
        for item in data:
            for k in item.keys():
                if k not in keys:
                    keys.append(k)
        with open(args.output, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(data)
        print(f"Saved to {args.output}")


if __name__ == '__main__':
    main()
