# -*- coding: utf-8 -*-
"""
 ______            _               _____ ______   ______
(_____ \          | |         _   (_____|_____ \ / _____)
 _____) )___  ____| |  _ ____| |_    _   _____) ) /
|  ____/ _  |/ ___) | / ) _  )  _)  | | (_____ (| |
| |   ( ( | ( (___| |< ( (/ /| |__ _| |_      | | \_____
|_|    \_||_|\____)_| \_)____)\___|_____)     |_|\______)

PacketIRC - A simple bandwidth concious IRC client server for packet radio.

File: settings.py
Author: Daria Juniper @juniberry
Date: 10-Dec-2023

"""
import logging

# Logging
LOG_FILE = "packetirc.log"
LOG_LEVEL = logging.INFO

# IRC server settings
SERVER = ""
PORT = 6667
PASS = ""
HIDE_SERVER = True
MAX_RETRIES = 3
RETRY_DELAY = 5 # seconds

# Default channel to join (optional)
CHANNEL = "#Testing"

# Custom welcome message to be displayed when the client starts
WELCOME_MESSAGE = """
Welcome to PacketIRC!
Type /help for a list of commands.
"""

# Bad word dictionary file for those who enjoy censorship
#    Note: You will have to populate that file yourself.
BAD_WORDS_FILTER = False
BAD_WORDS_FILE = "bad_words.txt"

# The /help info
HELP_INFO = """
PacketIRC commands:
  /quit [message] - Disconnect from the server with optional message.
  /msg <nickname> <message> - Send a private message to the specified user.
  /join <channel> - Join the specified channel.
  /names - Shows a list of users in the channel.
  /topic [new topic] - Set a new topic for the current channel or request the topic.
  /away [message] - Set an away message or clear the away status.
  /whois <nickname> - Retrieves information about the specified user.
  /help - Display this help message.
"""
