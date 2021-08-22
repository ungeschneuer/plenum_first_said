# Plenum First Said


Plenum First Said ist ein Twitterbot, der neue Wörter twittert, die zum ersten Mal während einer Bundestagsdebatte gesagt wurden. Das Projekt ist noch im Aufbau und es wird in keiner Weise eine Korrektheit garantiert. 

Das Projekt wurde durch den Twitter-Account [@NYT_first_said](https://twitter.com/NYT_first_said) von Max Bittker inspiriert und dessen [Code](https://github.com/MaxBittker/nyt-first-said) als Startpunkt genutzt, jedoch zum großen Teil verändert. 

Das Projekt ensteht im Rahmen des Stipendiums von [Bayern-Innovativ](https://www.bayern-innovativ.de/) zur Förderung von Künstlern (ich). 

## Funktionsweise

Die Webseite des Bundestags wird täglich nach einem neuen Plenarprotokoll abgesucht. Wird es gefunden, wird jedes einzelne Wort mit einer Datenbank abgeglichen. Sollte es nicht in der Datenbank gefunden werden, wird dieses zu einer Warteschlange hinzugefügt und zu einem bestimmten Zeitpunkt getwittert, als auch besagter Datenbank hinzugefügt.

Unregelmäßigkeiten entstehen durch Silbentrennungen, die nicht gut von Wortverbindungen getrennt werden können (siehe Know-how). 

## Architektur

`plenar.py` ist die Hauptfunktion, die den Rest orchestriert. Sie wird stündlich aufgerufen. `database.py` erlaubt eine Verbindung zur lokalen Redis Datenbank. 

`twitter_queue.py` packt neue Wörter in eine Warteliste und twittert diese in unterschiedlichen Zeitintervallen.

`fetch.xml` ruft das aktuelle Protokoll von der Seite. Der Link wurde hardgecodet und kann brechen. 

`scrape_functions.py` ist für die Worttrennung und Normalisierung da. 

`build_database.py` und `progressbar.py` gehen durch die vorher heruntergeladenen Protokolle und erstellen die Datenbank mit der neue Wörter abgeglichen werden. 

Die Webseite Sentry.io sorgt für schnelle Benachrichtigungen und die Dokumentation von Fehlern. 

## Was ist "neu"?

Aus Gründen der Unterhaltung werden einige Worte aussortiert, die zwar tatsächlich zum ersten Mal so gesagt werden, aber nur bedingt an sich einen Informationswert haben. Folgendes wird z.B. herausgefiltert:
- Plural
- Genitiv
- Gendern
- Wöter unter 4 Buchstaben

## TODOs
[ ] Sprecherin im Kontext mit erwähnen  
[ ] Weitere Verfeinerung der Wort-Normalisierung

## Lizenz

Das Projekt steht unter der [GNU General Public License 3](https://www.gnu.org/licenses/gpl-3.0.de.html). 

