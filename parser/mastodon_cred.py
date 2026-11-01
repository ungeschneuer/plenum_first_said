# -*- coding: utf-8 -*-
#!/usr/bin/python


import logging
from dotenv import load_dotenv
import os
from mastodon import Mastodon
import mastodon
from time import sleep
import hashlib

load_dotenv()


MastodonAPI = Mastodon(access_token = os.environ.get('MASTODON_FIRST_ACCESSTOKEN'),  api_base_url="https://mastodon.social")
MastodonKontextAPI = Mastodon(access_token = os.environ.get('MASTODON_KONTEXT_ACCESSTOKEN'),  api_base_url="https://mastodon.social")


# Erstellt den Kontext-Text basierend auf den verfügbaren Metadaten.
# Wenn Redner:in nicht vorhanden ist (z.B. nur Präsident:in/Vizepräsident:in im Datensatz),
# wird der "wurde gesagt von" Teil weggelassen.
def build_context_message(word, keys, metadata):
    titel = keys[b'titel'].decode('UTF-8')
    datum = keys[b'datum'].decode('UTF-8')
    link = metadata['link']
    
    if metadata.get('speaker') and metadata.get('party'):
        # Vollständige Nachricht mit Redner:in und Partei
        return "#{} tauchte zum ersten Mal im {} am {} auf. Es wurde im Rahmen der Rede von {} ({}) gesagt.\n\nVideo: {}".format(
            word, titel, datum, metadata['speaker'], metadata['party'], link)
    elif metadata.get('speaker'):
        # Redner:in vorhanden, aber keine Partei
        return "#{} tauchte zum ersten Mal im {} am {} auf. Es wurde im Rahmen der Rede von {} gesagt.\n\nVideo: {}".format(
            word, titel, datum, metadata['speaker'], link)
    else:
        # Redner:in nicht gefunden - vereinfachte Nachricht ohne "wurde gesagt von"
        return "#{} tauchte zum ersten Mal im {} am {} auf.\n\nVideo: {}".format(
            word, titel, datum, link)


# Idempotency-Key pro Wort und Post-Art: Wenn ein Request beim Server ankommt,
# die Antwort aber verloren geht (z.B. Timeout), erzeugt der Retry keinen zweiten Post.
def idempotency_key(word, kind):
    return hashlib.sha256((kind + ':' + word).encode('utf-8')).hexdigest()


# Mastodon API is a bit wobbly so a fix with while loops 
def toot_word(word, keys, metadata):

    # Max tries to get posting trough
    patience = 0
    
    #Posts Word
    is_afd = metadata and metadata.get('party') == 'AfD'
    while True:
        if patience > 10:
            logging.info('Maximale Versuche wurde überschritten.')
            return False
        else:
            try:
                if is_afd:
                    toot_status = MastodonAPI.status_post(word, spoiler_text='Wort von der AfD', sensitive=True,
                                                         idempotency_key=idempotency_key(word, 'word'))
                else:
                    toot_status = MastodonAPI.status_post(word, idempotency_key=idempotency_key(word, 'word'))
            except Exception as e:
                logging.exception(e)
                sleep(60)
                patience += 1
                continue
            break

    sleep(5)

    # Posts Context
    # Metada is information from OPTV
    if metadata:
        # Max tries reset
        patience = 0
        
        # Erstelle Kontext-Nachricht (mit oder ohne Redner:in)
        try:
            context_message = build_context_message(word, keys, metadata)
        except Exception as e:
            logging.exception(e)
            return toot_status["id"]

        while True:
            if patience > 10:
                logging.info('Maximale Versuche wurde überschritten.')
                return toot_status["id"]
            else:
                try:
                    context_status = MastodonKontextAPI.status_post(
                        context_message,
                        in_reply_to_id=toot_status["id"],
                        idempotency_key=idempotency_key(word, 'context'))
                except mastodon.MastodonNotFoundError as m:
                    logging.exception(m)
                    sleep(60)
                    patience += 1 
                    continue
                except Exception as e:
                    logging.exception(e)
                    sleep(60)
                    patience += 1
                    continue
                except:
                    logging.exception("Unbekannter Fehler")
                    sleep(60)
                    patience += 1
                    continue
                break

        # Max tries reset
        patience = 0

        while True:

            if patience > 10:
                logging.info('Maximale Versuche wurde überschritten.')
                return toot_status["id"]
            else:
                try:
                    second_context_status = MastodonKontextAPI.status_post(
                        "Das {} findet sich als PDF unter {}".format(
                            keys[b'titel'].decode('UTF-8'),
                            keys[b'pdf_url'].decode('UTF-8')),
                        in_reply_to_id=context_status["id"],
                        idempotency_key=idempotency_key(word, 'pdf'))
                except mastodon.MastodonNotFoundError as m:
                    logging.exception(m)
                    sleep(60)
                    patience += 1
                    continue
                except AttributeError as e:
                    logging.exception(e)
                    sleep(60)
                    patience += 1
                    continue
                except Exception as e:
                    logging.exception(e)
                    sleep(60)
                    patience += 1
                    continue
                except:
                    logging.exception("Unbekannter Fehler")
                    sleep(60)
                    patience += 1
                    continue
                break



    else:
        # Max tries reset
        patience = 0
        while True:

            if patience > 10:
                logging.info('Maximale Versuche wurde überschritten.')
                return toot_status["id"]
            else:
                try:     
                    context_status = MastodonKontextAPI.status_post("#{} tauchte zum ersten Mal im {} am {} auf. Das Protokoll findet sich unter {}".format(
                        word,
                        keys[b'titel'].decode('UTF-8'),
                        keys[b'datum'].decode('UTF-8'),
                        keys[b'pdf_url'].decode('UTF-8')),
                        in_reply_to_id = toot_status["id"],
                        idempotency_key=idempotency_key(word, 'context'))
                except mastodon.MastodonNotFoundError as m:
                    logging.exception("Unbekannter Fehler")
                    sleep(60)
                    patience += 1 
                    continue
                except Exception as e:
                    logging.exception(e)
                    sleep(60)
                    patience += 1
                    continue
                except:
                    logging.exception("Unbekannter Fehler")
                    sleep(60)
                    patience += 1
                    continue
                break


    logging.info('Toot wurde erfolgreich gesendet.')
    return toot_status["id"]
