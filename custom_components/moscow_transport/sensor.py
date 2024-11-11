"""Сервис получения информации о ближайшем автобусе из Московского транспорта"""
from __future__ import annotations

from datetime import timedelta
import logging

import voluptuous as vol

from homeassistant.components.sensor import (
    PLATFORM_SCHEMA,
    SensorDeviceClass,
    SensorEntity,
)
from homeassistant.const import CONF_NAME, MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
import homeassistant.util.dt as dt_util
from homeassistant.util import slugify

from . import data_mapper

_LOGGER = logging.getLogger(__name__)

INTEGRATION_NAME = "moscow_transport"

STOP_NAME = "stop_name"

CONF_STOP_ID = "stop_id"
CONF_ROUTE = "routes"

DEFAULT_NAME = "Moscow Transport"

USER_AGENT = "Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:79.0) Gecko/20100101 Firefox/79.0"

SCAN_INTERVAL = timedelta(minutes=1)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_STOP_ID): cv.string,
        vol.Optional(CONF_NAME, default=""): cv.string,
        vol.Optional(CONF_ROUTE, default=[]): vol.All(cv.ensure_list, [cv.string]),
    }
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the moscow transport sensor."""
    stop_id = config[CONF_STOP_ID]
    name = config[CONF_NAME]
    routes = config[CONF_ROUTE]
    session = async_create_clientsession(hass)

    async_add_entities([DiscoverMoscowTransport(
        session, stop_id, routes, name)], True)


def get_telemetry_suffix(byTelemetry):
    return '*' if byTelemetry == 0 else ''


class DiscoverMoscowTransport(SensorEntity):
    """Implementation of moscow_transport sensor."""

    _attr_attribution = "Данные Московского транспорта по телеметрии (* - данные из расписания)"
    _attr_icon = "mdi:bus"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_friendly_name = "hello world"

    # Не сохранять историю аттрибутов
    _unrecorded_attributes = frozenset({MATCH_ALL})

    def __init__(self, session, stop_id, routes, name) -> None:
        """Initialize sensor."""
        self.session = session
        self._stop_id = stop_id
        self._routes = routes
        self._state = None
        self._name = name or DEFAULT_NAME
        self._custom_name = name
        self._attrs = None
        self.entity_id = f"sensor.{stop_id}_{INTEGRATION_NAME}"

    async def async_update(self, *, tries=0):
        """Get the latest data from maps.yandex.ru and update the states."""
        attrs = {}

        try:
            stop_info = await self.get_stop_info()
        except:
            _LOGGER.error(
                f"Ошибка запроса к stop_id={self._stop_id}, {self._custom_name or self._name}")
            return

        if stop_info is None:
            return

        self._name = self._custom_name or stop_info['name']
        slugify_name = slugify(f"{self._name}_{INTEGRATION_NAME}")
        self.entity_id = f"sensor.{slugify_name}"

        closest_route = data_mapper.get_closest_route(stop_info, self._routes)
        if closest_route:
            telemetry_suffix = get_telemetry_suffix(closest_route[2])
            self._name = f"{self._name} ({closest_route[0]}{telemetry_suffix})"
            # do not save _state change in history
            self._state = dt_util.utcnow(
            ) + timedelta(seconds=closest_route[1])


        for route in stop_info['routePath']:

            if self._routes and route['number'] not in self._routes:
                # skip unnecessary route info
                continue

            for event in route['externalForecast']:
                if route['number'] not in attrs:
                    attrs[route['number']] = []

                route_time = dt_util.now(
                ) + timedelta(seconds=event['time'])
                time_formatted = route_time.strftime('%H:%M')
                telemetry_suffix = get_telemetry_suffix(event['byTelemetry'])
                attrs[route['number']].append(f"{time_formatted}{telemetry_suffix}"
                                              )

        attrs[STOP_NAME] = stop_info['name']

        self._attrs = attrs

    async def get_stop_info(self):
        request_url = f"https://moscowtransport.app/api/stop_v2/{self._stop_id}"

        headers = {"User-Agent": USER_AGENT}

        response = await self.session.request("GET", request_url, headers=headers, timeout=5)
        data = await response.json()
        if data['name'] == 'Exception':
            error_message = f"Нет остановки с stop_id={self._stop_id}"
            _LOGGER.error(error_message)
            raise Exception(error_message)
        return data

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._attrs

    @property
    def unique_id(self):
        """Return the unique_id."""
        return f"{self._stop_id}-moscow_transport"
