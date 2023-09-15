from typing import List, Literal, Optional, Union

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------
# Definitions
# ---------------------------------------------------------------------
ALERT_EVENT = Literal[
    "lost",
    "compromised",
    "cancel",
]

CHANNEL_NAME = Literal[
    "!all",
    "alerts", 
    "clients", 
    "debug", 
    "error", 
    "measurements", 
    "sensors", 
    "solution", 
    "systemtime", 
    "tags",
]

CLIENT_EVENT = Literal[
    "connected",
    "disconnected",
    "login",
    "logout",
    "subscribed",
    "unsubscribed",
]

USER_ROLE = Literal[
    "admin",
    "user",
]

# ---------------------------------------------------------------------
# Message Primitives
# ---------------------------------------------------------------------
class BaseRequest(BaseModel):
    request: str = Field(description="command")
    msgid: int = Field(description="message ID", default=0)

class BaseResponse(BaseModel):
    response: str = Field(description="response type")
    msgid: int = Field(description="message ID", default=0)

# ---------------------------------------------------------------------
# Response Patterns
# ---------------------------------------------------------------------
class ElementResponse(BaseResponse):
    response: str = "element"

class BeginResponse(BaseResponse):
    response: str = "begin"

class EndResponse(BaseResponse):
    response: str = "end"

class AckResponse(BaseResponse):
    response: str = "ack"

class ErrorResponse(BaseResponse):
    response: str = "error"
    code: int = Field(description="error code")
    desc: str = Field(description="human-readable error description")

# ---------------------------------------------------------------------
# Common
# ---------------------------------------------------------------------
class DeviceID(BaseModel):
    id: str

# ---------------------------------------------------------------------
# Requests: Authentication and Session Control
# ---------------------------------------------------------------------
class AuthLoginRequest(BaseRequest):
    request: str = "login"
    user: str
    password: str

class AuthLogoutRequest(BaseRequest):
    request: str = "logout"

class AuthPingRequest(BaseRequest):
    request: str = "ping"

# ---------------------------------------------------------------------
# Requests: User Accounts
# ---------------------------------------------------------------------
class User(BaseModel):
    login: str
    password: str
    roles: Optional[List[USER_ROLE]] = None
    desc: Optional[str] = None

class UserUpdate(BaseModel):
    login: str
    new_login: Optional[str] = None
    new_password: Optional[str] = None
    new_roles: Optional[List[USER_ROLE]] = None
    new_desc: Optional[str] = None

class UserLogin(BaseModel):
    login: str

class UserAccount(BaseModel):
    id: int
    login: str
    desc: str = None
    roles: List[USER_ROLE] = None

class UserAccountResponse(ElementResponse):
    user: UserAccount

class UserCreateRequest(BaseRequest):
    request: str = "createUser"
    user: User

class UserUpdateRequest(BaseRequest):
    request: str = "updateUser"
    user: UserUpdate

class UserRemoveRequest(BaseRequest):
    request: str = "removeUser"
    user: UserLogin

class UserListRequest(BaseRequest):
    request: str = "listUsers"

class UserGetRequest(BaseRequest):
    request: str = "getUser"
    user: UserLogin

# ---------------------------------------------------------------------
# Requests: System Configuration
# ---------------------------------------------------------------------
class ConfigCoordinatesRequest(BaseRequest):
    request: str = "setCoordinates"
    origin: List[float]
    orientation: float

class ConfigAltitudeRequest(BaseRequest):
    request: str = "setAltitude"
    altitude: float

class ConfigGetRequest(BaseRequest):
    request: str = "getConfig"
    item: str

class ConfigResetAllRequest(BaseRequest):
    request: str = "resetAllConfig"

# ---------------------------------------------------------------------
# Requests: Cells
# ---------------------------------------------------------------------
class Cell(BaseModel):
    id: str
    desc: Optional[str] = None
    ip_address: str
    port: Optional[int] = None

class CellOptionalAddr(Cell):
    ip_address: Optional[str]

class CellAddRequest(BaseRequest):
    request: str = "addCell"
    cell: Cell

class CellUpdateRequest(BaseRequest):
    request: str = "updateCell"
    cell: CellOptionalAddr

class CellRemoveRequest(BaseRequest):
    request: str = "removeCell"
    cell: DeviceID

class CellRemoveAllRequest(BaseRequest):
    request: str = "removeAllCells"

class CellListRequest(BaseRequest):
    request: str = "listCells"

