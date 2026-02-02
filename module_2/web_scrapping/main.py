import time

import config
from scrape import GradCafeScraper


def main():
    TARGET_SIZE = config.data_size
    DELAY_BETWEEN_PAGES = 1

    scraper = GradCafeScraper()

    current_count = 0
    page_num = 1

    print("="*60)
    print("GRAD CAFE SCRAPER")
    print("="*60)
    print(f"Target: {TARGET_SIZE:,} records")
    print(f"Current: {current_count:,} records")
    print(f"Remaining: {TARGET_SIZE - current_count:,} records")
    print("="*60)

    try:
        while current_count < TARGET_SIZE:
            print(f"Progress: {current_count:,}/{TARGET_SIZE:,} ({current_count/TARGET_SIZE*100:.1f}%)")

            # Scrape page
            applicants = scraper.scrape_page(page_num)

            # Save data and update count
            if applicants:
                scraper.save_data(applicants)
                current_count += len(applicants)  # Just add the new records!

                if current_count >= TARGET_SIZE:
                    print(f"Target reached! Scraped {current_count:,} records")
                    break
            else:
                print(f"No results found on page {page_num}")
                user_input = input("Continue to next page? (y/n): ")
                if user_input.lower() != 'y':
                    break

            page_num += 1
            time.sleep(DELAY_BETWEEN_PAGES)

    except KeyboardInterrupt:
        print(f"Scraping interrupted by user")
        print(f"📊 Final count: {current_count:,} records")

    except Exception as e:
        print(f"Error occurred: {e}")
        print(f"📊 Records scraped so far: {current_count:,}")

    finally:
        print("" + "="*60)
        print("SCRAPING SUMMARY")
        print("="*60)
        # Verify final count from file
        print(f"Total records scraped: {current_count:,}")
        print(f"Last page scraped: {page_num}")
        print(f"Data saved to: {config.data_file}")
        print("="*60)


if __name__ == '__main__':
    main()