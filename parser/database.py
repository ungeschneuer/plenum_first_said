import datetime
import logging
import os

import redis
from dotenv import load_dotenv

load_dotenv()


def _redis_port():
    port = os.getenv('REDIS_PORT', '6379')
    try:
        return int(port)
    except ValueError:
        logging.warning("Ungültiger REDIS_PORT '%s'. Fallback auf 6379.", port)
        return 6379


def _redis_client(db):
    redis_url = os.getenv('REDIS_URL', '').strip()
    redis_socket = os.getenv('REDIS_SOCKET', '').strip()
    redis_host = os.getenv('REDIS_HOST', 'localhost').strip()
    redis_password = os.getenv('REDIS_PASSWORD', '').strip() or None

    if redis_url:
        return redis.Redis.from_url(redis_url, db=db)

    if redis_socket:
        return redis.Redis(
            unix_socket_path=redis_socket,
            db=db,
            password=redis_password,
        )

    return redis.Redis(
        host=redis_host,
        port=_redis_port(),
        db=db,
        password=redis_password,
    )


# Tatsächliche Datenbank für Wörter
r = _redis_client(0)

# Datenbank für zu postende Wörter
postRedis = _redis_client(1)

# Datenbank mit geposteten tweets
pastRedis = _redis_client(2)


def _int_env(name, default):
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        logging.warning("Ungültiger Wert für %s. Fallback auf %s.", name, default)
        return default


# Wörter aus Protokollen, die älter sind, werden nicht mehr gepostet.
MAX_WORD_AGE_DAYS = _int_env('MAX_WORD_AGE_DAYS', 30)

# Maximale Anzahl an Wörtern in der Queue.
MAX_QUEUE_SIZE = _int_env('MAX_QUEUE_SIZE', 400)

# Wort abgleichen und zur Datenbank hinzufügen
def similiar_word(word):

    # Sonst Abfrage von verschiedenen Versionen und das tatsächliche Wort in die Datenbank einfügen
    pipe = r.pipeline()

    # Checken ob Kleinschreibung/Großschreibung
    pipe.hget('word:' + word.lower(), 'word')
    pipe.hget('word:' + word.capitalize(), 'word')


    # Existiert es schon im Plural oder ein einem anderen Fall?
    pipe.hget('word:' + word + 'er', 'word')
    pipe.hget('word:' + word + 'n', 'word')
    pipe.hget('word:' + word + 'en', 'word')
    pipe.hget('word:' + word + 's', 'word')
    pipe.hget('word:' + word + 'es', 'word')
    pipe.hget('word:' + word + 'e', 'word')


    # Existiert schon ein anderer Fall oder ein Singular?
    if word.endswith(('s','n', 'e')):
        pipe.hget('word:' + word[:-1], 'word')
    
    if word.endswith(('’s', 'in', '’n', 'er', 'en', 'es', 'se')):
        pipe.hget('word:' + word[:-2], 'word')

    if word.endswith(('ern')):
        pipe.hget('word:' + word[:-3], 'word')
    
    if word.endswith(('m')):
        pipe.hget('word:' + word[:-1] + 'n', 'word')

    if word.endswith(('n')):
        pipe.hget('word:' + word[:-1] + 'm', 'word')

    if word.endswith(('en')):
        pipe.hget('word:' + word[:-2] + 'er', 'word')
        pipe.hget('word:' + word[:-2] + 'e', 'word')
        pipe.hget('word:' + word[:-2] + 't', 'word')
    
    # Glücklicherweise wird das Gendern Standard. Darum wird es nicht mehr in die Queue eingefügt.
    if word.endswith(('innen')):
        pipe.hget('word:' + word[:-5], 'word')

    return pipe.execute()

# Überprüft, ob das Wort schon in der Datenbank ist und ob die älteste Version notiert ist. 
def check_newness(word, id):
    # Wenn das Wort direkt existiert, skippen
    if r.hexists('word:' + word, 'word'):
        check_age(word, id)
        return False
    
    # Wenn nicht, dann zur Datenbank hinzufügen und trotzdem checken, ob andere Formen schon existieren.
    else:
        if all(v is None for v in similiar_word(word)):
            add_to_database(word, id)
            return True
        else:
            add_to_database (word, id)
            return False

# Helferfunktion, um Wort zum Korpus hinzuzufügen
def add_to_database (word, id):
    try:
        r.hset('word:' + word, 'word', word)
        r.hset('word:' + word, 'id', id)
        return True
    except Exception as e:
        logging.exception(e)
        raise

#Sorgt dafür, dass tatsächlich das älteste Wort in der Datenbank steht
def check_age(word,id):

    # Quelle des Wortes welches aktuell in der Datenbank ist
    aktuelle_id = r.hget('word:' + word, 'id').decode("utf-8")

    if id == aktuelle_id:
        return False

    else:

        try: 
            aktuell_p = r.hgetall('protokoll:' + str(aktuelle_id))
            aktuelle_periode = int(aktuell_p[b'wahlperiode'].decode("utf-8"))
            aktuelle_protokollnummer = int(aktuell_p[b'protokollnummer'].decode("utf-8"))


            # Quelle des Wortes, welches sich doppelt 
            neu_p = r.hgetall('protokoll:' + str(id))
            neue_periode = int(neu_p[b'wahlperiode'].decode("utf-8"))
            neue_protokollnummer = int(neu_p[b'protokollnummer'].decode("utf-8"))


            if (aktuelle_periode == neue_periode and aktuelle_protokollnummer > neue_protokollnummer) or (aktuelle_periode > neue_periode):
                r.hset('word:' + word, 'id', id)
                return True
            else:
                return False
        except Exception as e:
            logging.exception(e)
            raise


# Fügt ein Wort zur Posting-Datenbank hinzu
def add_to_queue(word, id):

    # Fix für Strichfehler
    if word[0].islower():
        return False

    # Bereits gepostete Wörter nie wieder in die Queue
    if already_posted(word):
        logging.info("Wort '%s' wurde bereits gepostet und wird nicht erneut eingereiht.", word)
        return False

    postRedis.hset(word, 'word', word)
    postRedis.hset(word, 'id', id)
    
    return True

def delete_from_queue(word):
    if postRedis.delete(word):
        return True
    else: 
        return False


# Ist das Wort schon im Archiv der geposteten Wörter?
def already_posted(word):
    return pastRedis.exists(word) > 0


# Alle Wörter in der Queue (ohne Meta-Keys)
def queued_words():
    for key in postRedis.scan_iter():
        if key.startswith(b'meta:'):
            continue
        yield key.decode('utf-8')


# Zufälliges Wort aus der Queue oder None, wenn sie leer ist
def random_queued_word():
    for _ in range(10):
        key = postRedis.randomkey()
        if key is None:
            return None
        if not key.startswith(b'meta:'):
            return key.decode('utf-8')
    return next(queued_words(), None)


# Alter des Protokolls in Tagen, None wenn unbekannt
def protokoll_age_days(id):
    if id is None:
        return None
    if isinstance(id, bytes):
        id = id.decode('utf-8')
    datum = r.hget('protokoll:' + str(id), 'datum')
    if not datum:
        return None
    try:
        date = datetime.datetime.strptime(datum.decode('utf-8'), '%d.%m.%Y').date()
    except ValueError:
        return None
    return (datetime.date.today() - date).days


def is_too_old(id):
    age = protokoll_age_days(id)
    return age is not None and age > MAX_WORD_AGE_DAYS