# ---------------------------------------------------------------------
# Requests: Base Station
# ---------------------------------------------------------------------
class BaseStation(BaseModel):
    id: str
    desc: Optional[str] = None
    position: List[float]
    orientation: Optional[int] = Field(default=0, ge=0, le=359)
    cell_id: str

class BaseStationOptionalPos(BaseModel):
    id: str
    desc: Optional[str] = None
    position: Optional[List[float]] = None
    orientation: Optional[int] = Field(default=0, ge=0, le=359)
    cell_id: str

class BaseStationAddRequest(BaseRequest):
    request: str = "addBS"
    bs: BaseStation

class BaseStationUpdateRequest(BaseRequest):
    request: str = "updateBS"
    bs: BaseStationOptionalPos

class BaseStationListRequest(BaseRequest):
    request: str = "listBS"

class BaseStationRemoveRequest(BaseRequest):
    request: str = "removeBS"
    bs: DeviceID

class BaseStationRemoveAllRequest(BaseRequest):
    request: str = "removeAllBS"
    cell: DeviceID = None

# ---------------------------------------------------------------------
# Requests: Tags
# ---------------------------------------------------------------------
class Tag(BaseModel):
    id: str
    desc: Optional[str] = None
    mode: Optional[Union[int, str]] = None
    alt: Optional[float] = None

class TagAddRequest(BaseRequest):
    request: str = "addTag"
    tag: Tag

class TagUpdateRequest(BaseRequest):
    request: str = "updateTag"
    tag: Tag

class TagListRequest(BaseRequest):
    request: str = "listTags"

class TagRemoveRequest(BaseRequest):
    request: str = "removeTag"
    tag: DeviceID

class TagRemoveAllRequest(BaseRequest):
    request: str = "removeAllTag"

# ---------------------------------------------------------------------
# Requests: Tag Communications
# ---------------------------------------------------------------------
class Ntfn(BaseModel):
    id: Optional[str] = None
    data: str

class NtfnSendRequest(BaseRequest):
    request: str = "sendNtfn"
    tag_id: Optional[str] = None
    ntfn: Ntfn

# ---------------------------------------------------------------------
# Requests: Channel Subscriptions
# ---------------------------------------------------------------------
class ChannelJoinRequestVariant1(BaseRequest):
    request: str = "joinChannel"
    channel: CHANNEL_NAME

class ChannelJoinRequestVariant2(BaseRequest):
    request: str = "joinChannel"
    channel: List[CHANNEL_NAME]

class ChannelListRequest(BaseRequest):
    request: str = "listChannels"

class ChannelLeaveRequestVariant1(BaseRequest):
    request: str = "leaveChannel"
    channel: CHANNEL_NAME

class ChannelLeaveRequestVariant2(BaseRequest):
    request: str = "leaveChannel"
    channel: List[CHANNEL_NAME]

# ---------------------------------------------------------------------
# Notification Messages
# ---------------------------------------------------------------------
class ErrorNotification(BaseModel):
    channel: str = "error"
    code: int
    desc: str

class DebugNotification(BaseModel):
    channel: str = "debug"
    message: str

class ClientNotification(BaseModel):
    channel: str = "clients"
    conn: str
    ip_address: str
    event: str = List[CLIENT_EVENT]
    user: Union[str, None]
    reason: Union[str, None]
    target_channel: Union[str, None]

class AlertNotification(BaseModel):
    channel: str = "alerts"
    alert: str
    event: List[ALERT_EVENT]
    bs: str
    desc: str

class MeasurementsNotification(BaseModel):
    channel: str = "measurements"
    type: str = "twr"
    time: str
    tag: str
    meas: List[list]  # [[<bs_id>,<distance>,<signalPower>, [...], ...]]

class SensorTemperatureNotification(BaseModel):
    channel: str = "sensors"
    type: str = "temp"
    time: str
    tag: str
    temp: float = Field(ge=-40, le=85)

class SensorPressureNotification(BaseModel):
    channel: str = "sensors"
    type: str = "pressure"
    time: str
    tag: str
    pressure: float

class SensorHumidityNotification(BaseModel):
    channel: str = "sensors"
    type: str = "humidity"
    time: str
    tag: str
    humidity: int = Field(ge=0, le=100)

class Velocity(BaseModel):
    speed: float
    vertical: float
    heading_lcl: float
    heading_trf: Union[float, None]

class Accuracy(BaseModel):
    horizontal: float
    vertical: float

class SolutionNotification(BaseModel):
    channel: str = "solution"
    time: str
    tag: str
    validity: str
    position_lcl: List[float]
    position_trf: List[float]
    velocity: Velocity
    accuracy: Accuracy
