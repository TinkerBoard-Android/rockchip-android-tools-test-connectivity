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

from acts.controllers.anritsu_lib.md8475a import BtsTechnology
from acts.controllers.anritsu_lib.md8475a import LteMimoMode
from acts.controllers.anritsu_lib.md8475a import BtsNumber
from acts.controllers.anritsu_lib.md8475a import BtsPacketRate
from acts.controllers.anritsu_lib.md8475a import TestProcedure
from acts.controllers.anritsu_lib.md8475a import TestPowerControl
from acts.controllers.anritsu_lib.md8475a import TestMeasurement
from acts.test_utils.power.tel_simulations.LteSimulation import LteSimulation


class LteCaSimulation(LteSimulation):

    # Dictionary of lower DL channel number bound for each band.
    LOWEST_DL_CN_DICTIONARY = {
        1: 0,
        2: 600,
        3: 1200,
        4: 1950,
        5: 2400,
        6: 2650,
        7: 2750,
        8: 3450,
        9: 3800,
        10: 4150,
        11: 4750,
        12: 5010,
        13: 5180,
        14: 5280,
        17: 5730,
        18: 5850,
        19: 6000,
        20: 6150,
        21: 6450,
        22: 6600,
        23: 7500,
        24: 7700,
        25: 8040,
        26: 8690,
        27: 9040,
        28: 9210,
        29: 9660,
        30: 9770,
        31: 9870,
        32: 36000,
        33: 36200,
        34: 36350,
        35: 36950,
        36: 37550,
        37: 37750,
        38: 38250,
        39: 38650,
        40: 39650,
        41: 41590,
        42: 45590
    }

    # Simulation config files in the callbox computer.
    # These should be replaced in the future by setting up
    # the same configuration manually.
    LTE_BASIC_SIM_FILE = 'SIM_LTE_CA.wnssp'
    LTE_BASIC_CELL_FILE = 'CELL_LTE_CA_config.wnscp'

    # Simulation config keywords contained in the test name
    PARAM_CA = 'ca'

    # Test config keywords
    KEY_FREQ_BANDS = "freq_bands"

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

        # Get LTE CA frequency bands setting from the test configuration
        if self.KEY_FREQ_BANDS not in test_config:
            self.log.warning("The key '{}' is not set in the config file. "
                             "Setting to null by default.".format(
                                 self.KEY_FREQ_BANDS))

        self.freq_bands = test_config.get(self.KEY_FREQ_BANDS, True)

    def parse_parameters(self, parameters):
        """ Configs an LTE simulation with CA using a list of parameters.

        Calls the parent method first, then consumes parameters specific to LTE

        Args:
            parameters: list of parameters
        """

        # Enable all base stations initially. The ones that are not needed after
        # parsing the CA combo string can be removed.
        self.anritsu.set_simulation_model(
            BtsTechnology.LTE,
            BtsTechnology.LTE,
            BtsTechnology.LTE,
            BtsTechnology.LTE,
            reset=False)

        # Get the CA band configuration

        values = self.consume_parameter(parameters, self.PARAM_CA, 1)

        if not values:
            raise ValueError(
                "The test name needs to include parameter '{}' followed by "
                "the CA configuration. For example: ca_3c7c28a".format(
                    self.PARAM_CA))

        # Carrier aggregation configurations are indicated with the band numbers
        # followed by the CA classes in a single string. For example, for 5 CA
        # using 3C 7C and 28A the parameter value should be 3c7c28a.
        ca_configs = re.findall(r'(\d+[abcABC])', values[1])

        if not ca_configs:
            raise ValueError(
                "The CA configuration has to be indicated with one string as "
                "in the following example: ca_3c7c28a".format(self.PARAM_CA))

        carriers = []
        bts_index = 0

        # Elements in the ca_configs array are combinations of band numbers
        # and CA classes. For example, '7A', '3C', etc.

        for ca in ca_configs:

            band = ca[:-1]
            ca_class = ca[-1]

            if ca_class.upper() == 'B':
                raise ValueError(
                    "Class B carrier aggregation is not supported.")

            if band in carriers:
                raise ValueError(
                    "Intra-band non contiguous carrier aggregation "
                    "is not supported.")

            if ca_class.upper() == 'A':

                if bts_index >= len(self.bts):
                    raise ValueError("This callbox model doesn't allow the "
                                     "requested CA configuration")
                bts_index += 1
                carriers.append(band)

            elif ca_class.upper() == 'C':

                if bts_index + 1 >= len(self.bts):
                    raise ValueError("This callbox model doesn't allow the "
                                     "requested CA configuration")

                # Append this band two times as it will be used for two
                # different carriers.
                carriers.append(band)
                carriers.append(band)

                bts_index += 2

            else:
                raise ValueError("Invalid carrier aggregation configuration: "
                                 "{}{}.".format(band, ca_class))

        # Ensure there are at least two carriers being used
        self.num_carriers = bts_index
        if self.num_carriers < 2:
            raise ValueError("At least two carriers need to be indicated for "
                             "the carrier aggregation sim.")

        # Set the simulation model to use only the base stations that are
        # needed for this CA combination.

        self.anritsu.set_simulation_model(
            *[BtsTechnology.LTE for _ in range(self.num_carriers)],
            reset=False)

        # If base stations use different bands, make sure that the RF cards are
        # not being shared by setting the right maximum MIMO modes
        if self.num_carriers == 2:
            # RF cards are never shared when doing 2CA so 4X4 can be done in
            # both base stations.
            self.bts[0].mimo_support = LteMimoMode.MIMO_4X4
            self.bts[1].mimo_support = LteMimoMode.MIMO_4X4
        if self.num_carriers == 3:
            # 4X4 can only be done in the second base station if it is shared
            # with the primary. If the RF cards cannot be shared, then at most
            # 2X2 can be done.
            self.bts[0].mimo_support = LteMimoMode.MIMO_4X4
            if carriers[0] == carriers[1]:
                self.bts[1].mimo_support = LteMimoMode.MIMO_4X4
            else:
                self.bts[1].mimo_support = LteMimoMode.MIMO_2X2
            self.bts[2].mimo_support = LteMimoMode.MIMO_2X2

        # Enable carrier aggregation
        self.anritsu.set_carrier_aggregation_enabled()

        # Restart the simulation as changing the simulation model will stop it.
        self.anritsu.start_simulation()

        # Setup the bands in the base stations
        for bts_index in range(self.num_carriers):
            self.set_band_with_defaults(
                self.bts[bts_index],
                carriers[bts_index],
                calibrate_if_necessary=bts_index == 0)

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

                # Calculate the channel number for the second carrier to be
                # contiguous to the first one
                channel_number = int(self.LOWEST_DL_CN_DICTIONARY[int(band)] +
                                     bw * 10 - 2)

                # Temporarily adding this line to workaround a bug in the
                # Anritsu callbox in which the channel number needs to be set
                # to a different value before setting it to the final one.
                self.bts[bts_index].dl_channel = str(channel_number + 1)
                time.sleep(8)

                self.bts[bts_index].dl_channel = str(channel_number)

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
            raise ValueError(
                "The test parameter '{}' has to be included in the "
                "test name followed by the MIMO mode for each "
                "carrier separated by underscores.".format(self.PARAM_MIMO))

        if len(mimo_values) != self.num_carriers + 1:
            raise ValueError(
                "The test parameter '{}' has to be followed by "
                "a number of MIMO mode values equal to the number "
                "of carriers being used.".format(self.PARAM_MIMO))

        for bts_index in range(self.num_carriers):

            # Parse and set the requested MIMO mode

            for mimo_mode in LteSimulation.MimoMode:
                if mimo_values[bts_index + 1] == mimo_mode.value:
                    requested_mimo = mimo_mode
                    break
            else:
                raise ValueError(
                    "The mimo mode must be one of %s." %
                    {elem.value
                     for elem in LteSimulation.MimoMode})

            if (requested_mimo == LteSimulation.MimoMode.MIMO_4x4
                    and self.anritsu._md8475_version == 'A'):
                raise ValueError("The test requires 4x4 MIMO, but that is not "
                                 "supported by the MD8475A callbox.")

            self.set_mimo_mode(self.bts[bts_index], requested_mimo)

            # Parse and set the requested TM

            if tm_values:
                for tm in LteSimulation.TransmissionMode:
                    if tm_values[bts_index + 1] == tm.value[2:]:
                        requested_tm = tm
                        break
                else:
                    raise ValueError(
                        "The TM must be one of %s." %
                        {elem.value
                         for elem in LteSimulation.MimoMode})
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

        # Power is not set on the callbox until after the simulation is
        # started. Saving this value in a variable for later
        self.sim_ul_power = ul_power

        # Get downlink power

        dl_power = self.get_downlink_power_from_parameters(parameters)

        # Power is not set on the callbox until after the simulation is
        # started. Saving this value in a variable for later
        self.sim_dl_power = dl_power

        # Setup scheduling mode

        values = self.consume_parameter(parameters, self.PARAM_SCHEDULING, 1)

        if not values:
            scheduling = LteSimulation.SchedulingMode.STATIC
            self.log.warning(
                "The test name does not include the '{}' parameter. Setting to "
                "{} by default.".format(scheduling.value,
                                        self.PARAM_SCHEDULING))
        else:
            for scheduling_mode in LteSimulation.SchedulingMode:
                if values[1].upper() == scheduling_mode.value:
                    scheduling = scheduling_mode
                    break
            else:
                raise ValueError(
                    "The test name parameter '{}' has to be followed by one of "
                    "{}.".format(
                        self.PARAM_SCHEDULING,
                        {elem.value
                         for elem in LteSimulation.SchedulingMode}))

        if scheduling == LteSimulation.SchedulingMode.STATIC:

            values = self.consume_parameter(parameters, self.PARAM_PATTERN, 2)

            if not values:
                self.log.warning(
                    "The '{}' parameter was not set, using 100% RBs for both "
                    "DL and UL. To set the percentages of total RBs include "
                    "the '{}' parameter followed by two ints separated by an "
                    "underscore indicating downlink and uplink percentages."
                    .format(self.PARAM_PATTERN, self.PARAM_PATTERN))
                dl_pattern = 100
                ul_pattern = 100
            else:
                dl_pattern = int(values[1])
                ul_pattern = int(values[2])

            if (dl_pattern, ul_pattern) not in [(0, 100), (100, 0), (100,
                                                                     100)]:
                raise ValueError(
                    "Only full RB allocation for DL or UL is supported in CA "
                    "sims. The allowed combinations are 100/0, 0/100 and "
                    "100/100.")

            if self.dl_256_qam and bw == 1.4:
                mcs_dl = 26
            elif not self.dl_256_qam and self.tbs_pattern_on and bw != 1.4:
                mcs_dl = 28
            else:
                mcs_dl = 27

            if self.ul_64_qam:
                mcs_ul = 28
            else:
                mcs_ul = 23

            for bts_index in range(self.num_carriers):

                dl_rbs, ul_rbs = self.allocation_percentages_to_rbs(
                    self.bts[bts_index], dl_pattern, ul_pattern)

                self.set_scheduling_mode(
                    self.bts[bts_index],
                    LteSimulation.SchedulingMode.STATIC,
                    packet_rate=BtsPacketRate.LTE_MANUAL,
                    nrb_dl=dl_rbs,
                    nrb_ul=ul_rbs,
                    mcs_ul=mcs_ul,
                    mcs_dl=mcs_dl)

        else:

            for bts_index in range(self.num_carriers):

                self.set_scheduling_mode(self.bts[bts_index],
                                         LteSimulation.SchedulingMode.DYNAMIC)

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

    def start_test_case(self):
        """ Attaches the phone to all the other basestations.

        Starts the CA test case. Requires being attached to
        basestation 1 first.

        """

        # Trigger UE capability enquiry from network to get
        # UE supported CA band combinations. Here freq_bands is a hex string.

        self.anritsu.trigger_ue_capability_enquiry(self.freq_bands)

        testcase = self.anritsu.get_AnritsuTestCases()
        # Setting the procedure to selection is needed because of a bug in the
        # instrument's software (b/139547391).
        testcase.procedure = TestProcedure.PROCEDURE_SELECTION
        testcase.procedure = TestProcedure.PROCEDURE_MULTICELL
        testcase.power_control = TestPowerControl.POWER_CONTROL_DISABLE
        testcase.measurement_LTE = TestMeasurement.MEASUREMENT_DISABLE

        for bts_index in range(1, self.num_carriers):
            self.bts[bts_index].dl_cc_enabled = True

        self.anritsu.start_testcase()

        retry_counter = 0
        self.log.info("Waiting for the test case to start...")
        time.sleep(5)

        while self.anritsu.get_testcase_status() == "0":
            retry_counter += 1
            if retry_counter == 3:
                raise RuntimeError("The test case failed to start after {} "
                                   "retries. The connection between the phone "
                                   "and the basestation might be unstable."
                                   .format(retry_counter))
            time.sleep(10)

    def maximum_downlink_throughput(self):
        """ Calculates maximum downlink throughput as the sum of all the active
        carriers.
        """

        return sum(
            self.bts_maximum_downlink_throughtput(self.bts[bts_index])
            for bts_index in range(self.num_carriers))

    def start(self):
        """ Set the signal level for the secondary carriers, as the base class
        implementation of this method will only set up downlink power for the
        primary carrier component. """

        super().start()

        for bts_index in range(1, self.num_carriers):
            self.log.info("Setting DL power for BTS{}.".format(bts_index + 1))
            if self.sim_dl_power:
                self.bts[bts_index].output_level = \
                    self.calibrated_downlink_rx_power(self.bts1,
                                                      self.sim_dl_power)
