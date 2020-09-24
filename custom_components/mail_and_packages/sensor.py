"""
Based on @skalavala work at
https://blog.kalavala.net/usps/homeassistant/mqtt/2018/01/12/usps.html

Configuration code contribution from @firstof9 https://github.com/firstof9/
"""
from multiprocessing.util import info
from . import const
from homeassistant.helpers.entity import Entity
from homeassistant.const import CONF_RESOURCES
import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):

    data = hass.data[const.DOMAIN_DATA][entry.entry_id][const.DATA]
    coordinator = hass.data[const.DOMAIN_DATA][entry.entry_id][const.COORDINATOR]

    sensors = []

    if CONF_RESOURCES in entry.options:
        resources = entry.options[CONF_RESOURCES]
    else:
        resources = entry.data[CONF_RESOURCES]

    for variable in resources:
        sensors.append(PackagesSensor(data, variable, coordinator))

    async_add_entities(sensors, True)


class PackagesSensor(Entity):
    """ Represntation of a sensor """

    def __init__(self, data, sensor_type, coordinator):
        """ Initialize the sensor """
        self._coordinator = coordinator
        self._name = const.SENSOR_TYPES[sensor_type][const.SENSOR_NAME]
        self._icon = const.SENSOR_TYPES[sensor_type][const.SENSOR_ICON]
        self._unit_of_measurement = const.SENSOR_TYPES[sensor_type][const.SENSOR_UNIT]
        self.type = sensor_type
        self.data = data
        self._state = self.data._data[self.type]

    @property
    def unique_id(self):
        """Return a unique, Home Assistant friendly identifier for this entity."""
        return f"{self.data._host}_{self._name}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit_of_measurement

    @property
    def icon(self):
        """Return the unit of measurement."""
        return self._icon

    @property
    def should_poll(self):
        """No need to poll. Coordinator notifies entity of updates."""
        return False

    @property
    def available(self):
        """Return if entity is available."""
        return self._coordinator.last_update_success

    @property
    def device_state_attributes(self):
        """Return device specific state attributes."""
        attr = {}
        attr[const.ATTR_SERVER] = self.data._host
        if "Amazon" in self._name:
            attr[const.ATTR_ORDER] = self.data._data[const.AMAZON_ORDER]
        elif "Mail USPS Mail" == self._name:
            attr[const.ATTR_IMAGE] = self.data._image_name
        elif self.type == const.USPS_DELIVERING:
            attr[const.ATTR_TRACKING_NUM] = self.data._data[const.USPS_TRACKING]
        elif self.type == const.UPS_DELIVERING:
            attr[const.ATTR_TRACKING_NUM] = self.data._data[const.UPS_TRACKING]
        elif self.type == const.FEDEX_DELIVERING:
            attr[const.ATTR_TRACKING_NUM] = self.data._data[const.FEDEX_TRACKING]
        elif self.type == const.DHL_DELIVERING:
            attr[const.ATTR_TRACKING_NUM] = self.data._data[const.DHL_TRACKING]
        return attr

    async def async_update(self):
        """Update the entity.

        Only used by the generic entity update service.
        """
        await self._coordinator.async_request_refresh()

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.async_on_remove(
            self._coordinator.async_add_listener(self.async_write_ha_state)
        )
