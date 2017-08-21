import asyncio
from functools import lru_cache
import json
import time

from slackclient import SlackClient
import websockets

from vorta.events import MessageEvent


class Vorta(object):
    desired_channels = []
    keepalive_interval = 60

    def __init__(self, token=None, debug=False):
        self.token = token
        self.client = SlackClient(token)
        self.debug = debug
        self._message_id = 1
        self.identity = self.fetch_identity()
        self.at_me = '<@%s> ' % self.identity['user_id']
        self.websocket_url = self.fetch_websocket_url()
        self.check_channels()
        self.control_loop()

    def get_desired_channels(self):
        return self.desired_channels

    def output_debug(self, *args):
        if self.debug:
            print(*args)

    def fetch_identity(self):
        return self.client.api_call('auth.test')

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
        asyncio.async(self.keepalives())
        while True:
            content = yield from self.websocket.recv()
            if content is None:
                break
            event = json.loads(content)
            self.output_debug('received %s event' % event['type'], event)
            self.handle_event(event)

    @asyncio.coroutine
    def keepalives(self):
        while True:
            yield from asyncio.sleep(self.keepalive_interval)
            yield from self.ping()

    @asyncio.coroutine
    def ping(self):
        self._message_id += 1
        data = {
            'id': self._message_id,
            'type': 'ping'
        }
        content = json.dumps(data)
        yield from self.websocket.send(content)

    def event_object(self, event):
        if event['type'] == 'message':
            return MessageEvent(self, event)

    def handle_event(self, event):
        event_handler = 'event_%s' % event['type']
        if hasattr(self, event_handler):
            attr = getattr(self, event_handler)
            if callable(attr):
                obj = self.event_object(event)
                if obj is not None:
                    attr(obj)
                else:
                    attr(event)

    def fetch_channel_list(self):
        return self.client.api_call('channels.list')

    @lru_cache(maxsize=256)
    def fetch_channel_info(self, channel_id):
        return self.client.api_call(
            'channels.info',
            channel=channel_id,
        )

    @lru_cache(maxsize=256)
    def fetch_user_info(self, user_id):
        return self.client.api_call(
            'users.info',
            user=user_id,
        )

    def send_message(self, text, channel, attachments=None):
        return self.client.api_call(
            'chat.postMessage',
            text=text,
            channel=channel,
            attachments=attachments,
        )

    def update_message(self, text, channel_id, message_ts, attachments=None):
        return self.client.api_call(
            'chat.update',
            text=text,
            channel=channel_id,
            ts=message_ts,
            attachments=attachments,
        )

    def channel_name(self, channel_id):
        return '#%s' % self.fetch_channel_info(channel_id)['channel']['name']

    def user_name(self, user_id):
        return self.fetch_user_info(user_id)['user']['name']


    def event_message(self, event):
        if event.text.startswith(self.at_me):
            return self.event_at_message(event)
        if event.channel.startswith('D'):
            return self.event_dm_message(event)
        return self.event_chat_message(event)

    def event_chat_message(self, event):
        print('*** %s in %s: %s' % (event.user_name, event.channel_name, event.text))

    def event_at_message(self, event):
        text = event.text[len(self.at_me):]
        print('*** %s @ message in %s: %s' % (event.user_name, event.channel_name, text))

    def event_dm_message(self, event):
        print('*** IM from %s: %s' % (event.user_name, event.text))
