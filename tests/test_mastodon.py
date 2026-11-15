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

    def test_word_with_context_and_pdf_reply(self):
        metadata = {'link': 'https://optv/media/1', 'speaker': 'Anna Muster', 'party': 'SPD'}
        mastodon_id = mastodon_cred.toot_word('Wärmepumpenpflicht', PROTOCOL, metadata)

        self.assertEqual(mastodon_id, 101)
        self.assertEqual(self.word_account.posts[0][0], 'Wärmepumpenpflicht')
        context, pdf = self.context_account.posts
        self.assertIn('Anna Muster (SPD)', context[0])
        self.assertIn('https://optv/media/1', context[0])
        self.assertEqual(context[1]['in_reply_to_id'], 101)
        self.assertIn(PROTOCOL['pdf_url'], pdf[0])
        self.assertIn(PROTOCOL['wortseite'], pdf[0])
        self.assertEqual(pdf[1]['in_reply_to_id'], 201)

    def test_content_warning_for_words_of_the_afd(self):
        mastodon_cred.toot_word('Remigrationsplan', PROTOCOL, {'link': 'x', 'speaker': 'B', 'party': 'AfD'})
        self.assertEqual(self.word_account.posts[0][1]['spoiler_text'], 'Wort von der AfD')

    def test_without_metadata_a_single_reply_links_protocol_and_word_page(self):
        mastodon_cred.toot_word('Wärmepumpenpflicht', PROTOCOL, False)
        (reply,) = self.context_account.posts
        self.assertIn(PROTOCOL['pdf_url'], reply[0])
        self.assertIn(PROTOCOL['wortseite'], reply[0])

    def test_posts_are_idempotent(self):
        mastodon_cred.toot_word('Wärmepumpenpflicht', PROTOCOL, False)
        self.assertTrue(self.word_account.posts[0][1]['idempotency_key'])


if __name__ == '__main__':
    unittest.main()
