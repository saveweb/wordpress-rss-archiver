import logging
import re
import time
import functools
from typing import Dict, Optional
import requests


logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 32

def _assert(expr, msg=''):
    if not expr:
        raise AssertionError(msg)


def retry(try_count=3, retry_interval=2, retry_interval_step=3):
    def _retry(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            _retry_interval = retry_interval

            for i in range(try_count):
                try:
                    _result = func(*args, **kwargs)
                    if i > 0:
                        logger.warning('(Try %d/%d) %r success', i + 1, try_count, func.__name__)

                    return _result
                except Exception as e:
                    if i < try_count - 1:
                        logger.warning('(Try %d/%d) %r got exception %r: %r', i + 1, try_count, func.__name__, type(e), e)

                        if _retry_interval < 0:
                            _retry_interval = 0

                        logger.warning('Wait %.2f s to retry', _retry_interval)
                        time.sleep(_retry_interval)
                        _retry_interval += retry_interval_step

                        logger.warning('(Try %d/%d) retrying ...', i + 2, try_count)
                    else:
                        raise e

        return wrapper

    return _retry

def is_valid_job_id(s):
    if type(s) is not str:
        return False

    regex = r'^spn2\-[0-9a-f]{40}$'
    if re.search(regex, s):
        return True
    else:
        return False


@retry(try_count=8, retry_interval=2, retry_interval_step=5)
def _archive(sess: requests.Session, url: str, s3_auth: str,*, if_not_archived_within: str = '30d', skip_first_archive: str = '1', js_behavior_timeout: str = '30'):
    """
    Possible API result:
    {"url":"https://example.com/","job_id":"spn2-0123456789abcdef0123456789abcdef12345678"}
    {"message": "Cannot resolve host example.com.", "status": "error", "status_ext": "error:invalid-host-resolution"}
    """

    api_url = 'https://web.archive.org/save/'

    headers = {
        'Authorization': f'LOW {s3_auth}',
        'Accept': 'application/json',
    }

    data = {
        'url': url,
        'if_not_archived_within': if_not_archived_within,
        'skip_first_archive': skip_first_archive,
        'js_behavior_timeout': js_behavior_timeout,
        #'capture_screenshot': '1',
    }
    logger.debug('data: %r', data)

    r = sess.post(api_url, headers=headers, data=data)

    _assert(r.status_code == 200, f'archive.org archive API status code: {r.status_code}, content: {r.text[:256]}')
    _assert('application/json' in r.headers['Content-Type'], f'archive.org archive API Content-Type: {r.headers["Content-Type"]}')

    # order of result JSON dict key is not fixed
    return dict(sorted(r.json().items()))


@retry(try_count=8, retry_interval=2, retry_interval_step=5)
def _get_job_status(sess: requests.Session, job_id):
    url = f'https://web.archive.org/save/status/{job_id}'
    r = sess.get(url)

    _assert(r.status_code == 200, f'archive.org get_job_status API status code: {r.status_code}, content: {r.text[:256]}')
    _assert('application/json' in r.headers['Content-Type'], f'archive.org get_job_status API Content-Type: {r.headers["Content-Type"]}')

    # order of result JSON dict key is not fixed
    result = dict(sorted(r.json().items()))

    # delete useless info, shrink data size
    if 'outlinks' in result:
        del result['outlinks']

    if 'resources' in result:
        del result['resources']

    return result


@retry(try_count=8, retry_interval=2, retry_interval_step=5)
def get_user_status(sess: requests.Session, s3_auth: str):
    api_url = 'https://web.archive.org/save/status/user'
    headers = {
        'Authorization': f'LOW {s3_auth}',
        'Accept': 'application/json',
    }
    r = sess.get(api_url, headers=headers)

    # order of result JSON dict key is not fixed
    result = dict(sorted(r.json().items()))

    return result


class SPN2API(object):
    user_status: Optional[Dict]
    sess: requests.Session
    s3_auth: str

    def __init__(self, sess: requests.Session, s3_auth: str):
        self.sess = sess
        self.s3_auth = s3_auth
        self.user_status = get_user_status(self.sess, s3_auth)

    def is_archive_available(self):

        # init
        if self.user_status is None:
            logger.info('Initializing user_status ...')
            self.user_status = get_user_status(self.sess, self.s3_auth)
            logger.info('user_status:', self.user_status)

        if self.user_status['daily_captures_limit'] <= self.user_status['daily_captures']:
            raise Exception("API: daily_captures_limit reached! (limit:",self.user_status['daily_captures_limit'],")")

        if self.user_status['available'] >= 1: # cache
            time.sleep(1.5)
            logger.info("API: available: %r", self.user_status['available'])
            self.user_status['available'] -= 1
            if self.user_status['available'] == 0:
                time.sleep(2.5)
                self.user_status = get_user_status(self.sess, self.s3_auth)
            return True
        else:
            self.user_status = get_user_status(self.sess, self.s3_auth)
            return False

    def take_snapshot(self, url):
        while self.is_archive_available() == False:
            time.sleep(6) # rate limit

        job_tick = _archive(sess=self.sess, url=url, s3_auth=self.s3_auth)
        logger.info('job_tick: %r', job_tick)

        if 'job_id' in job_tick:
            if is_valid_job_id(job_tick['job_id']) == True:
                job_status = _get_job_status(self.sess, job_tick['job_id'])
                while job_status['status'] == 'pending':
                    time.sleep(3)
                    job_status = _get_job_status(self.sess, job_tick['job_id'])
                    logger.info('job_status: %r', job_status)
