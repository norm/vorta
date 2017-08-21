from os import getenv, path

from vorta import Vorta
from vorta.subprocesses import ReportingSubprocess


class CommandBot(Vorta):
    def event_at_message(self, event):
        command = event.text[len(self.at_me):]
        script = command.split(' ', 1)[0]

        # FIXME fully restrict to just [a-z_], and executable
        # FIXME don't have "./commands/blah" in output in slack
        if path.isfile('commands/%s' % script):
            ReportingSubprocess(
                self,
                './commands/%s' % command,
                event.channel
            )
        else:
            self.send_message(
                '`%s` is not a valid command' % script,
                event.channel,
            )

bot = CommandBot(getenv('SLACK_BOT_TOKEN'), debug=True)
