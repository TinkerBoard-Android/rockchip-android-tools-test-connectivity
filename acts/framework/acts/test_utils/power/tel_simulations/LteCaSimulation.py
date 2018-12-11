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
import re
import time

from acts.controllers.anritsu_lib.md8475a import BtsNumber
from acts.controllers.anritsu_lib.md8475a import TestProcedure
from acts.controllers.anritsu_lib.md8475a import TestPowerControl
from acts.controllers.anritsu_lib.md8475a import TestMeasurement
from acts.test_utils.power.tel_simulations.LteSimulation import LteSimulation


class LteCaSimulation(LteSimulation):
    # Simulation config files in the callbox computer.
    # These should be replaced in the future by setting up
    # the same configuration manually.
    LTE_BASIC_SIM_FILE = 'SIM_LTE_CA'
    LTE_BASIC_CELL_FILE = 'CELL_LTE_CA_config'

    # Simulation config keywords contained in the test name
    PARAM_CA = 'ca'

    def __init__(self, anritsu, log, dut, test_config, calibration_table):
        """ Configures Anritsu system for LTE simulation with carrier
        aggregation.

        Loads a simple LTE simulation enviroment with 5 basestations.

        Args:
            anritsu: the Anritsu callbox controller
            log: a logger handle
            dut: the android device handler
            test_config: test configuration obtained from the config file
            calibration_table: a dictionary containing path losses for
                different bands.

        """

        super().__init__(anritsu, log, dut, test_config, calibration_table)

        self.bts = [self.bts1, self.anritsu.get_BTS(BtsNumber.BTS2)]

        if self.anritsu._md8475_version == 'B':
            self.bts.extend([
                anritsu.get_BTS(BtsNumber.BTS3),
                anritsu.get_BTS(BtsNumber.BTS4),
                anritsu.get_BTS(BtsNumber.BTS5)
            ])

    def parse_parameters(self, parameters):
        """ Configs an LTE simulation with CA using a list of parameters.

        Calls the parent method first, then consumes parameters specific to LTE

        Args:
            parameters: list of parameters
        Returns:
            False if there was an error while parsing the config
        """

        if not super(LteSimulation, self).parse_parameters(parameters):
            return False

        # Get the CA band configuration

        values = self.consume_parameter(parameters, self.PARAM_CA, 1)

        if not values:
            self.log.error(
                "The test name needs to include parameter '{}' followed by "
                "the CA configuration. For example: ca_3c7c28a".format(
                    self.PARAM_CA))
            return False

        # Carrier aggregation configurations are indicated with the band numbers
        # followed by the CA classes in a single string. For example, for 5 CA
        # using 3C 7C and 28A the parameter value should be 3c7c28a.
        ca_configs = re.findall(r'(\d+[abcABC])', values[1])

        if not ca_configs:
            self.log.error(
                "The CA configuration has to be indicated with one string as "
                "in the following example: ca_3c7c28a".format(self.PARAM_CA))
            return False

        carriers = []
        bts_index = 0

        # Elements in the ca_configs array are combinations of band numbers
        # and CA classes. For example, '7A', '3C', etc.

        for ca in ca_configs:

            band = int(ca[:-1])
            ca_class = ca[-1]

            if ca_class.upper() == 'B':
                self.log.error("Class B carrier aggregation is not supported.")
                return False

            if band in carriers:
                self.log.error("Intra-band non contiguous carrier aggregation "
                               "is not supported.")
                return False

            if ca_class.upper() == 'A':

                if bts_index >= len(self.bts):
                    self.log.error("This callbox model doesn't allow the "
                                   "requested CA configuration")
                    return False

                self.set_band_with_defaults(
                    self.bts[bts_index],
                    band,
                    calibrate_if_necessary=bts_index == 0)

                bts_index += 1

            elif ca_class.upper() == 'C':

                if bts_index + 1 >= len(self.bts):
                    self.log.error("This callbox model doesn't allow the "
                                   "requested CA configuration")
                    return False

                self.set_band_with_defaults(
                    self.bts[bts_index],
                    band,
                    calibrate_if_necessary=bts_index == 0)
                self.set_band(
                    self.bts[bts_index + 1],
                    band,
                    calibrate_if_necessary=False)

                bts_index += 2

            else:
                self.log.error("Invalid carrier aggregation configuration: "
                               "{}{}.".format(band, ca_class))
                return False

            carriers.append(band)

        # Ensure there are at least two carriers being used
        self.num_carriers = bts_index
        if self.num_carriers < 2:
            self.log.error("At least two carriers need to be indicated for the"
                           " carrier aggregation sim.")
            return False

        # Get the bw for each carrier
        # This is an optional parameter, by default the maximum bandwidth for
        # each band will be selected.

        values = self.consume_parameter(parameters, self.PARAM_BW,
                                        self.num_carriers)

        bts_index = 0

        for ca in ca_configs:

            band = int(ca[:-1])
            ca_class = ca[-1]

            if values:
                bw = int(values[1 + bts_index])
            else:
                bw = max(self.allowed_bandwidth_dictionary[band])

            self.set_channel_bandwidth(self.bts[bts_index], bw)
            bts_index += 1

            if ca_class.upper() == 'C':

                self.set_channel_bandwidth(self.bts[bts_index], bw)

                # Temporarily adding this line to workaround a bug in the
                # Anritsu callbox in which the channel number needs to be set
                # to a different value before setting it to the final one.
                self.bts[bts_index].dl_channel = str(
                    int(self.bts[bts_index - 1].dl_channel) + bw * 10 - 1)
                time.sleep(8)

                self.bts[bts_index].dl_channel = str(
                    int(self.bts[bts_index - 1].dl_channel) + bw * 10 - 2)

                bts_index += 1

        # Get the TM for each carrier
        # This is an optional parameter, by the default value depends on the
        # MIMO mode for each carrier

        tm_values = self.consume_parameter(parameters, self.PARAM_TM,
                                           self.num_carriers)

        # Get the MIMO mode for each carrier

        mimo_values = self.consume_parameter(parameters, self.PARAM_MIMO,
                                             self.num_carriers)

        if not mimo_values:
            self.log.error("The test parameter '{}' has to be included in the "
                           "test name followed by the MIMO mode for each "
                           "carrier separated by underscores.".format(
                               self.PARAM_MIMO))
            return False

        if len(mimo_values) != self.num_carriers + 1:
            self.log.error("The test parameter '{}' has to be followed by "
                           "a number of MIMO mode values equal to the number "
                           "of carriers being used.".format(self.PARAM_MIMO))
            return False

        for bts_index in range(self.num_carriers):

            # Parse and set the requested MIMO mode

            for mimo_mode in LteSimulation.MimoMode:
                if mimo_values[bts_index + 1] == mimo_mode.value:
                    requested_mimo = mimo_mode
                    break
            else:
                self.log.error("The mimo mode must be one of %s." %
                               {elem.value
                                for elem in LteSimulation.MimoMode})
                return False

            if (requested_mimo == LteSimulation.MimoMode.MIMO_4x4
                    and self.anritsu._md8475_version == 'A'):
                self.log.error("The test requires 4x4 MIMO, but that is not "
                               "supported by the MD8475A callbox.")
                return False

            self.set_mimo_mode(self.bts[bts_index], requested_mimo)

            # Parse and set the requested TM

            if tm_values:
                for tm in LteSimulation.TransmissionMode:
                    if tm_values[bts_index + 1] == tm.value[2:]:
                        requested_tm = tm
                        break
                else:
                    self.log.error(
                        "The TM must be one of %s." %
                        {elem.value
                         for elem in LteSimulation.MimoMode})
                    return False
            else:
                # Provide default values if the TM parameter is not set
                if requested_mimo == LteSimulation.MimoMode.MIMO_1x1:
                    requested_tm = LteSimulation.TransmissionMode.TM1
                else:
                    requested_tm = LteSimulation.TransmissionMode.TM3

            self.set_transmission_mode(self.bts[bts_index], requested_tm)

            self.log.info("Cell {} was set to {} and {} MIMO.".format(
                bts_index + 1, requested_tm.value, requested_mimo.value))

        # Get uplink power

        ul_power = self.get_uplink_power_from_parameters(parameters)

        if not ul_power:
            return False

        # Power is not set on the callbox until after the simulation is
        # started. Saving this value in a variable for later
        self.sim_ul_power = ul_power

        # Get downlink power

        dl_power = self.get_downlink_power_from_parameters(parameters)

        if not dl_power:
            return False

        # Power is not set on the callbox until after the simulation is
        # started. Saving this value in a variable for later
        self.sim_dl_power = dl_power

        # No errors were found
        return True

    def set_band_with_defaults(self, bts, band, calibrate_if_necessary=True):
        """ Switches to the given band restoring default values

        Ensures the base station is switched from a different band so
        band-dependent default values are restored.

        Args:
            bts: basestation handle
            band: desired band
            calibrate_if_necessary: if False calibration will be skipped

        """

        # If the band is already the desired band, temporarily switch to
        # another band to trigger restoring default values.
        if int(bts.band) == band:
            # Using bands 1 and 2 but it could be any others
            bts.band = '1' if band != 1 else '2'

        self.set_band(bts, band, calibrate_if_necessary=calibrate_if_necessary)

    def set_downlink_rx_power(self, bts, rsrp):
        """ Sets downlink rx power in RSRP using calibration for every cell

        Calls the method in the parent class for each base station.

        Args:
            bts: this argument is ignored, as all the basestations need to have
                the same downlink rx power
            rsrp: desired rsrp, contained in a key value pair
        """

        for bts_index in range(self.num_carriers):
            self.log.info("Setting DL power for BTS{}.".format(bts_index + 1))
            # Use parent method to set signal level
            super().set_downlink_rx_power(self.bts[bts_index], rsrp)

    def start_test_case(self):
        """ Attaches the phone to all the other basestations.

        Starts the CA test case. Requires being attached to
        basestation 1 first.

        """

        testcase = self.anritsu.get_AnritsuTestCases()
        testcase.procedure = TestProcedure.PROCEDURE_MULTICELL
        testcase.power_control = TestPowerControl.POWER_CONTROL_DISABLE
        testcase.measurement_LTE = TestMeasurement.MEASUREMENT_DISABLE

        for bts_index in range(1, len(self.bts)):
            self.bts[bts_index].dl_cc_enabled = bts_index < self.num_carriers

        self.anritsu.start_testcase()

        retry_counter = 0
        self.log.info("Waiting for the test case to start...")
        time.sleep(5)

        while self.anritsu.get_testcase_status() == "0":
            retry_counter += 1
            if retry_counter == 3:
                self.log.error("The test case failed to start.")
                return False
            time.sleep(10)

        return True
