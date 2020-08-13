"""Module managing the required definitions for using the bits power monitor"""

import logging
import os
import time

from acts import context
from acts.controllers import power_monitor
from acts.controllers.bits_lib import bits_client
from acts.controllers.bits_lib import bits_service
from acts.controllers.bits_lib import bits_service_config as bsc
from acts.test_utils.instrumentation.power import power_metrics

MOBLY_CONTROLLER_CONFIG_NAME = 'Bits'
ACTS_CONTROLLER_REFERENCE_NAME = 'bitses'


def create(configs):
    return [Bits(index, config) for (index, config) in enumerate(configs)]


def destroy(bitses):
    for bits in bitses:
        bits.teardown()


def get_info(bitses):
    return [bits.config for bits in bitses]


def transform_name(bits_metric_name):
    """Transform bits metrics names to a more succinct version.

    Examples of bits_metrics_name as provided by the client:
    - default_device.slider.C1_30__PP0750_L1S_VDD_G3D_M_P:mA,
    - default_device.slider.C1_30__PP0750_L1S_VDD_G3D_M_P:mW,
    - default_device.Monsoon.Monsoon:mA,
    - default_device.Monsoon.Monsoon:mW,
    - <device>.<collector>.<rail>:<unit>

    Args:
        bits_metric_name: A bits metric name.

    Returns:
        For monsoon metrics, and for backwards compatibility:
          Monsoon:mA -> avg_current,
          Monsoon:mW -> avg_power,

        For everything else:
          <rail>:mW -> <rail/rail>_avg_current
          <rail>:mW -> <rail/rail>_avg_power
          ...
    """
    prefix, unit = bits_metric_name.split(':')
    rail = prefix.split('.')[-1]

    if 'mW' == unit:
        suffix = 'avg_power'
    elif 'mA' == unit:
        suffix = 'avg_current'
    elif 'mV' == unit:
        suffix = 'avg_voltage'
    else:
        logging.getLogger().warning('unknown unit type for unit %s' % unit)
        suffix = ''

    if 'Monsoon' == rail:
        return suffix
    elif suffix == '':
        return rail
    else:
        return '%s_%s' % (rail, suffix)


def raw_data_to_metrics(raw_data_obj):
    data = raw_data_obj['data']
    metrics = []
    for sample in data:
        unit = sample['unit']
        if 'Msg' == unit:
            continue
        elif 'mW' == unit:
            unit_type = 'power'
        elif 'mA' == unit:
            unit_type = 'current'
        elif 'mV' == unit:
            unit_type = 'voltage'
        else:
            logging.getLogger().warning('unknown unit type for unit %s' % unit)
            continue

        name = transform_name(sample['name'])
        avg = sample['avg']
        metrics.append(power_metrics.Metric(avg, unit_type, unit, name=name))

    return metrics


class Bits(object):
    def __init__(self, index, config):
        self.index = index
        self.config = config
        self._service = None
        self._client = None

    def setup(self, *_, **__):
        registry = power_monitor.get_registry()
        if 'bits_service' not in registry:
            raise ValueError('No bits_service binary has been defined in the '
                             'global registry.')
        if 'bits_client' not in registry:
            raise ValueError('No bits_client binary has been defined in the '
                             'global registry.')

        bits_service_binary = registry['bits_service'][0]
        bits_client_binary = registry['bits_client'][0]
        lvpm_monsoon_bin = registry.get('lvpm_monsoon', [None])[0]
        hvpm_monsoon_bin = registry.get('hvpm_monsoon', [None])[0]
        kibble_bin = registry.get('kibble_bin', [None])[0]
        kibble_board_file = registry.get('kibble_board_file', [None])[0]
        vm_file = registry.get('vm_file', [None])[0]
        config = bsc.BitsServiceConfig(self.config,
                                       lvpm_monsoon_bin=lvpm_monsoon_bin,
                                       hvpm_monsoon_bin=hvpm_monsoon_bin,
                                       kibble_bin=kibble_bin,
                                       kibble_board_file=kibble_board_file,
                                       virtual_metrics_file=vm_file)
        output_log = os.path.join(
            context.get_current_context().get_full_output_path(),
            'bits_service_out_%s.txt' % self.index)
        service_name = 'bits_config_%s' % self.index

        self._service = bits_service.BitsService(config,
                                                 bits_service_binary,
                                                 output_log,
                                                 name=service_name,
                                                 timeout=3600 * 24)
        self._service.start()
        self._client = bits_client.BitsClient(bits_client_binary,
                                              self._service,
                                              config)

    def disconnect_usb(self, *_, **__):
        self._client.disconnect_usb()

    def connect_usb(self, *_, **__):
        self._client.connect_usb()

    def measure(self, *_, measurement_args=None, **__):
        if measurement_args is None:
            raise ValueError('measurement_args can not be left undefined')

        duration = measurement_args.get('duration')
        if duration is None:
            raise ValueError(
                'duration can not be left undefined within measurement_args')
        self._client.start_collection()
        time.sleep(duration)

    def get_metrics(self, *_, timestamps=None, **__):
        if timestamps is None:
            raise ValueError('timestamps dictionary can not be left undefined')

        metrics = {}
        for segment_name, times in timestamps.items():
            start_ns = times['start'] * 1_000_000
            end_ns = times['end'] * 1_000_000
            self._client.add_marker(start_ns, 'start - %s' % segment_name)
            self._client.add_marker(end_ns, 'end - %s' % segment_name)
            raw_metrics = self._client.get_metrics(start_ns, end_ns)
            metrics[segment_name] = raw_data_to_metrics(raw_metrics)
        return metrics

    def release_resources(self):
        self._client.stop_collection()

    def teardown(self):
        if self._service is None:
            return

        if self._service.service_state == bits_service.BitsServiceStates.STARTED:
            self._service.stop()
