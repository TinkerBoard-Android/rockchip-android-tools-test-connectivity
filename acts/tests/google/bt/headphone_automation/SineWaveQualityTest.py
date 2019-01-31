from acts import asserts
from acts.signals import TestPass
from acts.test_utils.audio_analysis_lib import audio_analysis
from acts.test_utils.bt.A2dpCodecBaseTest import A2dpCodecBaseTest


class SineWaveQualityTest(A2dpCodecBaseTest):

    def setup_class(self):
        super().setup_class()
        channel_results = audio_analysis.get_file_anomaly_durations(
            filename=self.host_music_file,
            **self.audio_params.get('anomaly_params', {}))
        # If file specified in test config is not a sine wave tone, this fails.
        for channel, anomalies in channel_results.items():
            asserts.assert_equal(anomalies, [], 'Test file not pure',
                extras=self.metrics)
        self.log.info('Test file inspected.')

    def test_streaming(self):
        self.stream_music_on_codec(**self.codecs[0])
        self.run_thdn_analysis()
        self.run_anomaly_detection()
        raise TestPass('Completed music streaming.', extras=self.metrics)
