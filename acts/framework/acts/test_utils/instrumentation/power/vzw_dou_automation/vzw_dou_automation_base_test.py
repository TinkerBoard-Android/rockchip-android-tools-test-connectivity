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

import time

from acts.test_utils.instrumentation.power import instrumentation_power_test
from acts.test_utils.instrumentation.device.command.adb_commands import common
from acts.test_utils.instrumentation.device.command.adb_commands import goog
from acts.test_utils.instrumentation.device.apps.app_installer import AppInstaller
from acts.test_utils.instrumentation.instrumentation_base_test import InstrumentationTestError

DEFAULT_WAIT_TO_FASTBOOT_MODE = 10

class VzWDoUAutomationBaseTest(
    instrumentation_power_test.InstrumentationPowerTest):
  """Base class that implements common functionality of
  days of use test cases
  """

  def base_device_configuration(self):
    """Runs the adb commands for days of use power testing."""

    self.log.info('Running base adb setup commands.')
    self.ad_dut.adb.ensure_root()
    self.adb_run(common.dismiss_keyguard)
    self.adb_run(goog.location_off_warning_dialog.toggle(False))
    self.adb_run(common.airplane_mode.toggle(False))
    self.adb_run(common.auto_rotate.toggle(False))
    self.adb_run(common.screen_brightness.set_value(58))
    self.adb_run(common.screen_adaptive_brightness.toggle(False))
    self.adb_run(common.modem_diag.toggle(False))
    self.adb_run(common.skip_gesture.toggle(False))
    self.adb_run(common.screensaver.toggle(False))
    self.adb_run(common.doze_pulse_on_pick_up.toggle(False))
    self.adb_run(common.aware_enabled.toggle(False))
    self.adb_run(common.doze_wake_screen_gesture.toggle(False))
    self.adb_run(common.doze_mode.toggle(False))
    self.adb_run(common.doze_always_on.toggle(False))
    self.adb_run(common.silence_gesture.toggle(False))
    self.adb_run(common.single_tap_gesture.toggle(False))
    self.adb_run(goog.location_collection.toggle(False))
    self.adb_run(goog.icing.toggle(False))
    self.adb_run(common.stop_moisture_detection)
    self.adb_run(common.ambient_eq.toggle(False))
    self.adb_run(common.wifi.toggle(False))
    self.adb_run('echo 1 > /d/clk/debug_suspend')
    self.adb_run(common.bluetooth.toggle(True))
    self.adb_run(common.enable_full_batterystats_history)
    self.adb_run(goog.disable_playstore)
    self.adb_run(goog.disable_volta)
    self.adb_run(common.test_harness.toggle(True))
    self.adb_run('am force-stop com.google.android.apps.nexuslauncher')
    self.adb_run('input keyevent 26')
    self.adb_run(common.screen_timeout_ms.set_value(180000))

  def _prepare_device(self):
    """Prepares the device for power testing."""
    self._factory_reset()
    super()._prepare_device()
    self.base_device_configuration()

  def _factory_reset(self):
    """Factory reset device before testing."""
    self.log.info('Running factory reset.')
    self.ad_dut.adb.ensure_root()
    self._install_google_account_util_apk()
    self.adb_run(goog.remove_gmail_account)
    self.ad_dut.reboot()
    self.ad_dut.wait_for_boot_completion()
    self.ad_dut.adb.ensure_root()
    self.ad_dut.log.info("Reboot to bootloader")
    self.ad_dut.stop_services()
    self.ad_dut.adb.reboot("bootloader", ignore_status=True)
    time.sleep(DEFAULT_WAIT_TO_FASTBOOT_MODE)
    self.fastboot_run('-w')
    self.ad_dut.log.info("Reboot in fastboot")
    self.ad_dut.fastboot.reboot()
    self.ad_dut.wait_for_boot_completion()
    self.ad_dut.root_adb()
    if not self.ad_dut.is_sl4a_installed() and self._sl4a_apk:
        self._sl4a_apk.install()
    self.ad_dut.start_services()

  def _install_google_account_util_apk(self):
    """Installs google account util apk on the device."""
    _google_account_util_file = self.get_file_from_config(
        'google_account_util_apk')
    self._google_account_util = AppInstaller(self.ad_dut,
                                             _google_account_util_file)
    self._google_account_util.install('-g')
    if not self._google_account_util.is_installed():
      raise InstrumentationTestError(
          'Failed to install google account util APK.')