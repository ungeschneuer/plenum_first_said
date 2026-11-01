import logging
from database import (postRedis, queued_words, already_posted, protokoll_age_days,
                      delete_from_queue, MAX_WORD_AGE_DAYS, MAX_QUEUE_SIZE)


# Räumt die Queue auf:
# 1. Wörter, die schon gepostet wurden, werden entfernt (verhindert Doppelposts).
# 2. Wörter aus Protokollen älter als MAX_WORD_AGE_DAYS werden entfernt.
# 3. Ist die Queue danach noch zu groß, werden die ältesten Wörter entfernt.
def clean_queue():
    remaining = []
    removed_posted = removed_old = removed_overflow = 0

    for word in list(queued_words()):
        if already_posted(word):
            delete_from_queue(word)
            removed_posted += 1
            continue

        age = protokoll_age_days(postRedis.hget(word, 'id'))
        if age is not None and age > MAX_WORD_AGE_DAYS:
            delete_from_queue(word)
            removed_old += 1
            continue

        remaining.append((age, word))

    overflow = len(remaining) - MAX_QUEUE_SIZE
    if overflow > 0:
        # Unbekanntes Alter zuerst entfernen, danach die ältesten
        remaining.sort(key=lambda entry: float('inf') if entry[0] is None else entry[0], reverse=True)
        for _, word in remaining[:overflow]:
            delete_from_queue(word)
            removed_overflow += 1

    logging.info('Queue bereinigt: %d bereits gepostet, %d älter als %d Tage, %d wegen Überlauf entfernt.',
                 removed_posted, removed_old, MAX_WORD_AGE_DAYS, removed_overflow)

    return removed_posted + removed_old + removed_overflow


if __name__ == "__main__":
    import os
    log_file = os.path.join(os.path.dirname(__file__), 'post.log')
    logging.basicConfig(
        filename=log_file,
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')
    clean_queue()
