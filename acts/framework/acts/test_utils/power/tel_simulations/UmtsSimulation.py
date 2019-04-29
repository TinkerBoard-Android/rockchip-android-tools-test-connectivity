#!/usr/bin/env python3.4
#
#   Copyright 2018 - The Android Open Source Project
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
from acts.controllers.anritsu_lib.md8475a import BtsPacketRate
from acts.test_utils.power.tel_simulations.BaseSimulation import BaseSimulation
from acts.test_utils.tel.tel_defines import NETWORK_MODE_WCDMA_ONLY


class UmtsSimulation(BaseSimulation):
    """ Simple UMTS simulation with only one basestation.

    """

    # Simulation config files in the callbox computer.
    # These should be replaced in the future by setting up
    # the same configuration manually.

    UMTS_BASIC_SIM_FILE = ('C:\\Users\MD8475A\Documents\DAN_configs\\'
                           'SIM_default_WCDMA.wnssp')

    UMTS_R99_CELL_FILE = ('C:\\Users\MD8475A\Documents\\DAN_configs\\'
                          'CELL_WCDMA_R99_config.wnscp')

    UMTS_R7_CELL_FILE = ('C:\\Users\MD8475A\Documents\\DAN_configs\\'
                         'CELL_WCDMA_R7_config.wnscp')

    UMTS_R8_CELL_FILE = ('C:\\Users\MD8475A\Documents\\DAN_configs\\'
                         'CELL_WCDMA_R8_config.wnscp')

    # Test name parameters
    PARAM_RELEASE_VERSION = "r"
    PARAM_RELEASE_VERSION_99 = "99"
    PARAM_RELEASE_VERSION_8 = "8"
    PARAM_RELEASE_VERSION_7 = "7"
    PARAM_UL_PW = 'pul'
    PARAM_DL_PW = 'pdl'
    PARAM_BAND = "band"

    # Units in which signal level is defined in DOWNLINK_SIGNAL_LEVEL_DICTIONARY
    DOWNLINK_SIGNAL_LEVEL_UNITS = "RSCP"

    # RSCP signal levels thresholds (as reported by Android). Units are dBm
    # Using LTE thresholds + 24 dB to have equivalent SPD
    # 24 dB comes from 10 * log10(3.84 MHz / 15 KHz)

    DOWNLINK_SIGNAL_LEVEL_DICTIONARY = {
        'excellent': -51,
        'high': -76,
        'medium': -86,
        'weak': -96
    }

    # Transmitted output power for the phone
    # Stronger Tx power means that the signal received by the BTS is weaker
    # Units are dBm

    UPLINK_SIGNAL_LEVEL_DICTIONARY = {
        'excellent': -20,
        'high': 2,
        'medium': 8,
        'weak': 15,
        'edge': 23
    }

    def __init__(self, anritsu, log, dut, test_config, calibration_table):
        """ Configures Anritsu system for UMTS simulation with 1 basetation

        Loads a simple UMTS simulation enviroment with 1 basestation. It also
        creates the BTS handle so we can change the parameters as desired.

        Args:
            anritsu: the Anritsu callbox controller
            log: a logger handle
            dut: the android device handler
            test_config: test configuration obtained from the config file
            calibration_table: a dictionary containing path losses for
                different bands.

        """

        super().__init__(anritsu, log, dut, test_config, calibration_table)

        anritsu.load_simulation_paramfile(self.UMTS_BASIC_SIM_FILE)

        if not dut.droid.telephonySetPreferredNetworkTypesForSubscription(
                NETWORK_MODE_WCDMA_ONLY,
                dut.droid.subscriptionGetDefaultSubId()):
            log.error("Coold not set preferred network type.")
        else:
            log.info("Preferred network type set.")

        self.release_version = None

    def parse_parameters(self, parameters):
        """ Configs an UMTS simulation using a list of parameters.

        Calls the parent method and consumes parameters specific to UMTS.

        Args:
            parameters: list of parameters
        """

        super().parse_parameters(parameters)

        # Setup band

        values = self.consume_parameter(parameters, self.PARAM_BAND, 1)

        if not values:
            raise ValueError(
                "The test name needs to include parameter '{}' followed by "
                "the required band number.".format(self.PARAM_BAND))

        self.set_band(self.bts1, values[1])

        # Setup release version

        values = self.consume_parameter(parameters, self.PARAM_RELEASE_VERSION,
                                        1)

        if not values or values[1] not in [
                self.PARAM_RELEASE_VERSION_7, self.PARAM_RELEASE_VERSION_8,
                self.PARAM_RELEASE_VERSION_99
        ]:
            raise ValueError(
                "The test name needs to include the parameter {} followed by a "
                "valid release version.".format(self.PARAM_RELEASE_VERSION))

        self.set_release_version(self.bts1, values[1])

        # Setup uplink power

        ul_power = self.get_uplink_power_from_parameters(parameters)

        # Power is not set on the callbox until after the simulation is
        # started. Saving this value in a variable for later
        self.sim_ul_power = ul_power

        # Setup downlink power

        dl_power = self.get_downlink_power_from_parameters(parameters)

        # Power is not set on the callbox until after the simulation is
        # started. Saving this value in a variable for later
        self.sim_dl_power = dl_power

    def set_release_version(self, bts, release_version):
        """ Sets the release version.

        Loads the cell parameter file matching the requested release version.
        Does nothing is release version is already the one requested.

        """

        if release_version == self.release_version:
            self.log.info(
                "Release version is already {}.".format(release_version))
            return
        if release_version == self.PARAM_RELEASE_VERSION_99:

            cell_parameter_file = self.UMTS_R99_CELL_FILE
            packet_rate = BtsPacketRate.WCDMA_DL384K_UL64K

        elif release_version == self.PARAM_RELEASE_VERSION_7:

            cell_parameter_file = self.UMTS_R7_CELL_FILE
            packet_rate = BtsPacketRate.WCDMA_DL21_6M_UL5_76M

        elif release_version == self.PARAM_RELEASE_VERSION_8:

            cell_parameter_file = self.UMTS_R8_CELL_FILE
            packet_rate = BtsPacketRate.WCDMA_DL43_2M_UL5_76M

        else:
            raise ValueError("Invalid UMTS release version number.")

        self.anritsu.load_cell_paramfile(cell_parameter_file)

        # Loading a cell parameter file stops the simulation
        self.start()

        bts.packet_rate = packet_rate
