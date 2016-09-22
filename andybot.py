# -*- coding: utf-8 -*-
"""
  Slack bot experiment/leapfrog for use at CARTO to shave off those valuable
  seconds from every day tasks (e.g., getting the lat/long of a city
  or address)

  Excellent Slackbot template from:
    https://www.fullstackpython.com/blog/build-first-slack-bot-python.html

  API Keys are stored as environment variables: `export GMAPS_APIKEY="..."`
"""

# Features to add:
#  * anytime someone mentions a country name, give back a map of that country
#      using some static maps api
#  * give time to rain
#  * commute summary:
#    * the commute weather in the newyorkoffice channel
#    * suggested reading (NYTimes trending articles? Instapaper trends?)
#  * lunch suggester:
#     * using the Yelp API:
#         https://www.yelp.com/developers/documentation/v3/business_search

import os
import time as t
from slackclient import SlackClient
import requests
from datetime import datetime, time

# andy_bot's ID as an environment variable
BOT_ID = os.environ.get("BOT_ID")

# constants
# TODO: make this more robust to interactions with people
AT_BOT = "<@" + BOT_ID + ">:"
EXAMPLE_COMMAND = "do"

# current commands
#  prints in help with format: usage: ..., example: ..., output: ...
available_commands = {EXAMPLE_COMMAND: ('do something',
                                        'do foo',
                                        'will print annoying message'),
                      'weather': ('weather location',
                                  'weather new york city',
                                  'will print current weather in new york'
                                  'city'),
                      'xkcd': ('xkcd [latest]',
                               'xkcd',
                               'will print a random xkcd comic'),
                      'latlng': ('latlng place name',
                                 'latlng 201 moore street, brooklyn, ny',
                                 '40.7127837, -74.0059413'),
                      'data_obs': ('data observatory: _coming_soon_',
                                   '...',
                                   'will print a data observatory measure at '
                                   'the specified location')}

# instantiate Slack client
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))


def kelvin_to_fahrenheit(temp):
    """
      Convert at temperature in Kelvin to degrees Fahrenheit
    """
    return temp * 1.8 - 459.67

# commands available through andy_bot


def get_weather(location):
    """
      'weather'
      Returns the weather at the location requested
    """
    if location == '' or location is None:
        return 'Specify a place for weather: `weather manila, philippines`'

    owm_api_key = os.environ.get("OPENWEATHERMAP_APIKEY")
    owm_req = "http://api.openweathermap.org/data/2.5/weather" \
              "?q={location}&APPID={APIKEY}"

    fill = {"location": location, "APIKEY": owm_api_key}

    try:
        print(owm_req.format(**fill))
        r = requests.get(owm_req.format(**fill))
    except requests.exceptions.RequestException as e:
        print("Failed to get weather information. '%s'" % e)
        return "Failed to get weather information for %s" % location

    condition = "{main} ({description})".format(
        main=r.json()['weather'][0]['main'],
        description=r.json()['weather'][0]['description'])

    fill = {"name": r.json()['name'],
            "condition": condition,
            "temp": int(kelvin_to_fahrenheit(r.json()['main']['temp'])),
            "hi_temp": int(kelvin_to_fahrenheit(r.json()['main']['temp_max'])),
            "lo_temp": int(kelvin_to_fahrenheit(r.json()['main']['temp_min']))}

    description = "Weather in *{name}*\n" \
                  ">Temperature: *{temp}° F*\n" \
                  ">High temp: *{hi_temp}° F*\n" \
                  ">Low temp: *{lo_temp}° F*\n" \
                  ">Conditions: *{condition}*\n" \
                  "".format(**fill)

    if fill['temp'] < 45:
        description += "Wear something really warm!"
    elif fill['temp'] < 60 and fill['temp'] >= 45:
        description += "Take a sweater!"
    else:
        description += "Enjoy!"

    return description


def get_xkcd(latest=False):
    """
      'xkcd'
      returns a random xkcd comic
    """

    import random

    xkcd_api = 'http://xkcd.com/{comic_id}/info.0.json'
    max_id_num = int(requests.get('http://xkcd.com/info.0.json').json()['num'])
    print('Most recent comic: %d' % max_id_num)
    if not latest:
        comic_num = random.randint(1, max_id_num)
    else:
        comic_num = max_id_num
    print('Comic chosen: %d' % comic_num)
    try:
        resp = requests.get(xkcd_api.format(comic_id=comic_num))
    except requests.exceptions.RequestException as e:
        print("Failed to retrieve comic: %s" % e)
        return "Failed to retrieve comic :("

    response = '*{safe_title}*\n({month}/{day}/{year})\n{img}\n_{alt}_'

    return response.format(**resp.json())


