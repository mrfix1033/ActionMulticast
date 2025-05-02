from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL, CoInitialize
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume


def get_volume_object():
    CoInitialize()
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    return cast(interface, POINTER(IAudioEndpointVolume))


def get_volume():
    return get_volume_object().GetMasterVolumeLevelScalar()


def set_volume(value: float):
    """:param value: 0.0-1.0"""
    get_volume_object().SetMasterVolumeLevelScalar(value, None)
