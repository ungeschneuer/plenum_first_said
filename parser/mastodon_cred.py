"""Post a word and its replies on Mastodon.

The word account posts the form said in the protocol, and the context reply uses it as hashtag; the context account replies in a thread: who said it and
where (with the video of Open Parliament TV if there is one), the sentence of the protocol, and the links to the
PDF and the word page. The Mastodon API fails now and then, so each post is tried again a few times.
"""

import hashlib
import logging
import os
import re
from time import sleep

from mastodon import Mastodon

MastodonAPI = Mastodon(access_token=os.environ.get('MASTODON_FIRST_ACCESSTOKEN'), api_base_url='https://mastodon.social')
MastodonKontextAPI = Mastodon(access_token=os.environ.get('MASTODON_KONTEXT_ACCESSTOKEN'),
                              api_base_url='https://mastodon.social')

MAXIMUM_ATTEMPTS = 11
SECONDS_BETWEEN_ATTEMPTS = 60
SECONDS_BEFORE_REPLIES = 5
SPEAKER_SENTENCES = {
    'rede': 'Es wurde im Rahmen der Rede von {} gesagt.',
    'zwischenruf': 'Es fiel in einem Zwischenruf von {}.',
    'zitat': 'Es fiel in einem Zitat, das {} vorlas.',
}


def hashtag(lemma):
    """Mastodon ends a hashtag at a hyphen or other mark, so only letters, digits and underscores remain."""
    return '#' + re.sub(r'\W', '', lemma)


def person(metadata):
    affiliation = ', '.join(part for part in (metadata.get('party'), metadata.get('role')) if part)
    return f"{metadata['speaker']} ({affiliation})" if affiliation else metadata['speaker']


def build_context_message(word, protocol, metadata):
    """Where the word fell first; the speaker sentence is left out if no speaker is known."""
    message = f"{hashtag(word)} tauchte zum ersten Mal im {protocol['titel']} am {protocol['datum']} auf."
    if metadata and metadata.get('speaker'):
        sentence = SPEAKER_SENTENCES.get(metadata.get('occasion'), SPEAKER_SENTENCES['rede'])
        message += ' ' + sentence.format(person(metadata))
    if metadata and metadata.get('link'):
        message += f"\n\nVideo: {metadata['link']}"
    return message


def build_evidence_message(evidence):
    return f'Im Protokoll steht:\n\n{evidence}'


def build_links_message(protocol):
    return (f"Das {protocol['titel']} findet sich als PDF unter {protocol['pdf_url']}\n\n"
            f"Wie oft der Bundestag es seit 1949 gesagt hat: {protocol['wortseite']}")


def idempotency_key(word, kind):
    """One key per word and post: if a post reached the server but the answer got lost, the retry posts nothing."""
    return hashlib.sha256((kind + ':' + word).encode('utf-8')).hexdigest()


def post_with_retries(account, text, **options):
    for _attempt in range(MAXIMUM_ATTEMPTS):
        try:
            return account.status_post(text, **options)
        except Exception as error:
            logging.exception(error)
            sleep(SECONDS_BETWEEN_ATTEMPTS)
    logging.info('Maximale Versuche wurde überschritten.')
    return None


def toot_word(word, protocol, metadata, form=None, evidence=None):
    """Post the word and its replies; returns the id of the word post, or False if it could not be posted."""
    is_afd = bool(metadata) and metadata.get('party') == 'AfD'
    warning = {'spoiler_text': 'Wort von der AfD', 'sensitive': True} if is_afd else {}
    word_status = post_with_retries(MastodonAPI, form or word, idempotency_key=idempotency_key(word, 'word'), **warning)
    if word_status is None:
        return False

    sleep(SECONDS_BEFORE_REPLIES)
    replies = [('context', build_context_message(form or word, protocol, metadata))]
    if evidence:
        replies.append(('evidence', build_evidence_message(evidence)))
    replies.append(('pdf', build_links_message(protocol)))

    reply_to = word_status['id']
    for kind, text in replies:
        status = post_with_retries(MastodonKontextAPI, text, in_reply_to_id=reply_to,
                                   idempotency_key=idempotency_key(word, kind))
        if status is None:
            break
        reply_to = status['id']

    logging.info('Toot wurde erfolgreich gesendet.')
    return word_status['id']
