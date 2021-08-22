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
    pipe.hget("word:" + word, "word")
    pipe.hget("word:" + word.lower(), "word")
    pipe.hget("word:" + word.capitalize(), "word")

    if word.endswith('s') or word.endswith('rn'):
        pipe.hget("word:" + word[:-1], "word")

    if word.endswith('’s') or word.endswith('in') or word.endswith('’n') or word.endswith('es'):
        pipe.hget("word:" + word[:-2], "word")
        

    if all(v is None for v in pipe.execute()):
        r.hset("word:" + word, "word", word)
        r.hset("word:" + word, "id", id)
        return True


    return False

def add_to_queue(word, id):

    twittRedis.hset(word, "word", word)
    twittRedis.hset(word, "id", id)
    return True

