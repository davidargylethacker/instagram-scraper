import argparse
import json
import sys
import time

import requests

from instagram_scraper.app import PartialContentException
from instagram_scraper.auth.authentication import Authentication
from instagram_scraper.constants import RETRY_DELAY, CONNECT_TIMEOUT, MAX_RETRY_DELAY, USER_URL


class ProfileMetadataScraper(object):

    def __init__(self, username_to_scrape, login_user, login_password):
        self.username = username_to_scrape
        self.login_user = login_user
        self.login_pass = login_password
        self.authentication = Authentication()

    def scrape(self):
        print("hello world")
        self.authentication.user_login(self.login_user, self.login_pass)
        profile_info = self._get_profile_info()
        print(profile_info)
        self.authentication.logout()

    def _get_profile_info(self):
        url = USER_URL.format(self.username)
        resp = self._get_json(url)

        if resp is None:
            print('Error getting user info for {0}'.format(self.username))
            return

        print(resp)
        print('Saving metadata general information on {0}.json'.format(self.username))

        user_info = json.loads(resp)['graphql']['user']

        try:
            profile_info = {
                'biography': user_info['biography'],
                'followers_count': user_info['edge_followed_by']['count'],
                'following_count': user_info['edge_follow']['count'],
                'full_name': user_info['full_name'],
                'id': user_info['id'],
                'is_business_account': user_info['is_business_account'],
                'is_joined_recently': user_info['is_joined_recently'],
                'is_private': user_info['is_private'],
                'posts_count': user_info['edge_owner_to_timeline_media']['count'],
                'profile_pic_url': user_info['profile_pic_url']
            }
        except (KeyError, IndexError, StopIteration):
            print('Failed to build {0} profile info'.format(self.username))
            return

        item = {
            'GraphProfileInfo': {
                'info': profile_info,
                'username': self.username,
                'created_time': 1286323200
            }
        }
        return item
        # self.save_json(item, '{0}/{1}.json'.format(dst, username))

    def _get_json(self, *args, **kwargs):
        """Retrieve text from url. Return text as string or None if no data present """
        resp = self._safe_get(*args, **kwargs)

        if resp is not None:
            return resp.text

    def _safe_get(self, *args, **kwargs):
        # out of the box solution
        # session.mount('https://', HTTPAdapter(max_retries=...))
        # only covers failed DNS lookups, socket connections and connection timeouts
        # It doesnt work when server terminate connection while response is downloaded
        retry = 0
        retry_delay = RETRY_DELAY
        while True:
            try:
                response = self.authentication.session.get(timeout=CONNECT_TIMEOUT, cookies=None, *args, **kwargs)
                if response.status_code == 404:
                    return
                response.raise_for_status()
                content_length = response.headers.get('Content-Length')
                if content_length is not None and len(response.content) != int(content_length):
                    # if content_length is None we repeat anyway to get size and be confident
                    raise PartialContentException('Partial response')
                return response
            except (KeyboardInterrupt):
                raise
            except (requests.exceptions.RequestException, PartialContentException) as e:
                if 'url' in kwargs:
                    url = kwargs['url']
                elif len(args) > 0:
                    url = args[0]
                if retry < MAX_RETRIES:
                    print('Retry after exception {0} on {1}'.format(repr(e), url))
                    self.sleep(retry_delay)
                    retry_delay = min(2 * retry_delay, MAX_RETRY_DELAY)
                    retry = retry + 1
                    continue
                else:
                    keep_trying = self._retry_prompt(url, repr(e))
                    if keep_trying:
                        retry = 0
                        continue
                    else:
                        return

    def sleep(self, secs):
        min_delay = 1
        for _ in range(secs // min_delay):
            time.sleep(min_delay)
        time.sleep(secs % min_delay)

    def _retry_prompt(self, url, exception_message):
        """Show prompt and return True: retry, False: ignore, None: abort"""
        answer = input('Repeated error {0}\n(A)bort, (I)gnore, (R)etry or retry (F)orever?'.format(exception_message))
        if answer:
            answer = answer[0].upper()
            if answer == 'I':
                print('The user has chosen to ignore {0}'.format(url))
                return False
            elif answer == 'R':
                return True
            elif answer == 'F':
                print('The user has chosen to retry forever')
                global MAX_RETRIES
                MAX_RETRIES = sys.maxsize
                return True
            else:
                print('The user has chosen to abort')
                return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('username', help='Instagram user(s) to scrape', nargs='*')
    parser.add_argument('--login-user', '--login_user', '-u', default=None, help='Instagram login user')
    parser.add_argument('--login-pass', '--login_pass', '-p', default=None, help='Instagram login password')

    args = parser.parse_args()
    print(args.username)
    if args.username:
        scraper = ProfileMetadataScraper(args.username[0], args.login_user, args.login_pass)
        scraper.scrape()


if __name__ == '__main__':
    main()
