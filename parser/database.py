import redis

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

    # Existiert schon ein anderer Fall oder ein Singular?
    if word.endswith(('s','n', 'e')):
        pipe.hget('word:' + word[:-1], 'word')
    
    if word.endswith(('’s', 'in', '’n', 'er', 'en', 'es')):
        pipe.hget('word:' + word[:-2], 'word')

    return pipe.execute()




def add_word(word, id):
    # Wenn das Wort direkt existiert, skippen
    if r.hget('word:' + word, 'word'):
        check_age(word, id)
        return False
    
    # Wenn nicht, dann zur Datenbank hinzufügen und trotzdem checken, ob andere Formen schon existieren.
    else:
        if all(v is None for v in similiar_word(word)):
            r.hset('word:' + word, 'word', word)
            r.hset('word:' + word, 'id', id)
            return True
        else:
            r.hset('word:' + word, 'word', word)
            r.hset('word:' + word, 'id', id)
            return False

#Sorgt dafür, dass tatsächlich das älteste Wort in der Datenbank steht
def check_age(word,id):

    # Quelle des Wortes welches aktuell in der Datenbank ist
    aktuelle_id = r.hget('word:' + word, 'id')  
    aktuelle_periode = r.hget('protokoll:' + aktuelle_id, 'wahlperiode')
    aktuelles_protokollnummer = r.hget('protokoll:' + aktuelle_id, 'protokollnummer')

    # Quelle des Wortes, welches sich doppelt 
    neue_periode = r.hget('protokoll:' + id, 'wahlperiode')
    neue_protokollnummer = r.hget('protokoll:' + id, 'protokollnummer')

    if (aktuelle_periode >= neue_periode) and (aktuelles_protokollnummer > neue_protokollnummer):
        r.hset('word:' + word, 'word', word)
        r.hset('word:' + word, 'id', id)
        return True
    else:
        return False



def add_to_queue(word, id):

    twittRedis.hset(word, 'word', word)
    twittRedis.hset(word, 'id', id)
    
    return True

