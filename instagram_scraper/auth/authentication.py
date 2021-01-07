import json

import requests

from instagram_scraper.constants import BASE_URL, STORIES_UA, LOGIN_URL, LOGOUT_URL

CHROME_WIN_UA = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36'


class Authentication(object):

    def __init__(self):
        self.logged_in = False
        self.session = None
        self.cookies = None

    def guest_login(self):
        """Authenticate as a guest/non-signed in user"""
        self.session = requests.Session()
        self.session.headers = {'user-agent': CHROME_WIN_UA}
        self.session.headers.update({'Referer': BASE_URL, 'user-agent': STORIES_UA})
        request = self.session.get(BASE_URL)
        self.session.headers.update({'X-CSRFToken': request.cookies['csrftoken']})
        self.session.headers.update({'user-agent': CHROME_WIN_UA})

    def user_login(self, username, password):
        """Logs in to instagram."""
        self.session = requests.Session()
        self.session.headers = {'user-agent': CHROME_WIN_UA}
        self.session.headers.update({'Referer': BASE_URL, 'user-agent': STORIES_UA})
        req = self.session.get(BASE_URL)

        self.session.headers.update({'X-CSRFToken': req.cookies['csrftoken']})

        login_data = {'username': username, 'password': password}
        login = self.session.post(LOGIN_URL, data=login_data, allow_redirects=True)
        self.session.headers.update({'X-CSRFToken': login.cookies['csrftoken']})
        self.cookies = login.cookies
        login_text = json.loads(login.text)

        if login_text.get('authenticated') and login.status_code == 200:
            self.logged_in = True
            self.session.headers.update({'user-agent': CHROME_WIN_UA})
        else:
            print('Login failed for ' + username)

            if 'checkpoint_url' in login_text:
                checkpoint_url = login_text.get('checkpoint_url')
                print('Please verify your account at ' + BASE_URL[0:-1] + checkpoint_url)

                if self.interactive is True:
                    self.login_challenge(checkpoint_url)
            elif 'errors' in login_text:
                for count, error in enumerate(login_text['errors'].get('error')):
                    count += 1
                    print('Session error %(count)s: "%(error)s"' % locals())
            else:
                print(json.dumps(login_text))

    def logout(self):
        """Logs out of instagram."""
        if self.logged_in:
            try:
                logout_data = {'csrfmiddlewaretoken': self.cookies['csrftoken']}
                self.session.post(LOGOUT_URL, data=logout_data)
                self.logged_in = False
            except requests.exceptions.RequestException:
                print('Failed to log out')

    def session(self):
        return self.session()

    def cookies(self):
        return self.cookies
