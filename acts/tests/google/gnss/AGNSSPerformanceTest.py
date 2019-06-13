#!/usr/bin/env python3
#
#   Copyright 2019 - The Android Open Source Project
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

from acts import base_test
from acts.controllers.gnssinst_lib.rohdeschwarz import contest
from acts.test_utils.tel import tel_test_utils


class AGNSSPerformanceTest(base_test.BaseTestClass):

    # User parameters defined in the ACTS config file

    TESTPLAN_KEY = '{}_testplan'
    CONTEST_IP_KEY = 'contest_ip'
    REMOTE_SERVER_PORT_KEY = 'remote_server_port'
    AUTOMATION_PORT_KEY = 'automation_port'
    CUSTOM_FILES_KEY = 'custom_files'
    AUTOMATION_LISTEN_IP = 'automation_listen_ip'
    FTP_USER_KEY = 'ftp_user'
    FTP_PASSWORD_KEY = 'ftp_password'

    def __init__(self, controllers):
        """ Initializes class attributes. """

        super().__init__(controllers)

        self.dut = None
        self.contest = None
        self.contest_ip = None
        self.remote_port = None
        self.automation_port = None
        self.testplan = None

    def setup_class(self):
        """ Executed before any test case is started. Initializes the Contest
        controller and prepares the DUT for testing. """

        req_params = [
            self.CONTEST_IP_KEY, self.REMOTE_SERVER_PORT_KEY,
            self.AUTOMATION_PORT_KEY, self.AUTOMATION_LISTEN_IP,
            self.FTP_USER_KEY, self.FTP_PASSWORD_KEY
        ]

        for param in req_params:
            if param not in self.user_params:
                self.log.error('Required parameter {} is missing in config '
                               'file.'.format(param))
                return False

        contest_ip = self.user_params[self.CONTEST_IP_KEY]
        remote_port = self.user_params[self.REMOTE_SERVER_PORT_KEY]
        automation_port = self.user_params[self.AUTOMATION_PORT_KEY]
        listen_ip = self.user_params[self.AUTOMATION_LISTEN_IP]
        ftp_user = self.user_params[self.FTP_USER_KEY]
        ftp_password = self.user_params[self.FTP_PASSWORD_KEY]

        self.dut = self.android_devices[0]

        self.contest = contest.Contest(logger=self.log,
                                       remote_ip=contest_ip,
                                       remote_port=remote_port,
                                       automation_listen_ip=listen_ip,
                                       automation_port=automation_port,
                                       dut_on_func=self.set_apm_off,
                                       dut_off_func=self.set_apm_on,
                                       ftp_usr=ftp_user,
                                       ftp_pwd=ftp_password)

    def teardown_class(self):
        """ Executed after completing all selected test cases."""
        self.contest.destroy()

    def setup_test(self):
        """ Executed before every test case.

        Returns:
            False if the setup failed.
        """

        testplan_formatted_key = self.TESTPLAN_KEY.format(self.test_name)

        if testplan_formatted_key not in self.user_params:
            self.log.error('Test plan not indicated in the config file. Use '
                           'the {} key to set the testplan filename.'.format(
                               testplan_formatted_key))
            return False

        self.testplan = self.user_params[testplan_formatted_key]

    def agnss_performance_test(self):
        """ Executes the aGNSS performance test. """

        self.contest.execute_testplan(self.testplan)

    def set_apm_on(self):
        """ Wrapper method to turn airplane mode on.

        This is passed to the Contest object so it can be executed when the
        automation system requires the DUT to be set to 'off' state.
        """

        tel_test_utils.toggle_airplane_mode(self.log, self.dut, True)

    def set_apm_off(self):
        """ Wrapper method to turn airplane mode off.

        This is passed to the Contest object so it can be executed when the
        automation system requires the DUT to be set to 'on' state.
        """
        # Wait for the Contest system to initialize the base stations before
        # actually setting APM off.
        time.sleep(5)

        tel_test_utils.toggle_airplane_mode(self.log, self.dut, False)

    def test_agnss_performance(self):
        self.agnss_performance_test()
