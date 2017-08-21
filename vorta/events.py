class SlackEvent(object):
    pass


class MessageEvent(object):
    def __init__(self, vorta, event):
        self.vorta = vorta
        self.event = event

    @property
    def text(self):
        if self.event.get('message') is not None:
            return self.event['message']['text']
        else:
            return self.event['text']

    @property
    def channel(self):
        return self.event['channel']

    @property
    def channel_name(self):
        return self.vorta.channel_name(self.channel)
