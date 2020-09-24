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

from acts.test_utils.instrumentation.device.apps.dismiss_dialogs import \
    DialogDismissalUtil
from acts.test_utils.instrumentation.device.command.adb_commands import common
from acts.test_utils.instrumentation.power import instrumentation_power_test

from acts import signals
from acts.controllers.android_lib.errors import AndroidDeviceError

BIG_FILE_PUSH_TIMEOUT = 600


class LocalYoutubeMusicPlaybackTest(
    instrumentation_power_test.InstrumentationPowerTest):
    """Test class for running instrumentation test local youtube music playback"""

    def _prepare_device(self):
        super()._prepare_device()
        self.push_to_external_storage(
            self.get_file_from_config('music_file'),
            timeout=BIG_FILE_PUSH_TIMEOUT)
        self.base_device_configuration()
        self.adb_run(common.disable_audio.toggle(False))
        self._dialog_util = DialogDismissalUtil(
            self.ad_dut, self.get_file_from_config('dismiss_dialogs_apk')
        )
        self._dialog_util.dismiss_dialogs('YTMusic')
        self.adb_run('am force-stop com.google.android.apps.youtube.music')
        self.trigger_scan_on_external_storage()

        try:
            # The scan trigger does not work reliably, adding a reboot ensures
            # that files will be made visible to apps before the test.
            self.ad_dut.reboot(timeout=180)
        except (AndroidDeviceError, TimeoutError):
            raise signals.TestFailure('Device did not reboot successfully.')

    def test_local_youtube_music_playback(self):
        """Measures power when the device is playing music."""
        music_params = [
            ('album_name', 'Internal Illusions, External Delusions'),
            ('song_name', 'Oceanic Dawn')
        ]
        metrics = self.run_and_measure(
            'com.google.android.platform.powertests.YoutubeMusicTests',
            'testLocalPlaybackBackground',
            extra_params=music_params
        )
        self.record_metrics(metrics)
        self.validate_metrics(metrics)