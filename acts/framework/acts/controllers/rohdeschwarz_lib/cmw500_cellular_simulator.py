#!/usr/bin/env python3
#
#   Copyright 2019 - The Android Open Source Project
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
from acts.controllers.rohdeschwarz_lib import cmw500
from acts.controllers import cellular_simulator as cc


class CMW500CellularSimulator:
    """ A cellular simulator for telephony simulations based on the CMW 500
    controller. """

    # Indicates if it is able to use 256 QAM as the downlink modulation for LTE
    LTE_SUPPORTS_DL_256QAM = None

    # Indicates if it is able to use 64 QAM as the uplink modulation for LTE
    LTE_SUPPORTS_UL_64QAM = None

    # Indicates if 4x4 MIMO is supported for LTE
    LTE_SUPPORTS_4X4_MIMO = None

    # The maximum number of carriers that this simulator can support for LTE
    LTE_MAX_CARRIERS = None

    def __init__(self, ip_address, port):
        """ Initializes the cellular simulator.

        Args:
            ip_address: the ip address of the CMW500
            port: the port number for the CMW500 controller
        """
        try:
            self.cmw = cmw500.Cmw500(ip_address, port)
        except cmw500.CmwError:
            raise cc.CellularSimulatorError('Could not connect to CMW500.')

    def destroy(self):
        """ Sends finalization commands to the cellular equipment and closes
        the connection. """
        raise NotImplementedError()

    def setup_lte_scenario(self):
        """ Configures the equipment for an LTE simulation. """
        raise NotImplementedError()

    def setup_lte_ca_scenario(self):
        """ Configures the equipment for an LTE with CA simulation. """
        raise NotImplementedError()

    def set_band(self, bts_index, band):
        """ Sets the band for the indicated base station.

        Args:
            bts_index: the base station number
            band: the new band
        """
        raise NotImplementedError()

    def set_input_power(self, bts_index, input_power):
        """ Sets the input power for the indicated base station.

        Args:
            bts_index: the base station number
            input_power: the new input power
        """
        raise NotImplementedError()

    def set_output_power(self, bts_index, output_power):
        """ Sets the output power for the indicated base station.

        Args:
            bts_index: the base station number
            output_power: the new output power
        """
        raise NotImplementedError()

    def set_tdd_config(self, bts_index, tdd_config):
        """ Sets the tdd configuration number for the indicated base station.

        Args:
            bts_index: the base station number
            tdd_config: the new tdd configuration number
        """
        raise NotImplementedError()

    def set_bandwidth(self, bts_index, bandwidth):
        """ Sets the bandwidth for the indicated base station.

        Args:
            bts_index: the base station number
            bandwidth: the new bandwidth
        """
        raise NotImplementedError()

    def set_downlink_channel_number(self, bts_index, channel_number):
        """ Sets the downlink channel number for the indicated base station.

        Args:
            bts_index: the base station number
            channel_number: the new channel number
        """
        raise NotImplementedError()

    def set_mimo_mode(self, bts_index, mimo_mode):
        """ Sets the mimo mode for the indicated base station.

        Args:
            bts_index: the base station number
            mimo_mode: the new mimo mode
        """
        raise NotImplementedError()

    def set_transmission_mode(self, bts_index, transmission_mode):
        """ Sets the transmission mode for the indicated base station.

        Args:
            bts_index: the base station number
            transmission_mode: the new transmission mode
        """
        raise NotImplementedError()

    def set_scheduling_mode(self, bts_index, scheduling_mode, mcs_dl, mcs_ul,
                            nrb_dl, nrb_ul):
        """ Sets the scheduling mode for the indicated base station.

        Args:
            bts_index: the base station number
            scheduling_mode: the new scheduling mode
            mcs_dl: Downlink MCS (only for STATIC scheduling)
            mcs_ul: Uplink MCS (only for STATIC scheduling)
            nrb_dl: Number of RBs for downlink (only for STATIC scheduling)
            nrb_ul: Number of RBs for uplink (only for STATIC scheduling)
        """
        raise NotImplementedError()

    def set_enabled_for_ca(self, bts_index, enabled):
        """ Enables or disables the base station during carrier aggregation.

        Args:
            bts_index: the base station number
            enabled: whether the base station should be enabled for ca.
        """
        raise NotImplementedError()

    def set_dl_modulation(self, bts_index, modulation):
        """ Sets the DL modulation for the indicated base station.

        Args:
            bts_index: the base station number
            modulation: the new DL modulation
        """
        raise NotImplementedError()

    def set_ul_modulation(self, bts_index, modulation):
        """ Sets the UL modulation for the indicated base station.

        Args:
            bts_index: the base station number
            modulation: the new UL modulation
        """
        raise NotImplementedError()

    def set_tbs_pattern_on(self, bts_index, tbs_pattern_on):
        """ Enables or disables TBS pattern in the indicated base station.

        Args:
            bts_index: the base station number
            tbs_pattern_on: the new TBS pattern setting
        """
        raise NotImplementedError()