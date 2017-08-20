from os import getenv
from vorta import Vorta


bot = Vorta(getenv('SLACK_BOT_TOKEN'), debug=True)
