# -*- coding: utf-8 -*-
#!/usr/bin/python


import logging
from dotenv import load_dotenv
import os
from mastodon import Mastodon
import mastodon
from time import sleep

load_dotenv()


MastodonAPI = Mastodon(access_token = os.environ.get('MASTODON_FIRST_ACCESSTOKEN'),  api_base_url="https://mastodon.social")
MastodonKontextAPI = Mastodon(access_token = os.environ.get('MASTODON_KONTEXT_ACCESSTOKEN'),  api_base_url="https://mastodon.social")


# Mastodon API is a bit wobbly so a fix with while loops 
def toot_word(word, keys, metadata):

    # Max tries to get posting trough
    patience = 0
    
    #Posts Word
    while True:
        try: 
            toot_status = MastodonAPI.toot(word)

        except Exception as e:
            logging.exception(e)
            sleep(120)
            patience += 1
            continue
        if patience > 50:
            logging.info('Maximale Versuche wurde überschritten.')
            return False
        else:
            break

    
    # Posts Context
    # Metada is information from OPTV
    if metadata:
        while True:
            try:
                context_status = MastodonKontextAPI.status_post("#{} tauchte zum ersten Mal im {} am {} auf. Es wurde von {} ({}) gesagt.\n\nVideo: {}".format(
                        word,
                        keys[b'titel'].decode('UTF-8'),
                        keys[b'datum'].decode('UTF-8'),
                        metadata['speaker'],
                        metadata['party'],
                        metadata['link']),
                        in_reply_to_id = toot_status["id"])
            except mastodon.MastodonNotFoundError as m:
                logging.exception(m)
                sleep(120)
                patience += 1 
                continue
            except Exception as e:
                logging.exception(e)
                sleep(120)
                patience += 1
                continue
            except:
                logging.exception("Unbekannter Fehler")
                sleep(120)
                patience += 1
                continue
            if patience > 50:
                logging.info('Maximale Versuche wurde überschritten.')
                return False
            else:
                break



        while True:
            try:
                second_context_status = MastodonKontextAPI.status_post(
                    "Das {} findet sich als PDF unter {}".format(
                        context_status.user.screen_name,
                        keys[b'titel'].decode('UTF-8'),
                        keys[b'pdf_url'].decode('UTF-8')),
                    in_reply_to_status_id=context_status.id)
            except mastodon.MastodonNotFoundError as m:
                logging.exception(m)
                sleep(120)
                patience += 1
                continue
            except AttributeError as e:
                logging.exception(e)
                sleep(120)
                patience += 1
                continue

            except Exception as e:
                logging.exception(e)
                sleep(120)
                patience += 1
                continue
            except:
                logging.exception("Unbekannter Fehler")
                sleep(120)
                patience += 1
                continue
            if patience > 50:
                logging.info('Maximale Versuche wurde überschritten.')
                return False
            else:
                break



    else:
        while True:
            try:     
                context_status = MastodonKontextAPI.status_post("#{} tauchte zum ersten Mal im {} am {} auf. Das Protokoll findet sich unter {}".format(
                    word,
                    keys[b'titel'].decode('UTF-8'),
                    keys[b'datum'].decode('UTF-8'),
                    keys[b'pdf_url'].decode('UTF-8')),
                    in_reply_to_id = toot_status["id"])
            except mastodon.MastodonNotFoundError as m:
                logging.exception("Unbekannter Fehler")
                sleep(120)
                patience += 1 
                continue
            except Exception as e:
                logging.exception(e)
                sleep(120)
                patience += 1
                continue
            except:
                logging.exception("Unbekannter Fehler")
                sleep(120)
                patience += 1
                continue
            if patience > 50:
                logging.info('Maximale Versuche wurde überschritten.')
                return False
            else:
                break


    logging.info('Toot wurde erfolgreich gesendet.')
    return toot_status["id"]


