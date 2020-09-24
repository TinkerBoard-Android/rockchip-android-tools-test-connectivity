"""Class to configure wireless settings."""

import time
from acts.controllers.ap_lib import hostapd_constants

LEASE_FILE = "/tmp/dhcp.leases"
DNSMASQ_RESTART = "/etc/init.d/dnsmasq restart"
OPEN_SECURITY = "none"
PSK_SECURITY = "psk2"
WEP_SECURITY = "wep"
ENT_SECURITY = "wpa2"
ENABLE_RADIO = "0"
DISABLE_RADIO = "1"
ENABLE_HIDDEN = "1"


class WirelessSettingsApplier(object):
  """Class for wireless settings.

  Attributes:
    ssh: ssh object for the AP.
    wireless_configs: a list of
      acts.controllers.openwrt_lib.wireless_config.WirelessConfig.
    channel_2g: channel for 2G band.
    channel_5g: channel for 5G band.
  """

  def __init__(self, ssh, configs, channel_2g, channel_5g):
    """Initialize wireless settings.

    Args:
      ssh: ssh connection object.
      configs: a list of
        acts.controllers.openwrt_lib.wireless_config.WirelessConfig.
      channel_2g: channel for 2G band.
      channel_5g: channel for 5G band.
    """
    self.ssh = ssh
    self.wireless_configs = configs
    self.channel_2g = channel_2g
    self.channel_5g = channel_5g

  def apply_wireless_settings(self):
    """Configure wireless settings from a list of configs."""

    # set channels for 2G and 5G bands
    self.ssh.run("uci set wireless.radio1.channel='%s'" % self.channel_2g)
    self.ssh.run("uci set wireless.radio0.channel='%s'" % self.channel_5g)

    # disable default OpenWrt SSID
    self.ssh.run("uci set wireless.default_radio1.disabled='%s'" %
                 DISABLE_RADIO)
    self.ssh.run("uci set wireless.default_radio0.disabled='%s'" %
                 DISABLE_RADIO)

    # Enable radios
    self.ssh.run("uci set wireless.radio1.disabled='%s'" % ENABLE_RADIO)
    self.ssh.run("uci set wireless.radio0.disabled='%s'" % ENABLE_RADIO)

    for config in self.wireless_configs:

      # configure open network
      if config.security == OPEN_SECURITY:
        if config.band == hostapd_constants.BAND_2G:
          self.ssh.run("uci set wireless.default_radio1.ssid='%s'" %
                       config.ssid)
          self.ssh.run("uci set wireless.default_radio1.disabled='%s'" %
                       ENABLE_RADIO)
          if config.hidden:
            self.ssh.run("uci set wireless.default_radio1.hidden='%s'" %
                         ENABLE_HIDDEN)
        elif config.band == hostapd_constants.BAND_5G:
          self.ssh.run("uci set wireless.default_radio0.ssid='%s'" %
                       config.ssid)
          self.ssh.run("uci set wireless.default_radio0.disabled='%s'" %
                       ENABLE_RADIO)
          if config.hidden:
            self.ssh.run("uci set wireless.default_radio0.hidden='%s'" %
                         ENABLE_HIDDEN)
        continue

      self.ssh.run("uci set wireless.%s='wifi-iface'" % config.name)
      if config.band == hostapd_constants.BAND_2G:
        self.ssh.run("uci set wireless.%s.device='radio1'" % config.name)
      else:
        self.ssh.run("uci set wireless.%s.device='radio0'" % config.name)
      self.ssh.run("uci set wireless.%s.network='%s'" %
                   (config.name, config.iface))
      self.ssh.run("uci set wireless.%s.mode='ap'" % config.name)
      self.ssh.run("uci set wireless.%s.ssid='%s'" %
                   (config.name, config.ssid))
      self.ssh.run("uci set wireless.%s.encryption='%s'" %
                   (config.name, config.security))
      if config.security == PSK_SECURITY:
        self.ssh.run("uci set wireless.%s.key='%s'" %
                     (config.name, config.password))
      elif config.security == WEP_SECURITY:
        self.ssh.run("uci set wireless.%s.key%s='%s'" %
                     (config.name, config.wep_key_num, config.wep_key))
        self.ssh.run("uci set wireless.%s.key='%s'" %
                     (config.name, config.wep_key_num))
      elif config.security == ENT_SECURITY:
        self.ssh.run("uci set wireless.%s.auth_secret='%s'" %
                     (config.name, config.radius_server_secret))
        self.ssh.run("uci set wireless.%s.auth_server='%s'" %
                     (config.name, config.radius_server_ip))
        self.ssh.run("uci set wireless.%s.auth_port='%s'" %
                     (config.name, config.radius_server_port))
      if config.hidden:
        self.ssh.run("uci set wireless.%s.hidden='%s'" %
                     (config.name, ENABLE_HIDDEN))

    self.ssh.run("uci commit wireless")
    self.ssh.run("cp %s %s.tmp" % (LEASE_FILE, LEASE_FILE))

  def cleanup_wireless_settings(self):
    """Reset wireless settings to default."""
    self.ssh.run("wifi down")
    self.ssh.run("rm -f /etc/config/wireless")
    self.ssh.run("wifi config")
    self.ssh.run("cp %s.tmp %s" % (LEASE_FILE, LEASE_FILE))
    self.ssh.run(DNSMASQ_RESTART)
    time.sleep(9)

