import asyncio
from functools import lru_cache
import json
import time

from slackclient import SlackClient
import websockets


class Vorta(object):
    desired_channels = []

    def __init__(self, token=None, debug=False):
        self.token = token
        self.client = SlackClient(token)
        self.debug = debug
        self.websocket_url = self.fetch_websocket_url()
        self.check_channels()
        self.control_loop()

    def get_desired_channels(self):
        return self.desired_channels

    def output_debug(self, *args):
        if self.debug:
            print(*args)

    def fetch_websocket_url(self):
        return self.client.api_call('rtm.start')['url']

    def check_channels(self):
        # FIXME pagination of channel list
        channels = self.fetch_channel_list()['channels']
        channel_names = [
            '#%s' % channel['name']
                for channel in channels
        ]
        for channel in self.get_desired_channels():
            if channel not in channel_names:
                print('*** desired channel %s does not exist' % channel)
        for channel in channels:
            if '#%s' % channel['name'] in self.get_desired_channels():
                if not channel['is_member']:
                    print('*** not in desired channel #%s' % channel['name'])

    def control_loop(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            asyncio.gather(self.websocket_handler())
        )

    @asyncio.coroutine
    def websocket_handler(self):
        self.websocket = yield from websockets.connect(self.websocket_url)
        while True:
            content = yield from self.websocket.recv()
            if content is None:
                break
            event = json.loads(content)
            self.output_debug('received %s event' % event['type'], event)
            self.handle_event(event)

    def handle_event(self, event):
        event_handler = 'event_%s' % event['type']
        if hasattr(self, event_handler):
            attr = getattr(self, event_handler)
            if callable(attr):
                attr(event)

    def fetch_channel_list(self):
        return self.client.api_call('channels.list')

    @lru_cache(maxsize=256)
    def fetch_channel_info(self, channel_id):
        return self.client.api_call(
            'channels.info',
            channel=channel_id,
        )

    def channel_name(self, channel_id):
        return '#%s' % self.fetch_channel_info(channel_id)['channel']['name']

    def event_message(self, event):
        print('*** %s: %s' % (self.channel_name(event['channel']), event['text']))
