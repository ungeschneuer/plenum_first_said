from database import postRedis


total_keys = postRedis.dbsize()

if total_keys > 400:
    remove = total_keys - 400

    for i in range(0, remove):
        key = postRedis.randomkey()

        if key == b'meta:tweetstop':
            continue
        word = postRedis.hget(key, "word").decode("utf-8")
        postRedis.delete(word)


