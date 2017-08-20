import time

from slackclient import SlackClient


class Vorta(object):
    def __init__(self, token=None, debug=False):
        self.token = token
        self.client = SlackClient(token)
        self.debug = debug
        self.connect()
        self.control_loop()

    def output_debug(self, *args):
        if self.debug:
            print(*args)

    def connect(self):
        self.client.rtm_connect()
        print('connected')

    def control_loop(self):
        while True:
            for event in self.client.rtm_read():
                self.output_debug('received event', event)
                self.handle_event(event)
            time.sleep(1)

    def handle_event(self, event):
        event_handler = 'event_%s' % event['type']
        if hasattr(self, event_handler):
            attr = getattr(self, event_handler)
            if callable(attr):
                attr(event)

    def event_message(self, event):
        print('*** %s' % event['text'])
