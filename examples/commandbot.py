from os import getenv

from vorta import Vorta
from vorta.subprocesses import ReportingSubprocess


class CommandBot(Vorta):
    def event_at_message(self, event):
        command = event.text[len(self.at_me):]
        ReportingSubprocess(self, command, event.channel)


bot = CommandBot(getenv('SLACK_BOT_TOKEN'), debug=True)
