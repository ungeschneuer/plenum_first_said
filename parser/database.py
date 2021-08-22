import redis

# Tatsächliche Datenbank für Wörter
r = redis.StrictRedis(host='localhost', port=6379, db=0)

# Datenbank für Meta Stuff wie Sitzungsnummer
twittRedis = redis.StrictRedis(host='localhost', port=6379, db=1)

# Datenbank mit getwitterten tweets
pastRedis = redis.StrictRedis(host='localhost', port=6379, db=2)

# Wort abgleichen und zur Datenbank hinzufügen
def add_word(word, id):
    pipe = r.pipeline()
    
    # Checken ob Kleinschreibung, Großschreibung oder Plural schon existieren
    pipe.type("word:" + word)
    pipe.type("word:" + word.lower())
    pipe.type("word:" + word.capitalize())

    if word.endswith('s'):
        pipe.type("word:" + word[:-1])

    if word.endswith('’s') or word.endswith('in'):
        pipe.type("word:" + word[:-2])

    result = pipe.execute()

    if all(x == b'none' for x in result):
        r.hset("word:" + word, "word", word)
        r.hset("word:" + word, "id", id)
        print(word)
        return True


    return False

def add_to_queue(word, id):

    twittRedis.hset(word, "word", word)
    twittRedis.hset(word, "id", id)
    return True

