import logging
import requests

logger = logging.getLogger(__name__)

class SessionMonkeyPatch(object):
    def __init__(self, session: requests.Session, hard_retries=3):
        self.session = session
        self.hard_retries = hard_retries
        self.old_send_method = session.send
    def _new_send(self, request, **kwargs):
        hard_retries = self.hard_retries
        if hard_retries <= 0:
            raise ValueError('hard_retries must be positive')

        while hard_retries > 0:
            try:
                return self.old_send_method(request, **kwargs)
            except KeyboardInterrupt:
                raise
            except Exception as e:
                hard_retries -= 1
                if hard_retries <= 0:
                    raise e
                logger.warn('Hard retry... (%d), due to: %s' % (hard_retries, e))

    def hijack(self):
        self.session.send = self._new_send # type: ignore
        return self.session
        