import json
import ssl
import socket
from typing import Callable, List, Union

from pydantic import ValidationError

from exactapi import models

MAX_MESSAGE_LENGTH = 4096


class EXACTAPI:
    """
    EXACT API i.e. Exafore UWB Location Engine (EXL) JSON API.

    :param host: IP address of the EXL server.
    :param port: Port number of the EXL server.
    :param debug: If true, print messages to terminal.

    """
    def __init__(self, host: str, port: int, debug: bool = True) -> None:
        self.host = host
        self.port = port
        self.debug = debug
        
        self.connection = None
        self.message_id = 0


    def _handle_exception(self, exception: ValidationError) -> dict:
        """
        Handle the validation error of the pydantic model.

        :param exception: Validation error.

        """
        error = {
            "response": "exception",
            "errors": exception.errors(include_url=False),
        }
        if self.debug:
            print(error)
        return error


    def _send(self, request: models.BaseRequest):
        """
        Send a request message to the EXL server.

        :param request: Request model.

        """
        if self.connection is None:
            return
        self.message_id += 1
        request.msgid = self.message_id
        if self.debug:
            print(request.model_dump(exclude_none=True))
        message = f"{request.model_dump_json(exclude_none=True)}\n"
        self.connection.sendall(message.encode())
        

    def _recv(self, ismultielem: bool = False) -> Union[dict, List[dict]]:
        """
        Receive a response from the EXL server.

        :param ismultielem: True in case of multi-element response.
        :returns: Single-element or multi-element response.

        """
        response = {}  # single-element response
        elements = []  # multi-element response
        if self.connection is None:
            if ismultielem is True:
                return elements
            return response
        while True:
            message = self.connection.recv(MAX_MESSAGE_LENGTH).decode()
            response = dict(json.loads(message))
            response_type = response.get("response", "")
            if self.debug:
                print(response)
            if ismultielem:
                elements.append(response)
            # Acknowledge response, end of multi-element response, or
            # error response.
            if response_type in ("ack", "end", "error"):
                break
            # Single-elemet response of type 'element'.
            if response_type == "element" and ismultielem is False:
                break
        if ismultielem is True:
            return elements
        return response


    def recv_notification(self, callback: Callable = None, **kwargs):
        """
        Receive notification message(s) from the EXL server.

        :param callable: Function to call when a notification is received.
        :param kwargs: Keyword arguments for the callback function.

        """
        if self.connection is None:
            return
        while True:
            try:
                message = self.connection.recv(MAX_MESSAGE_LENGTH).decode()
                notification = dict(json.loads(message))
                if self.debug:
                    print(notification)
                if callback:
                    callback(notification, **kwargs)
            except KeyboardInterrupt:
                break


    # -----------------------------------------------------------------
    # Connection
    # -----------------------------------------------------------------
    def connect(self):
        """
        Connect to the EXL server.

        :raises: ConnectionError if no connection to the server.

        """
        context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        context.verify_mode = ssl.CERT_NONE
        context.load_default_certs()

        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ssl_socket = context.wrap_socket(tcp_socket)
        err_number = ssl_socket.connect_ex((self.host, self.port))
        if err_number == 0:
            self.connection = ssl_socket
        else:
            raise ConnectionError(f"Error number: {err_number}")


    def disconnect(self):
        """Disconnect from the EXL server."""
        if self.connection is None:
            return
        self.connection.close()
    
    # -----------------------------------------------------------------
    # Authentication and Session Control
    # -----------------------------------------------------------------
    def login(self, username: str, password: str) -> dict:
        """
        Attempt to authenticate a user.

        :param username: Username for the user account.
        :param password: Password in plaintext.
        :returns: On success, the server responds with RPL_ACK message.

        """
        try:
            request = models.AuthLoginRequest(
                user=username,
                password=password
            )
            self._send(request)
            return self._recv()
        except ValidationError as exc:
            return self._handle_exception(exc)


    def logout(self) -> dict:
        """
        Log out from the current session and unsubscribe from any
        channels joined earlier. Does not close the connection, so it
        is possible to log in as another user.

        :returns: On success, the server responds with RPL_ACK message.

        """
        request = models.AuthLogoutRequest()
        self._send(request)
        return self._recv()


    def ping(self) -> dict:
        """
        Simple request/response sequence for test purposes. Authorization: USER.
        
        :returns: On success, the server responds with RPL_ACK message.

        """
        request = models.AuthPingRequest()
        self._send(request)
        return self._recv()


    # -----------------------------------------------------------------
    # User Accounts
    # -----------------------------------------------------------------
    def user_create(
            self,
            username: str,
            password: str,
            roles: List[str] = None,
            desc: str = None
        ) -> dict:
        """
        Create a new user account to the system. Authorization: ADMIN.

        :param username: Username of the user account.
        :param password: Password in plaintext.
        :param roles: Roles of the user account, "admin" and/or "user".
        :param desc: Human-readable description of the user account.
        :returns: On success, the server responds with RPL_ACK message.

        """
        try:
            request = models.UserCreateRequest(
                user=models.User(
                    login=username,
                    password=password,
                    roles=roles,
                    desc=desc
                )
            )
            self._send(request)
            return self._recv()
        except ValidationError as exc:
            return self._handle_exception(exc)
    

    def user_update(
            self,
            username: str,
            new_username: str = None,
            new_password: str = None,
            new_roles: List[str] = None,
            new_desc: str = None
        ) -> dict:
        """
        Update the user account information. Authorization: ADMIN.

        :param username: Username of the user account.
        :param new_username: New username
        :param new_password: New password in plaintext.
        :param new_roles: New roles of the user account, "admin" and/or
            "user". If the field is present, all previous roles are
            removed.
        :param desc: New human-readable description of the user account.
        :returns: On success, the server responds with RPL_ACK message.

        """
        try:
            request = models.UserUpdateRequest(
                user=models.UserUpdate(
                    login=username,
                    new_login=new_username,
                    new_password=new_password,
                    new_roles=new_roles,
                    new_desc=new_desc
                )
            )
            self._send(request)
            return self._recv()
        except ValidationError as exc:
            return self._handle_exception(exc)


    def user_remove(self, username: str) -> dict:
        """
        Remove a user account from the system. Authorization: ADMIN.

        :param username: Username of the user account.
        :returns: On success, the server responds with RPL_ACK message.

        """
        try:
            request = models.UserRemoveRequest(
                user=models.UserLogin(
                    login=username,
                )
            )
            self._send(request)
            return self._recv()
        except ValidationError as exc:
            return self._handle_exception(exc)


    def user_list(self) -> List[dict]:
        """
        List all user accounts in the system. Authorization: USER.

        :returns: On success, the server responds with a multi-element response.

        """
        request = models.UserListRequest()
        self._send(request)
        return self._recv(ismultielem=True)


    def user_get(self, username: str) -> dict:
        """
        Get the user account information. Authorization: ADMIN.

        :returns: On success, the server responds with a single-element response.

        """
        try:
            request = models.UserGetRequest(
                user=models.UserLogin(login=username)
            )
            self._send(request)
            return self._recv()
        except ValidationError as exc:
            return self._handle_exception(exc)


    # -----------------------------------------------------------------
    # System Configuration
    # -----------------------------------------------------------------
    def config_coordinates(
            self, 
            lat: float, 
            lon: float, 
            alt: float, 
            angle: float
        ) -> dict:
        """
        Configure the local reference frame. Authorization: ADMIN.

        Set the parameters for transforming the coordinates of the local
        XYZ frame to the global WGS84 frame.

        :param lat: Latitude of the origin.
        :param lon: Longitude of the origin.
        :param alt: Altitude of the origin.
        :param angle: Angle from WGS84 East direction anti-clockwise to
            local reference frame X-direction, in degrees.
        :returns: On success, the server responds with RPL_ACK.

        """
        try:
            request = models.ConfigCoordinatesRequest(
                origin=[lat, lon, alt],
                orientation=angle
            )
            self._send(request)
            return self._recv()
        except ValidationError as exc:
            return self._handle_exception(exc)


    def config_altitude(self, altitude: float) -> dict:
        """
        Set the default altitude of the system. Authorization: ADMIN.

        :param altitude: Altitude constraint in meters relative to zero altitude.
        :returns: On success, the server responds with RPL_ACK.

        """
        try:
            request = models.ConfigAltitudeRequest(altitude=altitude)
            self._send(request)
            return self._recv()
        except ValidationError as exc:
            return self._handle_exception(exc)


    def config_get(self, item: str) -> dict:
        """
        Query system configuration. Authorization: ADMIN.

        :param item: Configuration item to query, 'coordinates' or 'altitude'.
        :returns: On success, the server responds with a single-element response.

        """
        try:
            request = models.ConfigGetRequest(item=item)
            self._send(request)
            return self._recv()
        except ValidationError as exc:
            return self._handle_exception(exc)


    def config_reset(self) -> dict:
        """
        Reset all system config items to default values. Authorization: ADMIN.

        :returns: On success, the server responds with RPL_ACK.

        """
        request = models.ConfigResetAllRequest()
        self._send(request)
        return self._recv()

    # -----------------------------------------------------------------
    # Cells
    # -----------------------------------------------------------------
    def cell_add(
            self, 
            cell_id: str, 
            ip_addr: str, 
            port: int = None, 
            desc: str = None
        ) -> dict:
        """
        Add a new cell to the system. Authorization. ADMIN.

        :param cell_id: Unique hexadecimal ID of the cell.
        :param ip_addr: IP address of the master base station of the cell.
        :param port: Communication port number of the master base station.
        :param desc: Human-readable description.
        :returns: On success, the server responds with a single-element
            response indicating the hexadecimal ID for the added cell.

        """
        request = models.CellAddRequest(
            cell=models.Cell(
                id=cell_id,
                ip_address=ip_addr,
                port = port,
                desc = desc,
            )
        )
        self._send(request)
        return self._recv()


    def cell_update(
            self, 
            cell_id: str, 
            ip_addr: str = None, 
            port: int = None, 
            desc: str = None
        ) -> dict:
        """
        Add a new cell to the system. Authorization. ADMIN.

        :param cell_id: Unique hexadecimal ID of the cell.
        :param ip_addr: IP address of the master base station of the cell.
        :param port: Communication port number of the master base station.
        :param desc: Human-readable description.
        :returns: On success, the server responds with RPL_ACK.

        """
        request = models.CellUpdateRequest(
            cell=models.CellOptionalAddr(
                id=cell_id,
                ip_address = ip_addr,
                port = port,
                desc = desc
            )
        )
        self._send(request)
        return self._recv()


    def cell_remove(self, cell_id: str) -> dict:
        """
        Remove a cell from the system. Authorization: ADMIN.

        :param cell_id: Hexadecimal ID of the cell to be removed.
        :returns: On success, the server responds with RPL_ACK.

        """
        try:
            request = models.CellRemoveRequest(
                cell=models.DeviceID(id=cell_id)
            )
            self._send(request)
            return self._recv()
        except ValidationError as exc:
            return self._handle_exception(exc)


    def cell_remove_all(self) -> dict:
        """
        Remove all cells from the system. Authorization: ADMIN.

        :param cell_id: Hexadecimal ID of the cell to be removed.
        :returns: On success, the server responds with RPL_ACK.

        """
        request = models.CellRemoveAllRequest()
        self._send(request)
        return self._recv()


    def cell_list(self) -> List[dict]:
        """
        List all cells in the system. Authorization: USER.

        :returns: On success, the server responds with multi-element response.

        """
        request = models.CellListRequest()
        self._send(request)
        return self._recv(ismultielem=True)

    # -----------------------------------------------------------------
    # Base Stations
    # -----------------------------------------------------------------
    def bs_add(
            self, 
            bs_id: str, 
            cell_id: str,
            coordinates: List[float], 
            angle: int = 0, 
            desc: str = None,
        ) -> dict:
        """
        Add a base station. Authorization: ADMIN

        :param bs_id: Hexadecimal ID of the base station.
        :param cell_id: Hexadecimal ID of the cell the base station belongs to.
        :param coordinates: Coordinate of the base station as [x, y, z].
        :param angle: Angle from local frame Y axis anti-clockwise to 
            base station mounting orientation, in degress (0..359).
        :param desc: Human-readable description.
        :returns: On success, the server responds with a single-element 
            response indicating the hexadecimal ID for the added base station.

        """
        try:
            request = models.BaseStationAddRequest(
                bs=models.BaseStation(
                    id=bs_id,
                    position=coordinates,
                    cell_id=cell_id,
                    orientation=angle,
                    desc=desc,
                )
            )
            self._send(request)
            return self._recv()
        except ValidationError as exc:
            return self._handle_exception(exc)


    def bs_update(
            self, 
            bs_id: str, 
            cell_id: str,
            coordinates: List[float] = None,
            angle: int = 0, 
            desc: str = None,
        ) -> dict:
        """
        Update base station. Authorization: ADMIN
        
        :param bs_id: Hexadecimal ID of the base station.
        :param cell_id: Hexadecimal ID of the cell the base station belongs to.
        :param coordinates: Coordinate of the base station as [x, y, z].
        :param angle: Angle from local frame Y axis anti-clockwise to 
            base station mounting orientation, in degress (0..359).
        :param desc: Human-readable description.
        :returns: On success, the server responds with RPL_ACK.

        """
        try:
            request = models.BaseStationUpdateRequest(
                bs=models.BaseStationOptionalPos(
                    id=bs_id,
                    desc=desc,
                    position = coordinates,
                    cell_id=cell_id,
                    orientation=angle,
                )
            )
            self._send(request)
            return self._recv()
        except ValidationError as exc:
            return self._handle_exception(exc)


    def bs_list(self) -> List[dict]:
        """
        List all base stations in the system. Authorization: USER.

        :returns: On success, the server responds with multi-element response.

        """
        request = models.BaseStationListRequest()
        self._send(request)
        return self._recv(ismultielem=True)


    def bs_remove(self, bs_id: str) -> dict:
        """
        Remove a base station from the system. Authorization: ADMIN.

        :param bs_id: Hexadecimal ID of the base station.
        :returns: On success, the server responds with RPL_ACK.

        """
        try:
            request = models.BaseStationRemoveRequest(
                bs=models.DeviceID(id=bs_id)
            )
            self._send(request)
            return self._recv()
        except ValidationError as exc:
            return self._handle_exception(exc)


    def bs_remove_all(self, cell_id: str = None):
        """
        Remove all base station from the system. Authorization: ADMIN.

        If 'cell_id' has been specified, only the base stations from
        that cell are removed from the system.

        :param cell_id: Hexadecimal ID of the base station.
        :returns: On success, the server responds with RPL_ACK.

        """
        try:
            if cell_id:
                request = models.BaseStationRemoveAllRequest(
                    cell=models.DeviceID(id=cell_id)
                )
            else:
                request = models.BaseStationRemoveAllRequest()
            self._send(request)
            return self._recv()
        except ValidationError as exc:
            return self._handle_exception(exc)


    # -----------------------------------------------------------------
    # Tags
    # -----------------------------------------------------------------
    def tag_add(
            self, 
            tag_id: str, 
            desc: str = None, 
            mode: Union[int, str] = 1, 
            alt: float = None
        ) -> dict:
        """
        Add a new tag to the system. Authorization: ADMIN.

        :param tag_id: Hexadecimal ID of the tag.
        :param desc: Human-readable description.
        :param mode: Operating mode selection. Default is 1. Mode numbers
            are given as integers, aliases as strings.
        :param alt:
        :returns: On success, the server responds with a single-element 
            response indicating the hexadecimal ID for the tag.

        """
        try:
            request = models.TagAddRequest(
                tag=models.Tag(
                    id=tag_id,
                    desc = desc,
                    mode = mode,
                    alt = alt
                )
            )
            self._send(request)
            return self._recv()
        except ValidationError as exc:
            return self._handle_exception(exc)


    def tag_update(
            self, 
            tag_id: str, 
            desc: str = None, 
            mode: Union[int, str] = 1, 
            alt: float = None
        ) -> dict:
        """
        Update the tag in the system. Authorization: ADMIN.

        :param tag_id: Hexadecimal ID of the tag.
        :param desc: Human-readable description.
        :param mode: Operating mode selection. Default is 1. Mode numbers
            are given as integers, aliases as strings.
        :param alt:
        :returns: On success, the server responds with RPL_ACK.

        """
        try:
            request = models.TagUpdateRequest(
                tag=models.Tag(
                    id=tag_id,
                    desc = desc,
                    mode = mode,
                    alt = alt,
                )
            )
            self._send(request)
            return self._recv()
        except ValidationError as exc:
            return self._handle_exception(exc)


    def tag_list(self) -> List[dict]:
        """
        List all tags in the system. Authorization: USER.

        :returns: On success, the server responds with multi-element response.

        """
        request = models.TagListRequest()
        self._send(request)
        return self._recv(ismultielem=True)


    def tag_remove(self, tag_id: str) -> dict:
        """
        Remove a tag from the system. Authorization: ADMIN.

        :param tag_id: Hexadecimal ID of the tag.
        :returns: On success, the server responds with RPL_ACK.

        """
        try:
            request = models.TagRemoveRequest(
                tag=models.DeviceID(id=tag_id)
            )
            self._send(request)
            return self._recv()
        except ValidationError as exc:
            return self._handle_exception(exc)


    def tag_remove_all(self) -> dict:
        """
        Remove all tags from the system. Authorization: ADMIN.

        :returns: On success, the server responds with RPL_ACK.

        """
        request = models.TagRemoveAllRequest()
        self._send(request)
        return self._recv()

    # -----------------------------------------------------------------
    # Tag Communication
    # -----------------------------------------------------------------
    def ntfn_send(self):
        pass

    def ntfn_status(self):
        pass

    # -----------------------------------------------------------------
    # Alerts
    # -----------------------------------------------------------------
    def alerts_list(self):
        pass

    def alerts_remove(self):
        pass

    def alerts_cancel(self):
        pass

    # -----------------------------------------------------------------
    # Logging
    # -----------------------------------------------------------------
    def log_start(self):
        pass

    def log_stop(self):
        pass

    def log_status(self):
        pass

    # -----------------------------------------------------------------
    # Channel Subscriptions
    # -----------------------------------------------------------------
    def channel_join(self, channel: List[str]) -> Union[dict, List[dict]]:
        """
        Join to a single channel (variant 1) or to multiple channels (variant 2).

        Authorization
        """
        try:
            channel_count = len(channel)
            if channel_count == 1:
                request = models.ChannelJoinRequestVariant1(channel=channel[0])
            elif channel_count > 1:
                request = models.ChannelJoinRequestVariant2(channel=channel)
            self._send(request)
            if channel_count == 1:
                self._recv()
            elif channel_count > 1:
                self._recv(ismultielem=True)
        except ValidationError as exc:
            return self._handle_exception(exc)


    def channel_list(self) -> dict:
        """
        List all the channels the client has currently joined to. Authorization: USER.

        :returns: On success, the server responds with a single-element response.

        """
        request = models.ChannelListRequest()
        self._send(request)
        return self._recv()


    def channel_leave(self, channel: List[str]) -> Union[dict, List[dict]]:
        """
        Leave a single channel (variant 1) or multiple channels (variant 2).
        """
        channel_count = len(channel)
        if channel_count == 1:
            request = models.ChannelLeaveRequestVariant1(channel=channel[0])
        elif channel_count > 1:
            request = models.ChannelLeaveRequestVariant2(channel=channel)
        self._send(request)
        if channel_count == 1:
            self._recv()
        elif channel_count > 1:
            self._recv(ismultielem=True)

