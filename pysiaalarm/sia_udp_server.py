"""This is the class for the actual TCP handler override of the handle method."""
import logging
from typing import Callable, Dict, Tuple
import socket
import struct
import binascii

from . import __author__, __copyright__, __license__, __version__
from .base_sia_server import BaseSIAServer
from .sia_account import SIAAccount
from .sia_account import SIAResponseType as resp
from .sia_event import SIAEvent

_LOGGER = logging.getLogger(__name__)


class SIAUDPServer(BaseSIAServer):
    """Class for a threaded SIA Server."""

    daemon_threads = True
    allow_reuse_address = True

    def __init__(
        self,
        server_address: Tuple[str, int],
        accounts: Dict[str, SIAAccount],
        func: Callable[[SIAEvent], None],
        counts: Dict,
    ):
        """Create a SIA UDP Server.

        Arguments:
            server_address Tuple[string, int] -- the address the server should listen on.
            accounts Dict[str, SIAAccount] -- accounts as dict with account_id as key, SIAAccount object as value.
            func Callable[[SIAEvent], None] -- Function called for each valid SIA event, that can be matched to a account.
            counts Dict -- counter kept by client to give insights in how many errorous events were discarded of each type.

        """
        BaseSIAServer.__init__(self, accounts, func, counts)
        self.server_address = server_address
        self.sock = None
        
    def shutdown(self):
        self.shutdown_flag = True
    
    def server_close(self):
        if self.sock:
            self.sock.close()
    
    def serve_forever(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(self.server_address)
        self.sock.settimeout(0.1)

        while True and not self.shutdown_flag:
            try:
                raw, wherefrom = self.sock.recvfrom(1024)
            except:
                continue
            if not raw:
                break
            line = bytearray(raw)

            fixup = True
            if fixup:
                crc = line[1:3]
                line = line[3:]
                crc = ("%x" % struct.unpack('!H', crc)[0]).upper().zfill(4)
                line = crc.encode("ascii") + line
            decoded_line = line.decode("ascii").replace("\r", "")
            _LOGGER.debug("Incoming line: %s", decoded_line)
            self.counts["events"] = self.counts["events"] + 1
            event, account, response = self.parse_and_check_event(
                decoded_line
            )
            try:
                self.sock.sendto(account.create_response(event, response), wherefrom)
            except Exception as exp:
                _LOGGER.warning(
                    "Exception caught while responding to event: %s, exception: %s",
                    event,
                    exp,
                )
            Domoticz.Debug("Sent response.")
            # check for event and if the response is acknowledge, which means the event is valid.
            if event and response == resp.ACK:
                self.counts["valid_events"] = (
                    self.counts["valid_events"] + 1
                )
                try:
                    self.func(event)
                except Exception as exp:
                    _LOGGER.warning(
                        "Last event: %s, gave error in user function: %s.",
                        event,
                        exp,
                    )
                    self.counts["errors"]["user_code"] = (
                        self.counts["errors"]["user_code"] + 1
                    )
