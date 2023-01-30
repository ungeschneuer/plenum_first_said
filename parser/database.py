import redis
import logging


# Tatsächliche Datenbank für Wörter
r = redis.StrictRedis(host='localhost', port=6379, db=0)

# Datenbank für zu twitternde Wörter
postRedis = redis.StrictRedis(host='localhost', port=6379, db=1)

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


# Fügt ein Wort zur Twitter-Datenbank hinzu
def add_to_queue(word, id):

    # Fix für Strichfehler
    if word[0].islower():
        return False

    postRedis.hset(word, 'word', word)
    postRedis.hset(word, 'id', id)
    
    return True

def delete_from_queue(word):
    if postRedis.delete(word):
        return True
    else: 
        return False



