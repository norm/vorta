import json
import shlex
import subprocess
import threading
import time


class Subprocess(object):
    autorun = True

    def __init__(self, vorta, command, channel):
        self.vorta = vorta
        self.command = command
        self.channel = channel
        self.output = ''
        self.exit_code = None
        if self.autorun:
            self.run()

    def run(self):
        self.run_subprocess()

    def run_subprocess(self):
        process = subprocess.Popen(
            shlex.split(self.command),
            stdout=subprocess.PIPE,
        )
        self.subprocess_started()

        while True:
            line = process.stdout.readline()
            if not line:
                break
            self.output += line.decode('utf-8')
            self.output_updated()

        self.exit_code = process.wait()
        self.subprocess_exited()

    def subprocess_started(self):
        pass

    def output_updated(self):
        pass

    def subprocess_exited(self):
        pass


class ThreadedSubprocess(Subprocess):
    def run(self):
        thread = threading.Thread(target=self.run_subprocess)
        thread.daemon = True
        thread.start()


class ReportingSubprocess(ThreadedSubprocess):
    last_update = 0
    update_interval = 3
    message_ts = None
    channel_id = None
    running_rgb = '#b6b6b6'
    success_rgb = '#0082c8'
    failure_rgb = '#e6194b'

    def subprocess_started(self):
        self.attachment = {
            'color': self.running_rgb,
            'fallback': 'Running "%s"...' % self.command,
            'mrkdwn_in': ['text', 'pretext'],
            'pretext': 'Running `%s`...' % self.command,
        }

        result = self.vorta.send_message(
            'Running `%s`...' % self.command,
            self.channel,
        )
        self.message_ts = result['ts']
        self.channel_id = result['channel']
        # show the first update more quickly than usual
        self.last_update = time.time() - (self.update_interval + 0.5)

    def output_updated(self):
        if self.output:
            # update the output only after sufficient time has passed
            # since the last, to avoid spamming slack
            if time.time() - self.last_update > self.update_interval:
                self.last_update = time.time()
                self.attachment.update({'text': '```%s```' % self.output})
                result = self.vorta.update_message(
                    '',
                    self.channel_id,
                    self.message_ts,
                    attachments=json.dumps([self.attachment])
                )

    def subprocess_exited(self):
        self.attachment.update({
            'color': self.success_rgb,
            'footer': 'Finished',
            'pretext': 'Ran `%s`.' % self.command,
            'text': '```%s```' % self.output,
            'ts': int(time.time()),
        })

        if not self.output:
            self.attachment.update({
                'text': '_(no output)_'
            })

        # indicate when errors occur running the script
        if self.exit_code:
            self.attachment.update({
                'color': self.failure_rgb,
                'footer': 'Finished (with error)',
                'pretext': 'Ran `%s`, which failed.' % self.command,
            })

        result = self.vorta.update_message(
            '',
            self.channel_id,
            self.message_ts,
            attachments=json.dumps([self.attachment])
        )

