# Plenum First Said


Plenum First Said ist ein Twitterbot, der neue Wörter twittert, die zum ersten Mal während einer Bundestagsdebatte gesagt wurden. Das Projekt ist noch im Aufbau und es wird in keiner Weise  Korrektheit garantiert. 

Das Projekt wurde durch den Twitter-Account [@NYT_first_said](https://twitter.com/NYT_first_said) von Max Bittker inspiriert und dessen [Code](https://github.com/MaxBittker/nyt-first-said) als Startpunkt genutzt, jedoch zum großen Teil verändert. 

## Funktionsweise

Über eine vom Bundestag bereitgestellte [OpenData-API](https://dip.bundestag.de/%C3%BCber-dip/hilfe/api#content) wird täglich nach einem neuen Plenarprotokoll des Bundestags gesucht. Wird es gefunden, wird jedes einzelne Wort mit einer selbsterstellten Datenbank abgeglichen, die aus allen veröffentlichten Plenarprotokollen aufgebaut wurde. Sollte das Wort nicht in der Datenbank gefunden werden, wird dieses zu einer Warteschlange hinzugefügt und zu einem bestimmten Zeitpunkt getwittert und besagter Datenbank selber hinzugefügt. Der Account [@FSBT_Kontext](https://twitter.com/FSBT_Kontext) antwortet automatisiert auf jeden Tweet mit weiterem Kontext zum Wort.

Unregelmäßigkeiten entstehen z.B. durch Silbentrennungen, die nicht gut von Wortverbindungen getrennt werden können (z.B. Know- (neue Zeile) how). 

## Architektur

`plenar.py` ist die Hauptfunktion, die den Rest orchestriert. Sie wird stündlich aufgerufen. `database.py` erlaubt eine Verbindung zur lokalen Redis Datenbank. 

`twitter_queue.py` und `twitter_creds.py` packt neue Wörter in eine Warteliste und twittert diese in unterschiedlichen Zeitintervallen.

`dpi_api.xml` verbindet den Bot mit den Servern des Bundestags und sucht nach neuen Protokollen über weiterlaufende IDs.

`xml_parse.xml` verarbeitet das Protokoll, sodass eine Analyse möglich ist.

`scrape_functions.py` ist für die Worttrennung und Normalisierung da, sowie die Verbindung zum Abgleich mit der Datenbank über `database.py`. 

Im Ordner utilities finden sich Skripte, die bei dem Aufbau der Datenbank geholfen haben. 

Über das Paket [python-dotenv](https://github.com/theskumar/python-dotenv) werden API-Schlüssel durch Umgebungsvariablen bereitgestellt. Dazu muss eine `.env` Datei in der Basis des Projektes existieren. 

Die Webseite [Sentry.io](https://sentry.io) sorgt für schnelle Benachrichtigungen und die Dokumentation von Fehlern. 

## Was bedeutet "neues Wort"?

Aus Gründen der Unterhaltung werden einige Worte aussortiert, die zwar tatsächlich zum ersten Mal so gesagt werden, aber nur bedingt an sich einen Informationswert haben. Folgendes wird z.B. herausgefiltert:
- Plural
- Genitiv
- gegenderte Formen
- Wörter unter 4 Buchstaben
- Gesetzesabkürzungen

## TODOs
- [ ] Sprecherin im Kontext mit erwähnen  
- [ ] Weitere Verfeinerung der Wort-Normalisierung

## Lizenz und Danksagung

Das Projekt steht unter der [GNU General Public License 3](https://www.gnu.org/licenses/gpl-3.0.de.html).  
Das Projekt entsteht im Rahmen eines Nachwuchs-Stipendiums des [Bayerische Staatministeriums für Wissenschaft und Kunst](https://www.stmwk.bayern.de/) zur Förderung der künstlerischen Entfaltung. 



