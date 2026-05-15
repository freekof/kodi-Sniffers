import unittest

import remote_server


class RemoteServerPageTests(unittest.TestCase):
    def test_home_page_has_sniff_and_direct_play_forms(self):
        html = remote_server.build_home_page([])

        self.assertIn('action="/submit"', html)
        self.assertIn('name="url"', html)
        self.assertIn('action="/play"', html)
        self.assertIn('name="play_url"', html)

    def test_home_page_renders_history_with_thumbnail_and_title(self):
        html = remote_server.build_home_page([
            {
                'title': '示例视频',
                'thumbnail': 'https://example.com/thumb.jpg',
                'streams': [],
            }
        ])

        self.assertIn('示例视频', html)
        self.assertIn('https://example.com/thumb.jpg', html)
        self.assertIn('/history/0', html)

    def test_history_detail_renders_stream_resolution_and_url(self):
        html = remote_server.build_history_detail_page({
            'title': '示例视频',
            'thumbnail': 'https://example.com/thumb.jpg',
            'streams': [
                {
                    'label': '[MP4] 1920x1080 - 1080p',
                    'url': 'https://example.com/video.mp4',
                }
            ],
        })

        self.assertIn('示例视频', html)
        self.assertIn('[MP4] 1920x1080 - 1080p', html)
        self.assertIn('https://example.com/video.mp4', html)
        self.assertIn('action="/play"', html)
        self.assertIn('readonly', html)
        self.assertIn('复制地址', html)
        self.assertIn('navigator.clipboard.writeText', html)

    def test_direct_play_submission_sets_received_direct_play_payload(self):
        remote_server.set_received_direct_play_url('https://example.com/live.m3u8')

        self.assertEqual(
            remote_server.get_received_action(),
            {'type': 'play', 'url': 'https://example.com/live.m3u8'},
        )


if __name__ == '__main__':
    unittest.main()
