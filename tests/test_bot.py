import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'parser'))

import bot  # noqa: E402

PROTOCOL = {'nummer': '21/108', 'datum': '2026-11-12', 'pdf': 'https://example.org/21108.pdf'}


def new_word(lemma: str, speaker: dict | None = None) -> dict:
    return {'lemma': lemma, 'formen': [lemma], 'protokoll': PROTOCOL, 'anzahl': 1, 'erste': speaker}


class BotTest(unittest.TestCase):
    def test_filters_of_the_earlier_bot(self):
        self.assertTrue(bot.is_postable('Deutschlandticket'))
        self.assertFalse(bot.is_postable('Zug'))
        self.assertFalse(bot.is_postable('BürgerInnen'))
        self.assertFalse(bot.is_postable('wahl-kampf'))
        self.assertFalse(bot.is_postable('Covid19'))

    def test_close_variants_are_posted_once(self):
        self.assertEqual(bot.without_similar_words(['Doppelwumms', 'Doppelwums', 'Zeitenwende']),
                         ['Doppelwumms', 'Zeitenwende'])

    def test_first_run_only_records_candidates(self):
        state = {'words': {}}
        bot.queue_new_words(state, [new_word('Deutschlandticket')], post=False)
        self.assertEqual(state['words']['Deutschlandticket']['status'], 'ausgelassen')

    def test_known_words_are_not_queued_again(self):
        state = {'words': {'Deutschlandticket': {'status': 'gepostet'}}}
        bot.queue_new_words(state, [new_word('Deutschlandticket'), new_word('Wärmepumpenpflicht')], post=True)
        self.assertEqual(state['words']['Deutschlandticket']['status'], 'gepostet')
        self.assertEqual(state['words']['Wärmepumpenpflicht']['status'], 'wartet')

    def test_protocol_details_for_the_replies(self):
        details = bot.protocol_details(new_word('Wärmepumpe'))
        self.assertEqual(details['titel'], 'Protokoll der 108. Sitzung des 21. Deutschen Bundestages')
        self.assertEqual(details['datum'], '12.11.2026')
        self.assertTrue(details['wortseite'].endswith('/wort/W%C3%A4rmepumpe'))

    def test_speaker_from_the_site_when_optv_has_none(self):
        entry = {'protokoll': bot.protocol_details(new_word('Wärmepumpe')),
                 'erste': {'name': 'Anna Muster', 'fraktion': 'SPD'}}
        metadata = bot.speaker_metadata(entry, {'link': 'https://optv', 'speaker': None, 'party': None})
        self.assertEqual((metadata['speaker'], metadata['party'], metadata['link']), ('Anna Muster', 'SPD', 'https://optv'))


if __name__ == '__main__':
    unittest.main()
