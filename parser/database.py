import redis

# Tatsächliche Datenbank für Wörter
r = redis.StrictRedis(host='localhost', port=6379, db=0)

# Datenbank für Meta Stuff wie Sitzungsnummer
twittRedis = redis.StrictRedis(host='localhost', port=6379, db=1)

# Datenbank mit getwitterten tweets
pastRedis = redis.StrictRedis(host='localhost', port=6379, db=2)

# Wort abgleichen und zur Datenbank hinzufügen
def compare_words(word):
    
    # Wenn genau das Wort existiert, skippen
    if r.hget('word:' + word, 'word'):
        return [word]
    
    # Sonst Abfrage von verschiedenen Versionen
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

    # Exisitiert schon ein anderer Fall oder ein Singular?
    if word.endswith(('s','n', 'e')):
        pipe.hget('word:' + word[:-1], 'word')
    
    if word.endswith(('’s', 'in', '’n', 'er', 'en', 'es')):
        pipe.hget('word:' + word[:-2], 'word')

    return pipe.execute()




def add_word(word, id):
    
    if all(v is None for v in compare_words(word)):
        r.hset('word:' + word, 'word', word)
        r.hset('word:' + word, 'id', id)
        return True

    return False

def add_to_queue(word, id):

    twittRedis.hset(word, 'word', word)
    twittRedis.hset(word, 'id', id)
    
    return True

