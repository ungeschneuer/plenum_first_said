import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'parser'))

import mastodon_cred  # noqa: E402

PROTOCOL = {'titel': 'Protokoll der 108. Sitzung des 21. Deutschen Bundestages', 'datum': '12.11.2026',
            'pdf_url': 'https://example.org/21108.pdf',
            'wortseite': 'https://ungeschneuer.github.io/plenum_first_said_website/wort/W%C3%A4rmepumpenpflicht'}


class RecordingAccount:
    def __init__(self, first_id: int):
        self.posts = []
        self.next_id = first_id

    def status_post(self, text, **options):
        self.posts.append((text, options))
        self.next_id += 1
        return {'id': self.next_id}


class MastodonTest(unittest.TestCase):
    def setUp(self):
        self.word_account = RecordingAccount(100)
        self.context_account = RecordingAccount(200)
        patches = [mock.patch.object(mastodon_cred, 'MastodonAPI', self.word_account),
                   mock.patch.object(mastodon_cred, 'MastodonKontextAPI', self.context_account),
                   mock.patch.object(mastodon_cred, 'sleep', lambda seconds: None)]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)

    def test_word_with_context_evidence_and_links_in_one_thread(self):
        metadata = {'link': 'https://optv/media/1', 'speaker': 'Anna Muster', 'party': 'SPD', 'occasion': 'rede'}
        mastodon_id = mastodon_cred.toot_word('Wärmepumpenpflicht', PROTOCOL, metadata, form='Wärmepumpenpflichten',
                                              evidence='Die Wärmepumpenpflichten kommen.')

        self.assertEqual(mastodon_id, 101)
        self.assertEqual(self.word_account.posts[0][0], 'Wärmepumpenpflichten')
        context, evidence, links = self.context_account.posts
        self.assertIn('#Wärmepumpenpflichten tauchte', context[0])
        self.assertIn('Rede von Anna Muster (SPD) gesagt', context[0])
        self.assertIn('Video: https://optv/media/1', context[0])
        self.assertEqual(context[1]['in_reply_to_id'], 101)
        self.assertIn('Die Wärmepumpenpflichten kommen.', evidence[0])
        self.assertEqual(evidence[1]['in_reply_to_id'], 201)
        self.assertIn(PROTOCOL['pdf_url'], links[0])
        self.assertIn(PROTOCOL['wortseite'], links[0])
        self.assertEqual(links[1]['in_reply_to_id'], 202)

    def test_interjection_quotation_and_role_are_named(self):
        interjection = {'speaker': 'B', 'party': 'FDP', 'occasion': 'zwischenruf'}
        quotation = {'speaker': 'Hakan Demir', 'party': 'SPD', 'occasion': 'zitat'}
        government = {'speaker': 'Gerhard Schröder', 'role': 'Bundeskanzler', 'occasion': 'rede'}
        self.assertIn('in einem Zwischenruf von B (FDP).', mastodon_cred.build_context_message('W', PROTOCOL, interjection))
        self.assertIn('in einem Zitat, das Hakan Demir (SPD) vorlas.',
                      mastodon_cred.build_context_message('W', PROTOCOL, quotation))
        self.assertIn('Gerhard Schröder (Bundeskanzler)', mastodon_cred.build_context_message('W', PROTOCOL, government))

    def test_no_video_line_without_a_video(self):
        message = mastodon_cred.build_context_message('W', PROTOCOL, {'link': None, 'speaker': 'B', 'party': 'SPD'})
        self.assertNotIn('Video', message)

    def test_hashtag_keeps_only_word_characters(self):
        self.assertEqual(mastodon_cred.hashtag('Ägäis-Aktivität'), '#ÄgäisAktivität')

    def test_content_warning_for_words_of_the_afd(self):
        mastodon_cred.toot_word('Remigrationsplan', PROTOCOL, {'link': 'x', 'speaker': 'B', 'party': 'AfD'})
        self.assertEqual(self.word_account.posts[0][1]['spoiler_text'], 'Wort von der AfD')

    def test_without_metadata_context_and_links_are_posted(self):
        mastodon_cred.toot_word('Wärmepumpenpflicht', PROTOCOL, False)
        context, links = self.context_account.posts
        self.assertNotIn('gesagt', context[0])
        self.assertIn(PROTOCOL['pdf_url'], links[0])
        self.assertIn(PROTOCOL['wortseite'], links[0])

    def test_posts_are_idempotent(self):
        mastodon_cred.toot_word('Wärmepumpenpflicht', PROTOCOL, False)
        self.assertTrue(self.word_account.posts[0][1]['idempotency_key'])

    def test_word_post_that_keeps_failing_returns_false(self):
        class FailingAccount:
            def status_post(self, text, **options):
                raise ConnectionError('down')
        with mock.patch.object(mastodon_cred, 'MastodonAPI', FailingAccount()):
            self.assertFalse(mastodon_cred.toot_word('Wärmepumpenpflicht', PROTOCOL, False))

if __name__ == '__main__':
    unittest.main()
