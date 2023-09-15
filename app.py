import json
import logging

from exactapi import EXACTAPI

API_USERNAME = "my-username"
API_PASSWORD = "my-password"

LOGFILE = "exafore.log"
LOGFORMAT = "%(message)s"

# Run the ifconfig command on EXL server to get server's IP address.
HOST = "172.17.128.162"
PORT = 8000


def on_notification(message: dict, logger: logging.Logger):
    """
    Called when a notification message is received from the EXL server.

    :param message: Received notification message.
    :param logger: Logger object.

    """
    logger.debug(json.dumps(message))


def main():
    logging.basicConfig(filename=LOGFILE, format=LOGFORMAT, level=logging.DEBUG)
    logger = logging.getLogger()

    client = EXACTAPI(host=HOST, port=PORT)
    client.connect()
    client.login(username=API_USERNAME, password=API_PASSWORD)
    client.channel_join(channel=["measurements", "solution"])
    client.channel_list()
    client.recv_notification(callback=on_notification, logger=logger)
    client.channel_leave(channel=["measurements", "solution"])
    client.logout()
    client.disconnect()


if __name__ == "__main__":
    main()
