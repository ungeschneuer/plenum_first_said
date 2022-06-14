import redis
from optv_api import get_op_response
import datetime
import logging


# Tatsächliche Datenbank für Wörter
r = redis.StrictRedis(host='localhost', port=6379, db=0)

# Datenbank für zu twitternde Wörter
twittRedis = redis.StrictRedis(host='localhost', port=6379, db=1)

# Datenbank mit getwitterten tweets
pastRedis = redis.StrictRedis(host='localhost', port=6379, db=2)

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

    return pipe.execute()

# Gleicht mit der OpenParliamentTV Datenbank ab
def check_open_parliament(word, id):
    datum = r.hget('protokoll:' + id, 'datum').decode('UTF-8')
    
    # Datum entspricht dem Tag vor dem Protokoll
    date_to_check = datetime.datetime.strptime(datum, '%d.%m.%Y') - datetime.timedelta(days=1)
    date = date_to_check.strftime('%Y-%m-%d')
    url = 'https://de.openparliament.tv/api/v1/search/media/?q=' + word + '&date=' + date
    return get_op_response(url)

def check_existence(word, id):
    # Wenn das Wort direkt existiert, skippen
    if r.hexists('word:' + word, 'word'):
        check_age(word, id)
        return False
    
    # Wenn nicht, dann zur Datenbank hinzufügen und trotzdem checken, ob andere Formen schon existieren.
    else:
        if all(v is None for v in similiar_word(word)):
            add_to_database(word, id)
            return check_open_parliament(word, id)
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
        return False

#Sorgt dafür, dass tatsächlich das älteste Wort in der Datenbank steht
def check_age(word,id):

    # Quelle des Wortes welches aktuell in der Datenbank ist
    aktuelle_id = r.hget('word:' + word, 'id').decode("utf-8")

    if id == aktuelle_id:
        return False

    else:

        aktuell_p = r.hgetall('protokoll:' + aktuelle_id)

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


# Fügt ein Wort zur Twitter-Datenbank hinzu
def add_to_queue(word, id):

    # Fix für Strichfehler
    if word[0].islower():
        return False

    twittRedis.hset(word, 'word', word)
    twittRedis.hset(word, 'id', id)
    
    return True



