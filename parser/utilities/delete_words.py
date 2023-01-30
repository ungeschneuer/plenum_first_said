from database import postRedis, r


# Entfernt neue Wörter aus der Queue und der Datenbank

while postRedis.dbsize() > 0:

    key = postRedis.randomkey().decode('utf-8')

    wkey = "word:" + key

    r.delete(wkey)
    postRedis.delete(key)

