from os import getenv
from vorta import Vorta


class TestBot(Vorta):
    desired_channels = [
        '#testing',
    ]


bot = TestBot(getenv('SLACK_BOT_TOKEN'), debug=True)
