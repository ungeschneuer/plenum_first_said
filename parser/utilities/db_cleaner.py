from database import twittRedis


total_keys = twittRedis.dbsize()

if total_keys > 400:
    remove = total_keys - 400

    for i in range(0, remove):
        key = twittRedis.randomkey()

        if key == b'meta:tweetstop':
            continue
        print(key)
        word = twittRedis.hget(key, "word").decode("utf-8")
        print('word:' + word)
        twittRedis.delete(word)


