"""Post words said for the first time in the Bundestag.

Runs every hour in GitHub Actions. The Bundestag Wortschatz site publishes the lemmas first said in recent
protocols (neue-woerter.json). New candidates join the queue in state/bot.json; at most one word is posted per run,
and the next post waits a random 55 to 120 minutes, as before. The state file is committed by the workflow.

Before posting, Open Parliament TV is asked whether the word was said before the protocol date; it also supplies
the video link and speaker for the context reply. Without OPTV data, the speaker comes from the site.

The first run only records the current candidates without posting, so that words posted by the earlier bot on
the server are not posted again.
"""

import datetime
import difflib
import json
import logging
import os
import random
import re
import urllib.parse
import urllib.request
from pathlib import Path

SITE_URL = 'https://ungeschneuer.github.io/plenum_first_said_website'
NEW_WORDS_URL = f'{SITE_URL}/data/neue-woerter.json'
STATE_FILE = Path(__file__).resolve().parent.parent / 'state' / 'bot.json'
MAX_WORD_AGE_DAYS = int(os.getenv('MAX_WORD_AGE_DAYS', '30'))
MINIMUM_WORD_LENGTH = 5
MINUTES_BETWEEN_POSTS = (55, 120)
SIMILAR_WORDS_PER_GROUP = 4
LOWERCASE_COMPOUND = re.compile(r'[a-zäöüß]+[-–][a-zäöüß]+')


def now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def load_state() -> dict | None:
    return json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else None


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=1, sort_keys=True) + '\n')


def fetch_new_words() -> list[dict]:
    with urllib.request.urlopen(NEW_WORDS_URL, timeout=60) as response:
        return json.load(response)


def is_postable(lemma: str) -> bool:
    """The filters of the earlier bot: no short words, numbers, glued words or line-break compounds."""
    return (len(lemma) >= MINIMUM_WORD_LENGTH and not any(character.isdigit() for character in lemma)
            and not any(character.isupper() for character in lemma[1:])
            and not LOWERCASE_COMPOUND.search(lemma))


def without_similar_words(lemmas: list[str]) -> list[str]:
    """Of words that are close variants of each other (spelling errors, compounds), keep the first."""
    kept: list[str] = []
    for lemma in lemmas:
        if not difflib.get_close_matches(lemma, kept, n=SIMILAR_WORDS_PER_GROUP):
            kept.append(lemma)
    return kept


def protocol_details(word: dict) -> dict:
    protocol = word['protokoll']
    wahlperiode, session = protocol['nummer'].split('/')
    session_date = datetime.date.fromisoformat(protocol['datum'])
    return {
        'titel': f'Protokoll der {int(session)}. Sitzung des {int(wahlperiode)}. Deutschen Bundestages',
        'datum': session_date.strftime('%d.%m.%Y'),
        'iso_datum': protocol['datum'],
        'pdf_url': protocol['pdf'],
        'wortseite': f"{SITE_URL}/wort/{urllib.parse.quote(word['lemma'])}",
    }


def queue_new_words(state: dict, new_words: list[dict], post: bool) -> None:
    known = state['words']
    candidates = [word for word in new_words if word['lemma'] not in known]
    postable = set(without_similar_words([word['lemma'] for word in candidates if is_postable(word['lemma'])]))
    for word in candidates:
        status = 'wartet' if post and word['lemma'] in postable else 'ausgelassen'
        known[word['lemma']] = {'status': status, 'protokoll': protocol_details(word), 'erste': word.get('erste')}
    logging.info('%d neue Kandidaten, davon %d in der Warteschlange', len(candidates),
                 sum(1 for word in candidates if known[word['lemma']]['status'] == 'wartet'))


def is_too_old(entry: dict) -> bool:
    session_date = datetime.date.fromisoformat(entry['protokoll']['iso_datum'])
    return (now().date() - session_date).days > MAX_WORD_AGE_DAYS


def speaker_metadata(entry: dict, optv_metadata: dict | bool) -> dict | bool:
    if optv_metadata and optv_metadata.get('speaker'):
        return optv_metadata
    first_speaker = entry.get('erste')
    if not first_speaker:
        return optv_metadata
    metadata = dict(optv_metadata) if optv_metadata else {'link': entry['protokoll']['wortseite']}
    metadata['speaker'] = first_speaker['name']
    metadata['party'] = first_speaker.get('fraktion')
    return metadata


def post_one_word(state: dict) -> None:
    from mastodon_cred import toot_word
    from optv_api import check_for_infos, double_check_newness

    queued = [lemma for lemma, entry in state['words'].items() if entry['status'] == 'wartet']
    for lemma in queued:
        if is_too_old(state['words'][lemma]):
            state['words'][lemma]['status'] = 'zu alt'
    queued = [lemma for lemma in queued if state['words'][lemma]['status'] == 'wartet']
    if not queued:
        logging.info('Keine Wörter in der Warteschlange.')
        return

    lemma = random.choice(queued)
    entry = state['words'][lemma]
    protocol = entry['protokoll']
    if not double_check_newness(lemma, protocol):
        entry['status'] = 'bei OPTV schon früher'
        logging.info('„%s“ wurde bei OPTV vor dem Protokolldatum gefunden.', lemma)
        return

    mastodon_id = toot_word(lemma, protocol, speaker_metadata(entry, check_for_infos(lemma, protocol)))
    if not mastodon_id:
        logging.info('„%s“ konnte nicht gepostet werden und bleibt in der Warteschlange.', lemma)
        return
    entry.update({'status': 'gepostet', 'mastodon_id': str(mastodon_id), 'gepostet_am': now().isoformat()})
    pause = random.randrange(*MINUTES_BETWEEN_POSTS)
    state['naechster_post_ab'] = (now() + datetime.timedelta(minutes=pause)).isoformat()
    logging.info('„%s“ gepostet, nächster Post frühestens in %d Minuten.', lemma, pause)


def main() -> None:
    logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO)
    state = load_state()
    first_run = state is None
    state = state or {'words': {}, 'naechster_post_ab': now().isoformat()}

    queue_new_words(state, fetch_new_words(), post=not first_run)
    can_post = os.getenv('MASTODON_FIRST_ACCESSTOKEN') and os.getenv('MASTODON_KONTEXT_ACCESSTOKEN')
    if first_run:
        logging.info('Erster Lauf: vorhandene Kandidaten wurden nur vermerkt, nicht gepostet.')
    elif not can_post:
        logging.warning('Mastodon-Tokens fehlen, es wird nicht gepostet.')
    elif now() >= datetime.datetime.fromisoformat(state['naechster_post_ab']):
        post_one_word(state)
    else:
        logging.info('Nächster Post erst ab %s.', state['naechster_post_ab'])
    save_state(state)


if __name__ == '__main__':
    main()
