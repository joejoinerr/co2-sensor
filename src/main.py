import time
from typing import Annotated

import pydantic
from smbus2 import SMBus

EE895ADDRESS = 0x5E
I2CREGISTER = 0x00


class SensorError(Exception):
    pass


class SensorReadoutError(SensorError):
    def __init__(self, reserved_value: str):
        self.reserved_value: str = reserved_value
        super().__init__(
            f"Error with sensor readout: reserved value is {reserved_value}, should be "
            f"8000."
        )


class SensorData(pydantic.BaseModel):
    co2: Annotated[int, pydantic.Field(gt=0)]
    temperature: float
    pressure: Annotated[float, pydantic.Field(gt=0)]


def fetch_sensor_data(i2cbus: SMBus) -> SensorData:
    read_data = i2cbus.read_i2c_block_data(EE895ADDRESS, I2CREGISTER, 8)

    # reserved value - useful to check that the sensor is reading out correctly
    # this should be 0x8000
    reserved = read_data[4].to_bytes(1, "big") + read_data[5].to_bytes(1, "big")
    if (reserved_hex := reserved.hex()) != "8000":
        raise SensorReadoutError(reserved_hex)

    co2 = read_data[0].to_bytes(1, "big") + read_data[1].to_bytes(1, "big")
    temperature = read_data[2].to_bytes(1, "big") + read_data[3].to_bytes(1, "big")
    pressure = read_data[6].to_bytes(1, "big") + read_data[7].to_bytes(1, "big")

    return SensorData(
        co2=int.from_bytes(co2, "big"),
        temperature=int.from_bytes(temperature, "big") / 100,
        pressure=int.from_bytes(pressure, "big") / 10
    )


def main():
    i2cbus = SMBus(1)
    # delay recommended according to this stackoverflow post
    # https://stackoverflow.com/questions/52735862/getting-ioerror-errno-121-remote-i-o-error-with-smbus-on-python-raspberry-w
    time.sleep(1)

    sensor_data = fetch_sensor_data(i2cbus)
    print(f"Temperature: {sensor_data.temperature}\N{DEGREE SIGN}C")
    print(f"CO\N{SUBSCRIPT TWO}: {sensor_data.co2}ppm")
    print(f"Pressure: {sensor_data.pressure}ppm")


if __name__ == "__main__":
    main()
