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

import os

from acts.test_utils.instrumentation.device.apps.app_installer import AppInstaller
from acts.test_utils.instrumentation.device.apps.permissions import PermissionsUtil
from acts.test_utils.instrumentation.device.command.adb_commands import common
from acts.test_utils.instrumentation.device.command.adb_commands import goog
from acts.test_utils.instrumentation.device.command.instrumentation_command_builder import \
  DEFAULT_INSTRUMENTATION_LOG_OUTPUT
from acts.test_utils.instrumentation.device.command.instrumentation_command_builder import \
  InstrumentationTestCommandBuilder
from acts.test_utils.instrumentation.instrumentation_base_test import \
  InstrumentationTestError
from acts.test_utils.instrumentation.instrumentation_proto_parser import \
  DEFAULT_INST_LOG_DIR
from acts.test_utils.instrumentation.power.vzw_dou_automation import \
  vzw_dou_automation_base_test

AUTOTESTER_LOG = 'autotester.log'
SCREENSHOTS_DIR = 'test_screenshots'


class VzWDoUAutomationCompBaseTest(
    vzw_dou_automation_base_test.VzWDoUAutomationBaseTest):
  """Base class that implements common functionality of
  days of use test cases with companion phone
  """

  def __init__(self, configs):
    super().__init__(configs)
    self._companion_test_apk = None
    self._companion_instr_cmd_builder = None

  def setup_class(self):
    """Class setup"""
    super().setup_class()
    self.ad_cp = self.android_devices[1]

  def setup_test(self):
    """Test setup"""
    super().setup_test()
    self._prepare_companion_device()
    self._companion_instr_cmd_builder = self._instr_command_builder()

  def _prepare_companion_device(self):
    """Prepares the companion device for power testing."""
    self._cleanup_companion_test_files()
    self._companion_permissions_util = PermissionsUtil(
        self.ad_cp, self.get_file_from_config('permissions_apk'))
    self._companion_permissions_util.grant_all()
    self._install_companion_test_apk()
    self.base_companion_device_configuration()

  def _install_companion_test_apk(self):
    """Installs test apk on the companion device."""
    test_apk_file = self.get_file_from_config('test_apk')
    self._companion_test_apk = AppInstaller(self.ad_cp, test_apk_file)
    self._companion_test_apk.install('-g')
    if not self._companion_test_apk.is_installed():
      raise InstrumentationTestError(
          'Failed to install test APK on companion device.')

  def _pull_companion_test_files(self):
    """Pull test-generated files from the companion device onto the log directory."""
    dest = self.ad_cp.device_log_path
    self.ad_cp.log.info(
        'Pulling test generated files from companion device to %s.' % dest)
    for file_name in [DEFAULT_INSTRUMENTATION_LOG_OUTPUT, SCREENSHOTS_DIR]:
      src = os.path.join(self.ad_cp.external_storage_path, file_name)
      self.ad_cp.pull_files(src, dest)

  def _cleanup_companion_test_files(self):
    """Remove test-generated files from the companion device."""
    self.ad_cp.log.info('Cleaning up test generated files on companion device.')
    for file_name in [
        DEFAULT_INST_LOG_DIR, DEFAULT_INSTRUMENTATION_LOG_OUTPUT,
        AUTOTESTER_LOG, SCREENSHOTS_DIR
    ]:
      src = os.path.join(self.ad_cp.external_storage_path, file_name)
      self.adb_run('rm -rf %s' % src, self.ad_cp)

  def _cleanup_companion_device(self):
    """Clean up device after power testing."""
    if self._companion_test_apk:
      self._companion_test_apk.uninstall()
    self._companion_permissions_util.close()
    self._pull_companion_test_files()
    self._cleanup_companion_test_files()

  def teardown_test(self):
    """Test teardown. Takes bugreport and cleans up device."""
    super().teardown_test()
    self._cleanup_companion_device()

  def base_companion_device_configuration(self):
    """Runs the adb commands to prepare the companion phone for days of use power testing."""

    self.log.info('Running base adb setup commands on companion.')
    self.ad_dut.adb.ensure_root()
    self.adb_run(common.test_harness.toggle(True))
    self.adb_run(goog.force_stop_nexuslauncher)
    self.adb_run(goog.disable_playstore)
    self.adb_run(goog.disable_chrome)
    self.adb_run(common.power_stayon)
    self.adb_run(common.mobile_data.toggle(True))
    self.adb_run('input keyevent 82')
    self.adb_run('input keyevent 3')

  def _instr_command_builder(self):
    """Return a command builder for companion devices in power tests """
    builder = InstrumentationTestCommandBuilder.default()
    builder.set_manifest_package(self._companion_test_apk.pkg_name)
    builder.add_flag('--no-isolated-storage')
    builder.set_output_as_text()
    builder.set_nohup()
    return builder

  def run_instrumentation_on_companion(self,
                    instr_class,
                    instr_method=None,
                    req_params=None,
                    extra_params=None):
    """Convenience method for setting up the instrumentation test command,
    running it on the companion device.

    Args:
        instr_class: Fully qualified name of the instrumentation test class
        instr_method: Name of the instrumentation test method
        req_params: List of required parameter names
        extra_params: List of ad-hoc parameters to be passed defined as tuples
          of size 2.
    """
    if instr_method:
      self._companion_instr_cmd_builder.add_test_method(instr_class,
                                                        instr_method)
    else:
      self._companion_instr_cmd_builder.add_test_class(instr_class)
    params = {}
    companion_instr_call_config = self._get_merged_config(
        'companion_instrumentation_call')
    # Add required parameters
    for param_name in req_params or []:
      params[param_name] = companion_instr_call_config.get(
          param_name,
          verify_fn=lambda x: x is not None,
          failure_msg='%s is a required parameter.' % param_name)
    # Add all other parameters
    params.update(companion_instr_call_config)
    for name, value in params.items():
      self._companion_instr_cmd_builder.add_key_value_param(name, value)

    if extra_params:
      for name, value in extra_params:
        self._companion_instr_cmd_builder.add_key_value_param(name, value)

    instr_cmd = self._companion_instr_cmd_builder.build()
    self.log.info('Running instrumentation call on companion: %s' % instr_cmd)
    self.adb_run_async(instr_cmd, ad=self.ad_cp)

  def get_phone_number(self, ad):
    """Retrieve the phone number for the device.

        Args:
            ad: The device to run on.
        Returns: string phone number
    """
    cmd = ('service call iphonesubinfo 16 | fgrep "\'" | cut -d"\'" -f2 | tr -d'
           ' "\\n" | sed "s/\.//g"')
    result = self.adb_run(cmd, ad=ad)
    return result[cmd]