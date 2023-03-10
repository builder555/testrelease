from typing import List, Tuple, Dict
import struct
import logging
import asyncio
from pinecil_setting_limits import value_limits
from pinecil_setting_limits import temperature_limits
from crx_uuid_name_map import names_v220, names_v221, live_data_names
from ble import BleakGATTCharacteristic
from ble import BLE
import time

class ValueOutOfRangeException(Exception):
    message = 'Value out of range'

class InvalidSettingException(Exception):
    message = 'Invalid setting'


class SettingNameToUUIDMap:
    def __init__(self):
        self.names = names_v220

    def set_version(self, version: str):
        self.names = names_v220 if version == '2.20' else names_v221
        
    def get_name(self, uuid: str) -> str:
        return self.names.get(uuid, uuid)
    
    def get_uuid(self, name: str) -> str:
        return next((k for k, v in self.names.items() if v == name), name)

class LiveDataToUUIDMap:
    def __init__(self):
        self.names = live_data_names

    def set_version(self, version: str):
        self.names = live_data_names
        
    def get_name(self, uuid: str) -> str:
        return self.names.get(uuid, uuid)
    
    def get_uuid(self, name: str) -> str:
        return next((k for k, v in self.names.items() if v == name), name)


class Pinecil:

    def __init__(self):
        self.ble = BLE(name='pinecil')
        self.settings_uuid: str = 'f6d75f91-5a10-4eba-a233-47d3f26a907f'
        self.bulk_data_uuid: str = '9eae1adb-9d0d-48c5-a6e7-ae93f0ea37b0'
        self.live_data_uuid: str = 'd85efab4-168e-4a71-affd-33e27f9bc533'
        self.temp_unit_crx: str = 'TemperatureUnit'
        self.settings_map = SettingNameToUUIDMap()
        self.live_data_map = LiveDataToUUIDMap()
        self.crx_settings: List[BleakGATTCharacteristic] = []
        self.crx_live_data: List[BleakGATTCharacteristic] = []
        self.live_data_to_read: List[str] = ['LiveTemp', 'Voltage', 'HandleTemp', 'OperatingMode', 'Watts']
        self.is_initialized = False
        self.is_getting_settings = False
        self.__last_read_settings = {}
        self.__last_read_settings_time = 0

    @property
    def is_connected(self):
        return self.ble.is_connected and self.is_initialized

    def __get_version(self, crxs: List[BleakGATTCharacteristic]):
        # this is just a hack until the version is exposed in the settings
        for crx in crxs:
            if crx.uuid == '0000ffff-0000-1000-8000-00805f9b34fb':
                return '2.21'
        return '2.20'
        
    async def connect(self):
        await self.ble.ensure_connected()
        self.crx_settings = await self.ble.get_characteristics(self.settings_uuid)
        self.crx_live_data = await self.ble.get_characteristics(self.live_data_uuid)
        self.settings_map.set_version(self.__get_version(self.crx_settings))
        self.unique_id = await self.__get_pinecil_id()
        self.is_initialized = True
        
    async def __read_setting(self, crx: BleakGATTCharacteristic) -> Tuple[str, int]:
        raw_value = await self.ble.read_characteristic(crx)
        number = struct.unpack('<H', raw_value)[0]
        return self.settings_map.get_name(crx.uuid), number

    async def __get_pinecil_id(self):
        try:
            characteristics = await self.ble.get_characteristics(self.bulk_data_uuid)
            for crx in characteristics:
                if crx.uuid == '00000004-0000-1000-8000-00805f9b34fb':
                    raw_value = await self.ble.read_characteristic(crx)
                    n = struct.unpack('<Q',raw_value)[0]
                    # using algorithm from here:
                    # https://github.com/Ralim/IronOS/commit/eb5d6ea9fd6acd221b8880650728e13968e54d3d
                    unique_id = ((n & 0xFFFFFFFF) ^ ((n >> 32) & 0xFFFFFFFF))
                    return f'{unique_id:X}'
        except:
            return ''

    async def get_all_settings(self) -> Dict[str, int]:
        logging.info('REQUEST FOR SETTINGS')
        while self.is_getting_settings:
            await asyncio.sleep(0.5)
        if time.time() - self.__last_read_settings_time < 2:
            return self.__last_read_settings
        try:
            logging.info(f'Reading all settings')
            self.is_getting_settings = True
            if not self.is_connected:
                await self.connect()
            tasks = [asyncio.ensure_future(self.__read_setting(crx)) for crx in self.crx_settings]
            results = await asyncio.gather(*tasks)
            settings = dict(results)
            logging.info(f'Reading all settings DONE')
            self.__last_read_settings = settings
            self.__last_read_settings_time = time.time()
            return settings
        except Exception as e:
            raise e
        finally:
            self.is_getting_settings = False

    async def __ensure_valid_temperature(self, setting, temperature):
        characteristics = await self.ble.get_characteristics(self.settings_uuid)
        temp_uuid = self.settings_map.get_uuid(self.temp_unit_crx)
        for crx in characteristics:
            if crx.uuid == temp_uuid:
                raw_value = await self.ble.read_characteristic(crx)
                temp_unit = struct.unpack('<H', raw_value)[0]
                within_limit = temperature_limits[setting][temp_unit]
                if not within_limit(temperature):
                    logging.warning(f'Temp. {temperature} is out of range for setting {setting}')
                    raise ValueOutOfRangeException
                break

    async def set_one_setting(self, setting, value):
        ensure_setting_exists(setting)
        ensure_setting_value_within_limits(setting, value)
        if not self.is_connected:
            await self.connect()
        if setting in temperature_limits:
            await self.__ensure_valid_temperature(setting, value)
        logging.info(f'Setting {value} ({type(value)}) to {setting}')
        uuid = self.settings_map.get_uuid(setting)
        for crx in self.crx_settings:
            if crx.uuid == uuid:
                value = struct.pack('<H', value)
                await self.ble.write_characteristic(crx, bytearray(value))
                break
        else:
            raise Exception('Setting not found')

    async def save_to_flash(self):
        await self.set_one_setting('save_to_flash', 1)

    async def get_info(self):
        return {
            'name': f'Pinecil-{self.unique_id}',
            'id': self.unique_id,
        }
    async def __read_live_item(self, crx: BleakGATTCharacteristic) -> Tuple[str, int]:
        raw_value = await self.ble.read_characteristic(crx)
        number = struct.unpack('<L', raw_value)[0]
        return self.live_data_map.get_name(crx.uuid), number

    async def get_live_data(self) -> Dict[str, int]:
        logging.debug(f'GETTING ALL LIVE VALUES')
        if not self.is_connected:
            await self.connect()
        tasks = []
        for crx in self.crx_live_data:
            if self.live_data_map.get_name(crx.uuid) in self.live_data_to_read:
                tasks.append(asyncio.ensure_future(self.__read_live_item(crx)))
        results = await asyncio.gather(*tasks)
        values = dict(results)
        logging.debug(f'GETTING ALL LIVE VALUES DONE')
        return values


def ensure_setting_exists(name: str):
    if name not in names_v220.values() and name not in names_v221.values():
        logging.warning(f'Setting {name} does not exist')
        raise InvalidSettingException

def ensure_setting_value_within_limits(name: str, value: int):
    min_val, max_val = value_limits[name]
    if not min_val <= value <= max_val:
        logging.warning(f'Value {value} is out of range for setting {name} ({min_val}-{max_val})')
        raise ValueOutOfRangeException
