from dataclasses import dataclass

@dataclass
class TreagerDetails:
    thingName: str
    userId: str
    lastConnectedOn: int
    thingNameLower: str
    friendlyName: str
    deviceType: str

@dataclass
class TreagerData:
    thingName: str
    status: dict
    features: dict
    limits: dict
    settings: dict
    usage: dict
    custom_cook: dict
    details: TreagerDetails
    stateIndex: int
    schemaVersion: str

