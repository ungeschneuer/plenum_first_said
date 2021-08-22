import redis

# Tatsächliche Datenbank für Wörter
r = redis.StrictRedis(host='localhost', port=6379, db=0)

# Datenbank für Meta Stuff wie Sitzungsnummer
twittRedis = redis.StrictRedis(host='localhost', port=6379, db=1)

# Datenbank mit getwitterten tweets
pastRedis = redis.StrictRedis(host='localhost', port=6379, db=2)

#Check Word Database
def check_wdb(word):
    wkey = "word:" + word

    if not r.get(wkey):
        r.set(wkey, '1')
        return True
    else: 
        return False

