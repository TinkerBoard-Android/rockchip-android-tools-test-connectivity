#!/usr/bin/env python3.4
#
#   Copyright 2020 - The Android Open Source Project
#
#   Licensed under the Apache License, Version 2.0 (the 'License');
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an 'AS IS' BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import collections
import json
import logging
import os
from acts import asserts
from acts import base_test
from acts import utils
from acts.controllers import iperf_server as ipf
from acts.controllers import iperf_client as ipc
from acts.metrics.loggers.blackbox import BlackboxMappedMetricLogger
from acts.test_utils.wifi import ota_sniffer
from acts.test_utils.wifi import wifi_retail_ap as retail_ap
from acts.test_utils.wifi import wifi_test_utils as wutils
from acts.test_utils.wifi import wifi_performance_test_utils as wputils
from acts.test_utils.wifi.aware import aware_const as aconsts
from acts.test_utils.wifi.aware import aware_test_utils as autils
from WifiRvrTest import WifiRvrTest

AccessPointTuple = collections.namedtuple(('AccessPointTuple'),
                                          ['ap_settings'])


class WifiAwareRvrTest(WifiRvrTest):

    # message ID counter to make sure all uses are unique
    msg_id = 0

    # offset (in seconds) to separate the start-up of multiple devices.
    # De-synchronizes the start-up time so that they don't start and stop scanning
    # at the same time - which can lead to very long clustering times.
    device_startup_offset = 2

    SERVICE_NAME = "GoogleTestServiceXYZ"

    PASSPHRASE = "This is some random passphrase - very very secure!!"
    PASSPHRASE2 = "This is some random passphrase - very very secure - but diff!!"

    def __init__(self, controllers):
        base_test.BaseTestClass.__init__(self, controllers)
        #self.tests = ('test_rvr_TCP_DL_2GHz', 'test_rvr_TCP_UL_2GHz')
        self.testcase_metric_logger = (
            BlackboxMappedMetricLogger.for_test_case())
        self.testclass_metric_logger = (
            BlackboxMappedMetricLogger.for_test_class())
        self.publish_testcase_metrics = True
        self.tests = ('test_aware_rvr_TCP_DL_ib_disconnected_disconnected',
                      'test_aware_rvr_TCP_DL_ib_connected_2G_1_disconnected',
                      'test_aware_rvr_TCP_UL_ib_connected_2G_1_disconnected',
                      'test_aware_rvr_TCP_DL_ib_connected_5G_1_disconnected',
                      'test_aware_rvr_TCP_DL_ib_connected_2G_1_connected_2G_1',
                      'test_aware_rvr_TCP_DL_ib_connected_5G_1_connected_5G_1',
                      'test_aware_rvr_TCP_DL_ib_connected_2G_1_connected_5G_1',
                      'test_aware_rvr_TCP_DL_ib_connected_2G_1_connected_2G_2',
                      'test_aware_rvr_TCP_DL_ib_connected_5G_1_connected_5G_2')

    def setup_class(self):
        """Initializes common test hardware and parameters.

        This function initializes hardwares and compiles parameters that are
        common to all tests in this class.
        """
        req_params = [
            'aware_rvr_test_params', 'testbed_params',
            'aware_default_power_mode', 'dbs_supported_models'
        ]
        opt_params = ['RetailAccessPoints', 'ap_networks', 'OTASniffer']
        self.unpack_userparams(req_params, opt_params)
        if hasattr(self, 'RetailAccessPoints'):
            self.access_points = retail_ap.create(self.RetailAccessPoints)
            self.access_point = self.access_points[0]
        else:
            self.access_point = AccessPointTuple({})
        self.testclass_params = self.aware_rvr_test_params
        self.num_atten = self.attenuators[0].instrument.num_atten
        self.iperf_server = ipf.create([{
            'AndroidDevice':
            self.android_devices[0].serial,
            'port':
            '5201'
        }])[0]
        self.iperf_client = ipc.create([{
            'AndroidDevice':
            self.android_devices[1].serial,
            'port':
            '5201'
        }])[0]

        self.log_path = os.path.join(logging.log_path, 'results')
        if hasattr(self,
                   'OTASniffer') and self.testbed_params['sniffer_enable']:
            self.sniffer = ota_sniffer.create(self.OTASniffer)[0]
        os.makedirs(self.log_path, exist_ok=True)
        if not hasattr(self, 'golden_files_list'):
            if 'golden_results_path' in self.testbed_params:
                self.golden_files_list = [
                    os.path.join(self.testbed_params['golden_results_path'],
                                 file) for file in
                    os.listdir(self.testbed_params['golden_results_path'])
                ]
            else:
                self.log.warning('No golden files found.')
                self.golden_files_list = []

        self.testclass_results = []

        # Turn WiFi ON
        if self.testclass_params.get('airplane_mode', 1):
            self.log.info('Turning on airplane mode.')
            for ad in self.android_devices:
                asserts.assert_true(utils.force_airplane_mode(ad, True),
                                    "Can not turn on airplane mode.")
        for ad in self.android_devices:
            wutils.wifi_toggle_state(ad, True)

    def teardown_class(self):
        # Turn WiFi OFF
        for dev in self.android_devices:
            wutils.wifi_toggle_state(dev, False)
        self.process_testclass_results()
        # Teardown AP and release its lockfile
        self.access_point.teardown()

    def teardown_test(self):
        self.iperf_server.stop()
        for ad in self.android_devices:
            if not ad.droid.doesDeviceSupportWifiAwareFeature():
                return
            ad.droid.wifiP2pClose()
            ad.droid.wifiAwareDestroyAll()
            autils.reset_device_parameters(ad)
            autils.validate_forbidden_callbacks(ad)
            wutils.reset_wifi(ad)

    def setup_aps(self, testcase_params):
        for network in testcase_params['ap_networks']:
            self.log.info('Setting AP {} {} interface on channel {}'.format(
                network['ap_id'], network['interface_id'], network['channel']))
            self.access_points[network['ap_id']].set_channel(
                network['interface_id'], network['channel'])

    def setup_duts(self, testcase_params):
        # Check battery level before test
        for ad in self.android_devices:
            if not wputils.health_check(ad, 20):
                asserts.skip('Overheating or Battery low. Skipping test.')
            ad.go_to_sleep()
            wutils.reset_wifi(ad)
        # Turn screen off to preserve battery
        for network in testcase_params['ap_networks']:
            for connected_dut in network['connected_dut']:
                self.log.info("Connecting DUT {} to {}".format(
                    connected_dut, self.ap_networks[network['ap_id']][
                        network['interface_id']]))
                wutils.wifi_connect(self.android_devices[connected_dut],
                                    self.ap_networks[network['ap_id']][
                                        network['interface_id']],
                                    num_of_tries=5,
                                    check_connectivity=True)

    def setup_aware_connection(self, testcase_params):
        # Basic aware setup
        for ad in self.android_devices:
            asserts.skip_if(
                not ad.droid.doesDeviceSupportWifiAwareFeature(),
                "Device under test does not support Wi-Fi Aware - skipping test"
            )
            aware_avail = ad.droid.wifiIsAwareAvailable()
            ad.droid.wifiP2pClose()
            wutils.wifi_toggle_state(ad, True)
            utils.set_location_service(ad, True)
            if not aware_avail:
                self.log.info('Aware not available. Waiting ...')
                autils.wait_for_event(ad,
                                      aconsts.BROADCAST_WIFI_AWARE_AVAILABLE,
                                      timeout=30)
            ad.aware_capabilities = autils.get_aware_capabilities(ad)
            autils.reset_device_parameters(ad)
            autils.reset_device_statistics(ad)
            autils.set_power_mode_parameters(ad, testcase_params['power_mode'])
            wutils.set_wifi_country_code(ad, wutils.WifiEnums.CountryCode.US)
            autils.configure_ndp_allow_any_override(ad, True)
            # set randomization interval to 0 (disable) to reduce likelihood of
            # interference in tests
            autils.configure_mac_random_interval(ad, 0)
            ad.ed.clear_all_events()

        # Establish Aware Connection
        self.init_dut = self.android_devices[0]
        self.resp_dut = self.android_devices[1]

        # note: Publisher = Responder, Subscribe = Initiator
        (resp_req_key, init_req_key, resp_aware_if, init_aware_if, resp_ipv6,
         init_ipv6) = autils.create_ib_ndp(
             self.resp_dut, self.init_dut,
             autils.create_discovery_config(self.SERVICE_NAME,
                                            aconsts.PUBLISH_TYPE_UNSOLICITED),
             autils.create_discovery_config(self.SERVICE_NAME,
                                            aconsts.SUBSCRIBE_TYPE_PASSIVE),
             self.device_startup_offset)
        testcase_params['aware_config'] = {
            "init_req_key": init_req_key,
            "resp_req_key": resp_req_key,
            "init_aware_if": init_aware_if,
            "resp_aware_if": resp_aware_if,
            "init_ipv6": init_ipv6,
            "resp_ipv6": resp_ipv6
        }
        testcase_params['iperf_server_address'] = init_ipv6
        for ad in self.android_devices:
            self.log.warning(
                ad.adb.shell('cmd wifiaware native_cb get_channel_info'))
        ndp_config = self.android_devices[0].adb.shell(
            'cmd wifiaware native_cb get_channel_info')
        ndp_config = json.loads(ndp_config)
        ndp_config = ndp_config[list(ndp_config.keys())[0]][0]
        testcase_params['channel'] = wutils.WifiEnums.freq_to_channel[
            ndp_config['channelFreq']]
        if testcase_params['channel'] < 13:
            testcase_params['mode'] = 'VHT20'
        else:
            testcase_params['mode'] = 'VHT80'
        testcase_params['test_network'] = {'SSID': 'Aware'}
        self.log.info('Wifi Aware Connection Established on Channel {} {} '
                      '(Interfaces: {},{})'.format(testcase_params['channel'],
                                                   testcase_params['mode'],
                                                   init_aware_if,
                                                   resp_aware_if))

    def setup_aware_rvr_test(self, testcase_params):
        # Setup the aps
        self.setup_aps(testcase_params)
        # Setup the duts
        self.setup_duts(testcase_params)
        # Set attenuator to 0 dB
        for attenuator in self.attenuators:
            attenuator.set_atten(0, strict=False)
        # Setup the aware connection
        self.setup_aware_connection(testcase_params)
        # Set DUT to monitor RSSI and LLStats on
        self.monitored_dut = self.android_devices[1]

    def cleanup_aware_rvr_test(self, testcase_params):
        # clean-up
        self.resp_dut.droid.connectivityUnregisterNetworkCallback(
            testcase_params['aware_config']['resp_req_key'])
        self.init_dut.droid.connectivityUnregisterNetworkCallback(
            testcase_params['aware_config']['init_req_key'])

    def compile_test_params(self, testcase_params):
        """Function that completes all test params based on the test name.

        Args:
            testcase_params: dict containing test-specific parameters
        """
        # Compile RvR parameters
        num_atten_steps = int((self.testclass_params['atten_stop'] -
                               self.testclass_params['atten_start']) /
                              self.testclass_params['atten_step'])
        testcase_params['atten_range'] = [
            self.testclass_params['atten_start'] +
            x * self.testclass_params['atten_step']
            for x in range(0, num_atten_steps)
        ]

        # Compile iperf arguments
        if testcase_params['traffic_direction'] == 'DL':
            testcase_params['iperf_args'] = wputils.get_iperf_arg_string(
                duration=self.testclass_params['iperf_duration'],
                reverse_direction=1,
                traffic_type=testcase_params['traffic_type'],
                ipv6=True)
            testcase_params['use_client_output'] = True
        else:
            testcase_params['iperf_args'] = wputils.get_iperf_arg_string(
                duration=self.testclass_params['iperf_duration'],
                reverse_direction=0,
                traffic_type=testcase_params['traffic_type'],
                ipv6=True)
            testcase_params['use_client_output'] = False

        # Compile AP and infrastructure connection parameters
        ap_networks = []
        if testcase_params['dut_connected'][0]:
            band = testcase_params['dut_connected'][0].split('_')[0]
            ap_networks.append({
                'ap_id':
                0,
                'interface_id':
                band if band == '2G' else band + '_1',
                'band':
                band,
                'channel':
                1 if band == '2G' else 36,
                'connected_dut': [0]
            })

        if testcase_params['dut_connected'][1]:
            if testcase_params['dut_connected'][0] == testcase_params[
                    'dut_connected'][1]:
                # if connected to same network, add it to the above
                ap_networks[0]['connected_dut'].append(1)
            else:
                band = testcase_params['dut_connected'][1].split('_')[0]
                if not testcase_params['dut_connected'][0]:
                    # if it is the only dut connected, assign it to ap 0
                    ap_id = 0
                elif band == ap_networks[0]['band']:
                    # if its connected to same band, connect to ap 1
                    ap_id = 1
                else:
                    # if its on a different band, connect to ap 0 as well
                    ap_id = 1
                ap_networks.append({
                    'ap_id':
                    ap_id,
                    'interface_id':
                    band if band == '2G' else band + '_1',
                    'band':
                    band,
                    'channel':
                    11 if band == '2G' else 149,
                    'connected_dut': [1]
                })
        testcase_params['ap_networks'] = ap_networks

        return testcase_params

    def _test_aware_rvr(self, testcase_params):
        """ Function that gets called for each test case

        Args:
            testcase_params: dict containing test-specific parameters
        """
        # Compile test parameters from config and test name
        testcase_params = self.compile_test_params(testcase_params)

        # Prepare devices and run test
        self.setup_aware_rvr_test(testcase_params)
        rvr_result = self.run_rvr_test(testcase_params)
        self.cleanup_aware_rvr_test(testcase_params)

        # Post-process results
        self.testclass_results.append(rvr_result)
        self.process_test_results(rvr_result)
        self.pass_fail_check(rvr_result)

    #Test cases
    def test_aware_rvr_TCP_DL_ib_disconnected_disconnected(self):
        testcase_params = collections.OrderedDict(
            traffic_type='TCP',
            traffic_direction='DL',
            power_mode='INTERACTIVE',
            dut_connected=[False, False],
        )
        self._test_aware_rvr(testcase_params)

    def test_aware_rvr_TCP_DL_ib_connected_2G_1_disconnected(self):
        testcase_params = collections.OrderedDict(
            traffic_type='TCP',
            traffic_direction='DL',
            power_mode='INTERACTIVE',
            dut_connected=['2G_1', False])
        self._test_aware_rvr(testcase_params)

    def test_aware_rvr_TCP_UL_ib_connected_2G_1_disconnected(self):
        testcase_params = collections.OrderedDict(
            traffic_type='TCP',
            traffic_direction='UL',
            power_mode='INTERACTIVE',
            dut_connected=['2G_1', False])
        self._test_aware_rvr(testcase_params)

    def test_aware_rvr_TCP_DL_ib_connected_5G_1_disconnected(self):
        testcase_params = collections.OrderedDict(
            traffic_type='TCP',
            traffic_direction='DL',
            power_mode='INTERACTIVE',
            dut_connected=['5G_1', False])
        self._test_aware_rvr(testcase_params)

    def test_aware_rvr_TCP_DL_ib_connected_2G_1_connected_2G_1(self):
        testcase_params = collections.OrderedDict(
            traffic_type='TCP',
            traffic_direction='DL',
            power_mode='INTERACTIVE',
            dut_connected=['2G_1', '2G_1'])
        self._test_aware_rvr(testcase_params)

    def test_aware_rvr_TCP_DL_ib_connected_5G_1_connected_5G_1(self):
        testcase_params = collections.OrderedDict(
            traffic_type='TCP',
            traffic_direction='DL',
            power_mode='INTERACTIVE',
            dut_connected=['5G_1', '5G_1'])
        self._test_aware_rvr(testcase_params)

    def test_aware_rvr_TCP_DL_ib_connected_2G_1_connected_5G_1(self):
        testcase_params = collections.OrderedDict(
            traffic_type='TCP',
            traffic_direction='DL',
            power_mode='INTERACTIVE',
            dut_connected=['2G_1', '5G_1'])
        self._test_aware_rvr(testcase_params)

    def test_aware_rvr_TCP_DL_ib_connected_2G_1_connected_2G_2(self):
        testcase_params = collections.OrderedDict(
            traffic_type='TCP',
            traffic_direction='DL',
            power_mode='INTERACTIVE',
            dut_connected=['2G_1', '2G_2'])
        self._test_aware_rvr(testcase_params)

    def test_aware_rvr_TCP_DL_ib_connected_5G_1_connected_5G_2(self):
        testcase_params = collections.OrderedDict(
            traffic_type='TCP',
            traffic_direction='DL',
            power_mode='INTERACTIVE',
            dut_connected=['5G_1', '5G_2'])
        self._test_aware_rvr(testcase_params)