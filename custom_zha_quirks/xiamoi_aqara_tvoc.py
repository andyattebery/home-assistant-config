"""Quirk for lumi.airmonitor.acn01 tvoc air monitor - firmware 0.0.0_0029."""

from zigpy.profiles import zha
from zigpy.quirks import CustomCluster
import zigpy.types as t
from zigpy.zcl.clusters.general import AnalogInput, Basic, Identify, Ota
from zigpy.zcl.clusters.measurement import RelativeHumidity, TemperatureMeasurement
from zigpy.zdo.types import NodeDescriptor

from zhaquirks import Bus, LocalDataCluster, PowerConfigurationCluster
from zhaquirks.const import (
    DEVICE_TYPE,
    ENDPOINTS,
    INPUT_CLUSTERS,
    MODELS_INFO,
    NODE_DESCRIPTOR,
    OUTPUT_CLUSTERS,
    PROFILE_ID,
)
from zhaquirks.xiaomi import (
    LUMI,
    BasicCluster,
    RelativeHumidityCluster,
    TemperatureMeasurementCluster,
    XiaomiAqaraE1Cluster,
    XiaomiCustomDevice,
)

MEASURED_VALUE = 0x0000


class AnalogInputCluster(CustomCluster, AnalogInput):
    """Analog input cluster, relay tvoc to the correct cluster."""

    def _update_attribute(self, attrid, value):
        super()._update_attribute(attrid, value)
        self.endpoint.voc_level.update_attribute(MEASURED_VALUE, value)


class EmulatedTVOCMeasurement(LocalDataCluster):
    """TVOC measurement cluster to receive reports from the AnalogInput cluster."""

    PRESENT_VALUE = 0x0055
    ONE_HOUR = 3600
    MIN_CHANGE = 5
    TEN_SECONDS = 10

    cluster_id = 0x042E
    name = "VOC Level"
    ep_attribute = "voc_level"

    attributes = {
        MEASURED_VALUE: ("measured_value", t.Single),
    }

    async def bind(self):
        """Bind cluster."""
        result = await self.endpoint.analog_input.bind()
        await self.endpoint.analog_input.configure_reporting(
            self.PRESENT_VALUE,
            self.TEN_SECONDS,
            self.ONE_HOUR,
            self.MIN_CHANGE,
        )
        return result


class TVOCMonitor(XiaomiCustomDevice):
    """Aqara LUMI lumi.airmonitor.acn01."""

    def __init__(self, *args, **kwargs):
        """Init."""
        self.temperature_bus = Bus()
        self.humidity_bus = Bus()
        super().__init__(*args, **kwargs)

    signature = {
        # <SimpleDescriptor endpoint=1 profile=260 device_type=0x0402
        # device_version=1
        # input_clusters=[0x0000, 0x0001, 0x0003, 0x0500]
        # output_clusters=[0x0019]>
        MODELS_INFO: [(LUMI, "lumi.airmonitor.acn01")],
        ENDPOINTS: {
            1: {
                PROFILE_ID: 260,
                DEVICE_TYPE: 0x0402,
                INPUT_CLUSTERS: [
                    0x0000,
                    0x0001,
                    0x0003,
                    0x0500,
                ],
                OUTPUT_CLUSTERS: [0x0019],
            }
        },
    }

    replacement = {
        NODE_DESCRIPTOR: NodeDescriptor(
            0x02, 0x40, 0x80, 0x115F, 0x7F, 0x0064, 0x2C00, 0x0064, 0x00
        ),
        ENDPOINTS: {
            1: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.TEMPERATURE_SENSOR,
                INPUT_CLUSTERS: [
                    BasicCluster,
                    Identify.cluster_id,
                    TemperatureMeasurementCluster,
                    PowerConfigurationCluster,
                    RelativeHumidityCluster,
                    AnalogInputCluster,
                    EmulatedTVOCMeasurement,
                    XiaomiAqaraE1Cluster,
                ],
                OUTPUT_CLUSTERS: [Ota.cluster_id],
            }
        },
    }