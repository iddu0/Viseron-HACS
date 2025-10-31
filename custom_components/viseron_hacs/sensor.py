# for testing, i'm learning!
from homeassistant.helpers.entity import Entity

async def async_setup_entry(hass, config_entry, async_add_entities):
    async_add_entities([ExampleSensor])

class ExampleSensor(Entity):
    def __init__(self):
        self.__attr_name = "Example Sensor"
        self.__attr_native_value = 42

    @property
    def name(self):
        return self.__attr_name
    
    @property

    def native_value(self):
        return self.__attr_native_value
