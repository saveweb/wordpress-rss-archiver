import logging
from typing import List
import feedparser
from urllib.parse import urljoin
import requests
import datetime
import time

from wordpress_rss_archiver.utils.spn2 import SPN2API
from wordpress_rss_archiver.utils.requests_patch import SessionMonkeyPatch

def arg_parser():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('FEED_URL', help='RSS feed URL (http?://example.com/feed)')
    parser.add_argument('--ia-s3', help='IA s3 API KEYS (access_key:secret_key) (get from https://archive.org/account/s3.php)')
    parser.add_argument('--debug', action='store_true')
    return parser.parse_args()


def main():
    arg = arg_parser()
    feed_url: str = arg.FEED_URL
    s3_auth: str = arg.ia_s3
    if arg.debug:
        logging.basicConfig(level=logging.DEBUG)

    sess = requests.Session()
    sess = SessionMonkeyPatch(sess).hijack()

    spn2api = SPN2API(sess, s3_auth=s3_auth)

    feed_url = sess.head(feed_url).url

    pid=0
    while True:
        pid += 1
        print('pid:', pid)

        r = sess.get(feed_url, params={'paged': pid})

        if r.status_code == 404:
            print('404, We reached the end of the feed.')
            break

        r.raise_for_status()
        data = r.text

        feed = feedparser.parse(data)
        items: List = feed["items"]

        for item in items:
            print("============")

            title = item["title"]
            print('title:', title)

            guid = item["guid"]
            print('guid:', guid)

            item_url_raw = item["link"]
            item_url = urljoin(feed_url, item_url_raw)
            print('item_url:', item_url)
            
            time_p: time.struct_time = item["published_parsed"]
            try:
                print('format_time:', datetime.datetime(*time_p[:6]).isoformat()) # type: ignore
            except ValueError:
                print('format_time: None')

            print('Submitting to SPN ...')

            spn2api.take_snapshot(item_url)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()