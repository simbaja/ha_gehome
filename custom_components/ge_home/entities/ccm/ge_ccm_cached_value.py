class GeCcmCachedValue():
    def __init__(self):
        self._set_value = None
        self._last_device_value = None

    def get_value(self, device_value):
        
        # If the last device value is different from the current one, return the device value which overrides the set value
        if self._last_device_value != device_value:
            self._last_device_value = device_value
            self._set_value = None
            return device_value
        
        if self._set_value is not None:
            return self._set_value

        return device_value

    def set_value(self, value):
        self._set_value = value