def say_greeting(command):
    import random
    responses = ('hello!', 'hi!', 'howdy!', 'hey!', 'aloha!')
    if 'hello' in command or 'hi' in command:
        r_number = iandom.randint(len(responses))
        response = responses[r_number]
    elif 'morning' in command:
        response = 'Good morning lovely human! Make some great maps today.'

    return response


def get_latlng(location):
    """
        'latlng'
        get the latlng of a given place
    """

    api_template = "https://maps.googleapis.com/maps/api/geocode/json" \
                   "?address={location}&key={apikey}"

    try:
        fill = {'location': location,
                'apikey': os.environ.get("GMAPS_APIKEY")}

        print('API Request: %s' % api_template.format(**fill))

        resp = requests.get(api_template.format(**fill))
    except requests.exceptions.RequestException as e:
        print('Failed to get Lat/Long from Google Maps service: %s' % e)
        return 'Failed to get Lat/Lng from Google Maps service'

    fill['lat'] = resp.json()['results'][0]['geometry']['location']['lat']
    fill['lng'] = resp.json()['results'][0]['geometry']['location']['lng']
    fill['location'] = resp.json()['results'][0]['formatted_address']

    return '*{lat},{lng}* is the lat/lng of of *{location}*.'.format(**fill)


def get_help():
    """
      'help'
      prints currently available commands with samples
    """
    command_help = "@andy_bot tries to help!\n\n" \
                   "Summon me like this: `@andy_bot: command`\n\n" \
                   "Available commands are:\n\n"

    command_template = "*{usage}*\n" \
                       "> Example: _{example}_\n" \
                       "> Response: _{explanation}_\n"

    for k in available_commands:
        fill = {'command': k,
                'usage': available_commands[k][0],
                'example': available_commands[k][1],
                'explanation': available_commands[k][2]}

        command_help += command_template.format(**fill)

    return command_help


def handle_command(command, channel):
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """
    response = "Not sure what you mean. Use the *" + EXAMPLE_COMMAND + \
               "* command with numbers, delimited by spaces."
    if command.startswith(EXAMPLE_COMMAND):
        response = "Sure...write some more code then I can do that!"
    elif command.startswith('weather'):
        # tell the weather
        # format: weather place name
        if 'evening commute' in command:
            response = "*Your evening commute weather!*\n\n"
            if 'nyc' in command:
                response += get_weather('brooklyn, new york')
            elif 'denver' in command:
                response += get_weather('denver, colorado')
        else:
            response = get_weather(command.split('weather')[1].strip())
    elif command.startswith('xkcd'):
        # get random xkcd comic
        if 'latest' in command:
            response = get_xkcd(latest=True)
        else:
            response = get_xkcd()
    elif command.startswith('help'):
        # print current commands
        response = get_help()
    elif command.startswith('latlong') or command.startswith('latlng'):
        # retrieve lat/long of input location
        if command.startswith('latlng'):
            stem = 'latlng '
        else:
            stem = 'latlong '

        response = get_latlng(command.split(stem)[1])
    elif 'morning' in command.lower():
        response = say_greeting(command)

    slack_client.api_call("chat.postMessage", channel=channel,
                          text=response, as_user=True)


def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        This parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    # print commands sent through Slack
    if len(slack_rtm_output) > 0:
        for c in slack_rtm_output:
            if c['type'] != 'presence_change':
                print("Command intercepted: %s" % slack_rtm_output)

    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                # return text after the @mention, whitespace removed
                return output['text'].split(AT_BOT)[1].strip().lower(), \
                       output['channel']
    return None, None

if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1  # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        print("StarterBot connected and running!")
        told_weather = False
        while True:
            command, channel = parse_slack_output(slack_client.rtm_read())
            now_time = datetime.now().time()
            if command and channel:
                print('command', command, 'channel', channel)
                handle_command(command, channel)
            elif now_time > time(16, 45) and not told_weather:
                # print evening commute weather in #research channel
                # TODO: change this to #newyorkoffice
                handle_command('weather evening commute nyc', 'C0AF8Q25N')
                hanlde_command('weather evening commute denver', 'C0AF8Q25N')
                # TODO: give special warning if it is going to rain on the
                #        commute home
                told_weather = True
            t.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")
