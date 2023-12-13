# PacketIRC

PacketIRC is a bandwidth-conscious IRC (Internet Relay Chat) client, specifically designed for packet radio communication. It offers a client-side implementation with simplified IRC functionalities tailored for efficient use over low-bandwidth connections.

## Features

- Simplified IRC client for packet radio.
- Customizable settings through an external configuration file.
- Bandwidth-efficient communication.
- Logging capabilities for debugging and record-keeping.
- User-friendly commands for IRC interaction.
- Bad word filtering for clean communication.
- Handles various IRC events and actions.

## Installation

### Prerequisites

- Python 3
- `irc` package

### Setup

1. Clone the repository or download the source code.
2. Install dependencies: `pip install -r requirements.txt`.
3. Configure the `settings.py` file with your IRC server details and preferences.
4. Leverage xinet.d or inet.d to serve up the script via a tcp port.
5. Add the port you choose to your /etc/services file.
5. Configure BPQ or your Packet Switch to connect to the application tcp port such that it will pass the users callsign and optionally return to the node on exit.
6. ...
7. Profit

### Example BPQ32 Configuration
- CMDPORT is a 0 indexed list of ports which point to local applications.
- The C 15 is "CONNECT VIA PORT 15" which is TELNET in this configuration to localhost CMDPORT index 0 which is 1234 in this example.
- The S means return to Node on completion instead of dropping the connection.
```
PORT
PORTNUM=15
 ID=Telnet
 DRIVER=TELNET
 ...
 CONFIG
  ...
  CMDPORT=1234 6000 6001 6002
  ...
ENDPORT

APPLICATION 10,IRC,C 15 HOST 0 S
```

### Example xinetd Service Definition
/etc/services (at the end of the file)
```
packetirc       1234/tcp
```

/etc/xinet.d/packetirc
```
service packetirc
{
    port            = 1234
    socket_type     = stream
    protocol        = tcp
    wait            = no
    user            = nobody
    server          = /home/bpq/PacketIRC/packetirc.py
    disable         = no
}
```

## Manual Usage

1. Run the script: `python3 packetirc.py`
2. Enter your callsign when it appears to be doing nothing (BPQ passes callsign first thing).

## Commands

- `/quit`: Disconnect and exit.
- `/msg <nickname> <message>`: Send a private message.
- `/join <channel>`: Join a specified channel.
- `/part`: Leave the current channel.
- `/nick <nickname>`: Change your nickname.
- `/list`: List available channels.
- `/topic <topic>`: Change or view the channel topic.
- `/away <message>`: Set an away message.
- `/me <action>`: Perform an action.
- `/whois <nickname>`: Get information about a user.
- `/names`: List users in the current channel.
- `/slap <nickname>`: A fun command to "slap" another user.
- `/lid`: A custom command for special operators.
- `/help`: Display help information.

## Configuration

Edit `settings.py` to configure the following:

- Server details (address, port, password)
- Default channel
- Logging settings
- Bad words filter and file path
- Custom message for command help

## Contributing

Contributions are welcome. Please open issues for any bugs or feature requests and submit pull requests for any improvements.

