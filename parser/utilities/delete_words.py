from database import twittRedis, r


# Entfernt neue Wörter aus der Queue und der Datenbank

while twittRedis.dbsize() > 0:

    key = twittRedis.randomkey().decode('utf-8')

    wkey = "word:" + key

    r.delete(wkey)
    twittRedis.delete(key)

