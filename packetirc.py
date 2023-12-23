#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
 ______            _               _____ ______   ______
(_____ \          | |         _   (_____|_____ \ / _____)
 _____) )___  ____| |  _ ____| |_    _   _____) ) /
|  ____/ _  |/ ___) | / ) _  )  _)  | | (_____ (| |
| |   ( ( | ( (___| |< ( (/ /| |__ _| |_      | | \_____
|_|    \_||_|\____)_| \_)____)\___|_____)     |_|\______)

PacketIRC is a bandwidth-conscious IRC client specifically designed for packet radio communication.
It includes a client-side implementation with simplified IRC functionalities.

File: client.py
Author: Daria Juniper @juniberry
Date: 10-Dec-2023

Changes:
12-Dec-2023 - Initial version 1.0 beta.

"""
import socket
import threading
import random
import time
import logging
import re
import irc.client
import os
import sys

# Import settings from an external configuration file.
from settings import LOG_FILE, LOG_LEVEL, SERVER, PORT, PASS, CHANNEL, HIDE_SERVER, MAX_RETRIES, RETRY_DELAY, HELP_INFO, WELCOME_MESSAGE, BAD_WORDS_FILE, BAD_WORDS_FILTER


# Globals
VERSION = 'v1.1b'
BAD_WORDS = []
HOME_PATH = os.path.dirname(os.path.abspath(__file__)) # Grab home path for use with logging et al.

# State
is_running = True

# Initialize logging.
logging.basicConfig(filename=os.path.join(HOME_PATH, LOG_FILE), filemode='w', level=LOG_LEVEL, format='%(asctime)s - %(levelname)s - %(message)s')

# PacketIRC Client Class
class PacketIRCClient(irc.client.SimpleIRCClient):
    """
    PacketIRCClient class extends irc.client.SimpleIRCClient.
    It includes methods for handling various IRC events and actions.
    """
    def __init__(self, callsign):
        """
        Initialize the IRC client with a callsign and current_channel property.
        The callsign should be passed from the packet switch and the client is
        designed to only operate on a single channel for sanity/bandwidth.
        """
        super().__init__()
        self.callsign = callsign
        self.current_channel = None

    def on_disconnect(self, connection, event):
        global is_running

        is_running = False
        logging.info(f"{callsign} Disconnected from server.")
        print("** Disconnected.")

    def on_error(self, connection, event):
        """
        Handle any errors encountered during the IRC session.
        We will not inform the user since many of these errors can be unhelpful
        or contain information you dont wish broadcast on the air. So we log it.
        """
        logging.error(f"{callsign} on_error(): {event}")

    def on_motdstart(self, connection, event):
        """
        Triggered when the MOTD listing begins.
        """
        print("** Message of the Day")

    def on_motd(self, connection, event):
        """
        Dump out lines of the MOTD
        Apparently this is only fired once? But could be multiple times?
        """
        for line in event.arguments:
            print(line)

    def on_notice(self, connection, event):
        """
        Handle Notices
        Notices can come from the server, users and sometimes seemingly out of the aether.
        """
        source = event.source.nick if event.source else "SERVER"
        text = event.arguments[0]
        print(f"-{source}- {text}")

    def on_welcome(self, connection, event):
        """
        Triggered when initially connected to an IRC server.
        We are going to use this to set up our initial channel if set in settings.
        """
        server_name = connection.get_server_name()
        print(f"** Connected to {server_name}")

        # Request client send a keepalive message every 30 sec.
        connection.set_keepalive(30)

        # If CHANNEL is specified in settings.py then join it.
        if CHANNEL:
            connection.join(CHANNEL)

    def on_whoisuser(self, connection, event):
        """
        Triggered when the server returns query info for a WHOIS
        """
        nick = event.arguments[0]
        username = event.arguments[1]
        hostname = event.arguments[2]
        server = event.arguments[3]
        real_name = event.arguments[4]

        print(f"** WHOIS for {nick}")
        print(f"   {username}@{hostname}")
        # Not all IRCd's will return the server, so this needs to be optional.
        if not all(char in ' *' for char in server):
            print(f"   Server: {server}")
        print(f"   Name: {real_name}")

    def on_nicknameinuse(self, connection, event):
        """
        Nickname is in use!
        Oh noes!  Let's do something silly like randomly pick a number, tack that on
        to the callsign and back away slowly............ >_>
        """
        self.callsign += "_" + str(random.randint(0, 999))
        connection.nick(self.callsign)

    def on_join(self, connection, event):
        """
        Triggered when the user joins a channel (including the user).
        If this is us joining a channel, action it as such.
        If this is a new user joining our channel, action it as....
        """
        nickname = event.source.nick
        channel = event.target
        # If the target of the notice is us, we're the ones joining.
        if nickname == self.connection.get_nickname():
            # Reset current channel if we're joining a new one
            self.current_channel = channel
            print(f"** Joined {channel}")

            # Request the topic for the new channel
            connection.topic(channel)
        else:
            # Nope, just another luser joining the idle sesh.
            print(f"* {nickname} has joined {channel}")

    def on_part(self, connection, event):
        """
        Triggered when a luser leaves a channel.
        """
        nickname = event.source.nick
        channel = event.target
        reason = event.arguments[0] if event.arguments else ""
        print(f"* {nickname} has left {channel} ({reason})")

    def on_namreply(self, connection, event):
        """
        Triggered when joining a channel or requesting NAMES.
        """
        channel = event.arguments[1]
        names = event.arguments[2].split()

        # Print the names directly
        print(f"Users in {channel}: {', '.join(names)}")

    def on_quit(self, connection, event):
        """
        Triggered when a luser quits in a channel we are in.
        """
        nickname = event.source.nick
        reason = event.arguments[0] if event.arguments else ""
        print(f"* {nickname} has quit ({reason})")

    def on_privmsg(self, connection, event):
        """
        Triggered when a user sends us a directed PRIVMSG.
        """
        sender = event.source.nick
        message = event.arguments[0]
        print(f"** {sender}: {message}")

    def on_pubmsg(self, connection, event):
        """
        Triggered from a PRIVMSG sent to a channel we are in.
        """
        # Handle public messages received in the channel
        nickname = event.source.nick
        message = event.arguments[0]
        print(f"<{nickname}> {message}")

    def on_action(self, connection, event):
        """
        Triggered by emotive ACTIONs, be they on a channel or directed.
        """
        nickname = event.source.nick
        message = event.arguments[0]
        channel = event.target
        print(f"* {nickname} {message}")

    def on_topicprotected(self, connection, event):
        """
        Apparently this is supposed to trigger when we try to change the topic
        but are not permitted to.
        """
        print(f"** You don't have permission to change the topic.")
        # TODO:
        ## User doesn't have perm to set topic.
        ## This seems to be broken?

    def on_topic(self, connection, event):
        """
        Triggered by the server to indicate that the topic has been changed.
        """
        who = event.source.nick
        #channel = event.target
        new_topic = event.arguments[0]

        print(f"* {who} changed the topic to: {new_topic}")

    def on_currenttopic(self, connection, event):
        """
        Triggered by the server to indicate the current topic of a channel, from our query request.
        """
        channel = event.arguments[0]
        topic = event.arguments[1]
        print(f"** {channel}: {topic}")

    def on_list(self, connection, event):
        """
        Handles the event for LISTing channels. This method is called for each channel in the list.
        This can be a firehose ...we might want to put a flood or limit on this eventually...soon..ish
        """
        channel = event.arguments[0] if event.arguments else ''
        user_count = event.arguments[1] if len(event.arguments) > 1 else ''
        topic = event.arguments[2] if len(event.arguments) > 2 else ''

        # Truncate topic to 60 characters if longer.
        if len(topic) > 60:
            topic = topic[:57] + '...'

        print(f"{channel} [{user_count}] {topic}")


def handle_user_input(irc_client):
    """
    Continuously handle user input and processes IRC style commands.
    This handler is run within it's own thread aside from the PacketIRC client class.
    """
    global is_running

    # Threaded runloop. Toggle is_running to False to exit the user interface thread.
    while is_running:
        try:
            # Fetch user input, strip whitespace and log it.
            message = input().strip()
            logging.info(f"{callsign} >>> {message}")

            # Check to see if the user message is a command.
            if message.startswith('/'):
                # It likely is, try to process it.
                #
                # Split the message into command and command_args
                parts = message.split(' ', 1)
                command = parts[0].lower()
                command_args = parts[1] if len(parts) > 1 else ""

                # /QUIT - Disconnect and exit with optional quit message.
                if command == '/quit':
                    # Set the running state flag off, to exit thread runloop.
                    is_running = False

                    # If the user specified a message, use it, otherwise plug in 73.
                    quit_message = command_args if command_args else "73"

                    # We checking for naughty words? If so clean them.
                    if BAD_WORDS_FILTER:
                        quit_message = filter_input(quit_message)

                    ## TODO FIX
                    ## Custom quit message is not working.
                    # Perform the quit action and break out of the loop.
                    irc_client.connection.quit(message=quit_message)
                    break

                # /MSG - Send a private message to another user.
                elif command == '/msg':
                    # Split the command up into a user and the message to them.
                    parts = command_args.split(' ', 1)

                    # Did the user provide a target user and message?
                    if len(parts) == 2:
                        target_nickname, message_to_send = parts

                        # Wash their mouths out if we're in the buisness of doing that.
                        if BAD_WORDS_FILTER:
                            message_to_send = filter_input(message_to_send)

                        # Send a PRIVMSG to the specified user.
                        irc_client.connection.privmsg(target_nickname, message_to_send)
                    else:
                        # Nope, so scold them.
                        print("Usage: /msg <nickname> <message> - Sends a private message to the specified user.")

                # /JOIN - Join a specified channel.
                elif command == '/join':
                    if command_args:
                        # Check if the user is trying to join a valid channel name
                        if is_valid_channel_name(command_args):
                            # Part from the current channel if already joined to one.
                            if irc_client.current_channel:
                                # Provide a canned PART message to inform existing users incase they want to follow.
                                irc_client.connection.part(irc_client.current_channel, message="Switching to {command_args}")

                            # Join the new channel.
                            irc_client.connection.join(command_args)
                        else:
                            # The user input an invalid channel name, tell them.
                            print("** Invalid channel name.")
                    else:
                        # Not enough parameters, give'em a talkin' to.
                        print("Usage: /join <channel> - Joins the specified channel.")

                # /PART - Leave the channel we are in.
                elif command == '/part':
                    # Are we even in a channel? If so, let's leave it.
                    if irc_client.current_channel:
                        # Did they provide a parting message? If not let's plug in "Leaving"
                        part_message = command_args if command_args else "Leaving"

                        # Do that censorship thing if we're puritans.
                        if BAD_WORDS_FILTER:
                            part_message = filter_input(part_message)

                        # Part the channel
                        irc_client.connection.part(irc_client.current_channel, message=part_message)

                        # Tell the user we have left the channel.
                        print(f"** Left {irc_client.current_channel}")

                        # Clear the current_channel for state control.
                        irc_client.current_channel = None
                    else:
                        # They're not the only one who's confuzzled.
                        print("** You are not currently in any channel.")

                # /NICK - Process nickname changes.
                elif command == '/nick':
                    # Did they specify a parameter?
                    if command_args:
                        # Yep, use it as the new nickname.
                        irc_client.connection.nick(command_args)
                    else:
                        # Nope, inform them of their error.
                        print("Usage: /nick <nickname> - Changes your nickname.")

                # /LIST - Drink from the firehose. This should be fun -.-
                elif command == '/list':
                    # Request a channel listing from the server.
                    irc_client.connection.list()

                # /TOPIC - Set the topic if the user provides args, print the current topic if not.
                elif command == '/topic':
                    # Are we even in a channel?
                    if irc_client.current_channel:
                        if command_args:
                            # We got args, lets set a new topic for the current channel

                            # There is more profanity on amateur radio than women.
                            # True facts are true.
                            if BAD_WORDS_FILTER:
                                topic = filter_input(command_args)

                            # Send the new topic command.
                            irc_client.connection.topic(irc_client.current_channel, new_topic=topic)
                        else:
                            # No args, so let's request the topic for the current channel.

                            ## TODO FIX
                            ## This is broken, does not return the current topic.
                            channel = irc_client.connection.current_channel
                            irc_client.connection.topic(irc_client.current_channel)
                    else:
                        # Not in a channel, inform them of their confuzzlement.
                        print("** You are not currently in any channel.")

                # /AWAY - Flag as away and optionally with an away message.
                elif command == '/away':
                    # Did the user specify an optional away message? If not plug in "AFK"
                    away_message = command_args if command_args else "AFK"

                    # We doing that bad work check? If so do it.
                    if BAD_WORDS_FILTER:
                        away_message = filter_input(away_message)

                    # Set client into away state with message.
                    irc_client.connection.send_raw(f"AWAY :{away_message}")

                # /ME - Perform an emotive action ...or any action really.
                elif command == '/me':
                    # Are we in a channel?
                    if irc_client.current_channel:
                        # We are, check to see the user provided args.
                        action_message = command_args
                        if action_message:

                            # Are we removing the fun again?
                            if BAD_WORDS_FILTER:
                                action_message = filter_input(command_args)
                            
                            # Send off the action.
                            irc_client.connection.action(irc_client.current_channel, action_message)
                        else:
                            # Inform them on the usage since they failed to provide args.
                            print("Usage: /me <action> - Performs an action.")
                    else:
                        # It helps if you are, really.
                        print("** You are not currently in any channel.")

                # /WHOIS - Our most favourite of IRC commands.
                elif command == '/whois':
                    ## TODO FIX
                    ## Returns nothing if the user is non-exist.

                    # We require args, check for them.
                    if command_args:
                        # Fantastic, fire off the whois query.
                        irc_client.connection.whois(command_args)
                    else:
                        # Tell the user we need those args.
                        print("Usage: /whois <nickname> - Retrieves information about the specified user.")

                # /NAMES - Lists the lusers in the current channel.
                elif command == '/names':
                    # Are we in a channel?
                    if irc_client.current_channel:
                        # Yepo, fire off the query, handle the results in an event.
                        irc_client.connection.names(irc_client.current_channel)
                    else:
                        # Again, it helps.
                        print("** You're not currently in any channel.")

                # /SLAP - The most useful of all the commands.
                elif command == '/slap':
                    # We need to be in a channel to use this emote. And we need a victi...target.
                    if irc_client.current_channel:
                        if command_args:
                            action_message = f"slaps {command_args} around a bit with some coax."
                            irc_client.connection.action(irc_client.current_channel, action_message)
                        else:
                            # Did you expect me to use a fish? pfft.
                            print("Usage: /slap <nickname> - Slaps a user around a bit with some coax.")
                    else:
                        # You know the drill by now.
                        print("** You are not currently in any channel.")

                # /LID - I made this up because I felt like it.
                elif command == '/lid':
                    if irc_client.current_channel:
                        if command_args:
                            action_message = f"presses the LID alarm while looking at {command_args}."
                        else:
                            # If the user didnt pass a target, assume they're the LID.
                            action_message = "may possibly be a LID."
                        irc_client.connection.action(irc_client.current_channel, action_message)                        
                    else:
                        # ...
                        print("** You are not currently in any channel. Are you the LID?")

                # /HELP - Prints commands and their usage from the settings.py file.
                elif command == '/help':
                    print(HELP_INFO)

                #
                # TODO: MOAR NEW COMMANDS GO HERE
                #

                # Invalid command ..?
                else:
                    print("Unknown command.")

            else:
                # Test for link level disconnect message such if the RF link drops or is DC'd
                # eg: "*** Disconnected from Stream 10"
                if message.startswith('*** Disconnected from'):
                    # Discard this message and close the connection.
                    # ..If the user manually typed this for the lulz, ...oh well.
                    ## TODO FIX
                    ## Encap commands into their own functions, clean this up.
                    is_running = False
                    irc_client.connection.quit()

                # User input is just a channel PRIVMSG.

                # Are we even in a channel?!
                if irc_client.current_channel:
                    # Are we filtering for bad words?
                    if BAD_WORDS_FILTER:
                        # Yep, wash their mouth out.
                        message = filter_input(message)

                    # Send the PRIVMSG to the current channel.
                    irc_client.connection.privmsg(irc_client.current_channel, message)
                else:
                    # We're not joined to a channel, so scold them.
                    print("** You are not currently in any channel.")

        except (EOFError, KeyboardInterrupt):
            # Handle Ctrl-D or Ctrl-C gracefully...ish
            is_running = False
            if irc_client.is_connected():
                irc_client.connection.disconnect('Disconnected')
            break
        except Exception as e:
            # Log the unexpected error and try to continue on as if nothing happened! ^.^
            logging.error("{callsign} handle_user_input: Ignoring unexpected error: {e}")
            continue

"""
  (\(\ 
  (-.-) zZzZZZzzZz
 o_(")(")
"""

def is_valid_channel_name(channel_name):
    """
    Checks if a given string is a valid IRC channel name.
    Valid channel names start with '#' or '&' and must not contain spaces, commas, or control characters.
    """
    # Regular expression for a valid channel name
    pattern = r'^[#][^\s,]+$'

    # Using re.match to check if the channel name fits the updated pattern
    return bool(re.match(pattern, channel_name))

def load_bad_words(file_path):
    """
    Load a file of banned words (one per line) into an array for message filtering.
    """
    global BAD_WORDS

    try:
        with open(file_path, 'r') as file:
            BAD_WORDS = [word.strip() for word in file.readlines()]
    except FileNotFoundError:
        # User error, let's just log it and continue like nothing happened >_>
        logging.error(f"***MISSING BAD_WORDS FILE*** {file_path} not found!")

def filter_input(input_text):
    """
    Filter input_text against the BAD_WORDS array.
    Any banned words will be replaced with '!!!'
    """
    global BAD_WORDS

    for word in BAD_WORDS:
        input_text = input_text.replace(word, '!!!')

    return input_text

def main(callsign):
    """
    main()
    First we load the banned words, initialize the class, welcome the user.
    Then we attempt to connect to the IRC server.
    If we connect, we then kick off the user input handler thread and enter the
    main run loop where we marshall the irc client thread and check for valid run state.
    Once everything is done doing what it should be doing we close up shop.
    """
    global is_running

    # Are we filtering for bad words?! If so, load it.
    if BAD_WORDS_FILTER:
        load_bad_words(os.path.join(HOME_PATH, BAD_WORDS_FILE))

    # Instantiate IRC Client class 
    client = PacketIRCClient(callsign)

    # Have a little ego trip
    print(f"PacketIRC {VERSION}")
    print(WELCOME_MESSAGE, flush=True)

    # Connect the client or retry on failure
    retry_count = 0
    while True:
        try:
            logging.info(f"{callsign}: Connecting to {SERVER}:{PORT}")

            # Show user the server info?
            if HIDE_SERVER:
                print("Connecting to server...", flush=True)
            else:
                print(f"** Connecting to {SERVER}:{PORT}", flush=True)

            ## TODO: maybe add in interwebs lookup for callsign Name??
            # Strip the SSID value from a callsign to it's base call since this causes ident issues
            base_call = re.match(r'^[A-Z0-9]+', callsign).group()
            client.connect(SERVER, PORT, callsign, password=PASS, username=base_call, ircname=base_call)
            break
        except irc.client.ServerConnectionError as e:
            # Handle connection errors by checking retry count and giving it another shot if under.
            logging.error(f"{callsign}: Error connecting to server: {e}")
            print(f"** Error connecting to server: {e}", flush=True)
            retry_count += 1

            # Keep trying or throw in the towel?
            if retry_count < MAX_RETRIES:
                logging.error(f"{callsign}: Retrying connection to {SERVER}:{PORT} in {RETRY_DELAY} seconds.")
                print(f"** Retrying in {RETRY_DELAY} seconds...", flush=True)
                time.sleep(RETRY_DELAY)
            else:
                # Yeah, we done here.
                logging.error(f"{callsign}: Maximum retries reached. Exiting.")
                print(f"Unable to connect to {SERVER}:{PORT}", flush=True)
                print(f"Please try again later, exiting.", flush=True)
                return
        except (socket.timeout, socket.error) as e:
            # Something screwy is going on, tell the user, log it and exit.
            logging.error(f"{callsign}: Socket error occurred: {e}")
            print("** Socket error occurred: {e}", flush=True)
            return

    # If we got this far, we're connected and good to start the threading.
    # Spool up a thread to handle user input.
    input_thread = threading.Thread(target=handle_user_input, args=(client,))
    input_thread.daemon = True
    input_thread.start()

    # Main run loop
    try:
        while is_running:
            # Flush stdout buffer to ensure the Packet Switch moves the IO.
            sys.stdout.flush()
            
            # Spin the irc client thread
            client.reactor.process_once(timeout=0.2)
    except irc.client.ServerNotConnectedError:
        # We got disconnected, shut down everything!
        logging.error(f"{callsign} Lost connection to the server.")
        print("** Lost connection to the server.", flush=True)
    except Exception as e:
        # What is this, I'm not even supposed to be here today... log it.
        logging.error(f"{callsign} Unexpected error: {e}")
        print(f"** Unexpected error has occurred: {e}", flush=True)
    finally:
        if client.connection.is_connected():
            client.connection.disconnect()

    # Wait for the user input thread to finish, but not too long!
    input_thread.join(timeout=5)

    # Exit stage left.
    print("Exiting PacketIRC, 73.")


if __name__ == "__main__":
    """
    Grab the users callsign from the Packet Switch. Complain and exit if it's blank.
    If we have something start up the client class.
    """
    global callsign

    # Get the user callsign, this will be the first input on stdin from the Packet Switch
    # provided that the APPLICATION line is configured to pass it, which is should be! RTFM!
    callsign = input().strip()

    # They didn't RTFM or this is cli invoked ...improperly.
    if not callsign:
        print("Callsign not passed, check your APPLICATION line. Exiting!")
        logging.error("Packet Switch did not pass a callsign, exiting!")
        sys.exit(1)

    logging.info(f"Starting client for {callsign}")
    main(callsign)
