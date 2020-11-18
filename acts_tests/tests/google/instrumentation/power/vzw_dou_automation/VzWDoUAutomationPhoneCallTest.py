#!/usr/bin/env python3
#
#   Copyright 2020 - The Android Open Source Project
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
import copy
import time

from acts.test_decorators import repeated_test
from acts_contrib.test_utils.instrumentation.device.command.adb_commands import goog
from acts_contrib.test_utils.instrumentation.power.vzw_dou_automation import \
  vzw_dou_automation_comp_base_test
from acts_contrib.test_utils.instrumentation.power.vzw_dou_automation import \
  vzw_dou_automation_base_test
from acts_contrib.test_utils.instrumentation.device.command.adb_commands import common

class VzWDoUAutomationPhoneCallTest(
    vzw_dou_automation_comp_base_test.VzWDoUAutomationCompBaseTest):
  """Class for running VZW DoU phone call test cases"""

  @repeated_test(
      num_passes=3,
      acceptable_failures=2,
      result_selector=vzw_dou_automation_base_test.get_median_current)
  def test_voice_call_over_lte(self, attempt_number):
    """Measures power when the device is on call with mute on and off."""
    self.ad_dut.adb.ensure_root()
    self.adb_run(goog.disable_playstore)
    self._google_apps_test_utils.prevent_playstore_auto_updates()
    companion_phone_number = self.get_phone_number(self.ad_cp)
    self.log.debug(
        'The companion phone number is {}'.format(companion_phone_number))
    dut_phone_number = self.get_phone_number(self.ad_dut)
    self.log.debug('The dut phone number is {}'.format(dut_phone_number))
    time.sleep(vzw_dou_automation_base_test.DEFAULT_DEVICE_COOL_DOWN_TIME)
    # In this test case three calls are made
    PHONE_CALL_COUNT = 3
    metrics_list = []
    for i in range(PHONE_CALL_COUNT):
      # The companion phone mutes on 1st and 3rd calls
      is_companion_muted = 'TRUE' if i % PHONE_CALL_COUNT != 1 else 'FALSE'
      self.run_instrumentation_on_companion(
          'com.google.android.platform.dou.CompanionPhoneVoiceCallTests',
          'testReceiveVoiceCall',
          extra_params=[('recipient_number', dut_phone_number),
                        ('recipient_number_companion', companion_phone_number),
                        ('enable_mute', is_companion_muted)])
      # The dut mutes on 2nd and 3rd calls
      is_dut_muted = 'TRUE' if i % PHONE_CALL_COUNT != 0 else 'FALSE'
      metrics = self.run_and_measure(
          'com.google.android.platform.dou.PhoneVoiceCallWithMuteTests',
          'testVoiceCall',
          extra_params=[('recipient_number', dut_phone_number),
                        ('recipient_number_companion', companion_phone_number),
                        ('enable_mute', is_dut_muted)], count=i, attempt_number=attempt_number)
      metrics_list.append(metrics)
    final_metrics = self._generate_final_metrics(metrics_list)
    self.record_metrics(final_metrics)
    self.validate_metrics(final_metrics)

  @repeated_test(
      num_passes=3,
      acceptable_failures=2,
      result_selector=vzw_dou_automation_base_test.get_median_current)
  def test_voice_call_over_lte_wifi(self, attempt_number):
    """Measures power when the device is on call with mute on and off
    with wifi connected."""
    self.ad_dut.adb.ensure_root()
    self.adb_run(goog.disable_playstore)
    self.adb_run(common.wifi_state.toggle(True))
    self._google_apps_test_utils.prevent_playstore_auto_updates()
    companion_phone_number = self.get_phone_number(self.ad_cp)
    self.log.debug(
        'The companion phone number is {}'.format(companion_phone_number))
    dut_phone_number = self.get_phone_number(self.ad_dut)
    self.log.debug('The dut phone number is {}'.format(dut_phone_number))
    time.sleep(vzw_dou_automation_base_test.DEFAULT_DEVICE_COOL_DOWN_TIME)
    # In this test case three calls are made
    PHONE_CALL_COUNT = 3
    metrics_list = []
    for i in range(PHONE_CALL_COUNT):
      # The companion phone mutes on 1st and 3rd calls
      is_companion_muted = 'TRUE' if i % PHONE_CALL_COUNT != 1 else 'FALSE'
      self.run_instrumentation_on_companion(
          'com.google.android.platform.dou.CompanionPhoneVoiceCallTests',
          'testReceiveVoiceCall',
          extra_params=[('recipient_number', dut_phone_number),
                        ('recipient_number_companion', companion_phone_number),
                        ('enable_mute', is_companion_muted)])
      # The dut mutes on 2nd and 3rd calls
      is_dut_muted = 'TRUE' if i % PHONE_CALL_COUNT != 0 else 'FALSE'
      metrics = self.run_and_measure(
          'com.google.android.platform.dou.PhoneVoiceCallWithMuteTests',
          'testVoiceCall',
          extra_params=[('wifi_ssid', vzw_dou_automation_base_test.WIFI_SSID),
                        ('recipient_number', dut_phone_number),
                        ('recipient_number_companion', companion_phone_number),
                        ('enable_mute', is_dut_muted)],
          count=i,
          attempt_number=attempt_number)
      metrics_list.append(metrics)
    final_metrics = self._generate_final_metrics(metrics_list)
    self.record_metrics(final_metrics)
    self.validate_metrics(final_metrics)

  @repeated_test(
      num_passes=1,
      acceptable_failures=0,
      result_selector=vzw_dou_automation_base_test.get_median_current)
  def test_voice_call_bluetooth(self, attempt_number):
    """Measures power when the device is on call with bluetooth paired."""
    self.connect_companion_to_wifi()
    self.log_in_companion_gmail_account()
    self.pair_dut_bluetooth()
    companion_phone_number = self.get_phone_number(self.ad_cp)
    self.log.debug(
        'The companion phone number is {}'.format(companion_phone_number))
    dut_phone_number = self.get_phone_number(self.ad_dut)
    self.log.debug('The dut phone number is {}'.format(dut_phone_number))
    bt_device_address = self.ad_dut.bt_device_address
    self.log.info('The bt device address is {}'.format(bt_device_address))
    self.adb_run(goog.disable_playstore)
    time.sleep(vzw_dou_automation_base_test.DEFAULT_DEVICE_COOL_DOWN_TIME)

    self.run_instrumentation_on_companion(
        'com.google.android.platform.dou.CompanionSimulateVoiceTests',
        'testPlayYoutube',
        extra_params=[('wifi_ssid', vzw_dou_automation_base_test.WIFI_SSID),
                      ('recipient_number', dut_phone_number)])

    metrics = self.run_and_measure(
        'com.google.android.platform.dou.PhoneVoiceCallTests',
        'testVoiceCall',
        extra_params=[('recipient_number', dut_phone_number),
                      ('recipient_number_companion', companion_phone_number),
                      ('bluetooth_device_mac_addr', bt_device_address)],
        attempt_number=attempt_number)

    self.record_metrics(metrics)
    self.validate_metrics(metrics)

  @repeated_test(
      num_passes=1,
      acceptable_failures=0,
      result_selector=vzw_dou_automation_base_test.get_median_current)
  def test_voice_call_and_browser(self, attempt_number):
    """Measures power when the device is on call with bluetooth paired."""

    self.pair_dut_bluetooth()
    self.connect_companion_to_wifi()
    self.log_in_companion_gmail_account()
    companion_phone_number = self.get_phone_number(self.ad_cp)
    self.log.debug(
        'The companion phone number is {}'.format(companion_phone_number))
    dut_phone_number = self.get_phone_number(self.ad_dut)
    self.log.debug('The dut phone number is {}'.format(dut_phone_number))
    bt_device_address = self.ad_dut.bt_device_address
    self.log.info('The bt device address is {}'.format(bt_device_address))
    time.sleep(vzw_dou_automation_base_test.DEFAULT_DEVICE_COOL_DOWN_TIME)

    self.run_instrumentation_on_companion(
        'com.google.android.platform.dou.CompanionSimulateVoiceTests',
        'testPlayYoutube',
        extra_params=[('wifi_ssid', vzw_dou_automation_base_test.WIFI_SSID),
                      ('recipient_number', dut_phone_number)])

    metrics = self.run_and_measure(
        'com.google.android.platform.dou.PhoneVoiceCallAndBrowserTests',
        'testVoiceCallAndBrowser',
        extra_params=[('recipient_number', dut_phone_number),
                      ('recipient_number_companion', companion_phone_number),
                      ('wifi_ssid', vzw_dou_automation_base_test.WIFI_SSID),
                      ('bluetooth_device_mac_addr', bt_device_address)],
        attempt_number=attempt_number)

    self.record_metrics(metrics)
    self.validate_metrics(metrics)

  @repeated_test(
      num_passes=3,
      acceptable_failures=2,
      result_selector=vzw_dou_automation_base_test.get_median_current)
  def test_voice_call(self, attempt_number):
    """Measures power when the device is on call."""
    self.connect_companion_to_wifi()
    self.log_in_companion_gmail_account()
    companion_phone_number = self.get_phone_number(self.ad_cp)
    self.log.debug(
        'The companion phone number is {}'.format(companion_phone_number))
    dut_phone_number = self.get_phone_number(self.ad_dut)
    self.log.debug('The dut phone number is {}'.format(dut_phone_number))
    time.sleep(vzw_dou_automation_base_test.DEFAULT_DEVICE_COOL_DOWN_TIME)

    self.run_instrumentation_on_companion(
        'com.google.android.platform.dou.CompanionSimulateVoiceTests',
        'testPlayYoutube',
        extra_params=[('wifi_ssid', vzw_dou_automation_base_test.WIFI_SSID),
                      ('recipient_number', dut_phone_number),
                      ('recipient_number_companion', companion_phone_number)])

    metrics = self.run_and_measure(
        'com.google.android.platform.dou.PhoneVoiceCallTests',
        'testVoiceCall',
        extra_params=[('recipient_number', dut_phone_number),
                      ('recipient_number_companion', companion_phone_number)],
        attempt_number=attempt_number)

    self.record_metrics(metrics)
    self.validate_metrics(metrics)

  @repeated_test(
      num_passes=3,
      acceptable_failures=2,
      result_selector=vzw_dou_automation_base_test.get_median_current)
  def test_mobile_hotspot(self, attempt_number):
    """Measures power for companion connect to the dut mobile hotspot."""

    self.connect_companion_to_wifi()
    self.log_in_companion_gmail_account()
    companion_phone_number = self.get_phone_number(self.ad_cp)
    self.log.debug(
        'The companion phone number is {}'.format(companion_phone_number))

    dut_mhs_ssid = self.generate_random_ssid()
    self.log.info('The dut_mhs_ssid is {}'.format(dut_mhs_ssid))

    self.run_instrumentation_on_companion(
        'com.google.android.platform.dou.CompanionMHSTests',
        'testPlayYoutubeViaMHS',
        extra_params=[('recipient_number', dut_mhs_ssid),
                      ('recipient_number_companion', companion_phone_number)])

    metrics = self.run_and_measure(
        'com.google.android.platform.dou.MobileHotspotTests',
        'testMobileHotspot',
        extra_params=[('recipient_number', dut_mhs_ssid),
                      ('recipient_number_companion', companion_phone_number)],
        attempt_number=attempt_number)

    self.record_metrics(metrics)
    self.validate_metrics(metrics)

  def _generate_final_metrics(self, metrics_list):
    """General a final metrics by combine each weighted value in the original metrics.

        Results = Talk *40% + Listen *40% + Silence *20%

        Args:
            metrics: The metrics is a dictionary with a list of
              power_metrics.Metric as value

        Returns:
            A recalculated dictionary
        """
    final_list = []
    final_metrics = {}
    combined_seg_name = ''

    for index, metrics in enumerate(metrics_list):
      for key, result_list in metrics.items():
        if not final_list:
          for result_metrics in result_list:
            final_list.append(copy.deepcopy(result_metrics))
            final_list[-1].value = 0
        if index == 2:
          for i, result_metrics in enumerate(result_list):
            if i == 0:
              self.log.info('The result metrix index is %s and value is %s',
                            index, result_metrics.value)
            final_list[i].value += result_metrics.value * 0.2
        else:
          for i, result_metrics in enumerate(result_list):
            if i == 0:
              self.log.info('The result metrix index is %s and value is %s',
                            index, result_metrics.value)
            final_list[i].value += result_metrics.value * 0.4
        if combined_seg_name == '':
          combined_seg_name = key

    final_metrics[combined_seg_name] = final_list
    return final_metrics
