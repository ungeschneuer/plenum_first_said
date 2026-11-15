# Plenum First Said


Plenum First Said ist ein Bot, der neue Wörter postet, die zum ersten Mal während einer Bundestagsdebatte gesagt wurden. Es wird in keiner Weise Korrektheit garantiert. 

Das Projekt wurde durch den Twitter-Account [@NYT_first_said](https://x.com/NYT_first_said) von Max Bittker inspiriert und dessen [Code](https://github.com/MaxBittker/nyt-first-said) als Startpunkt genutzt, jedoch zum großen Teil verändert. 

## Funktionsweise

Der Bot postet Wörter, die im neuesten Plenarprotokoll zum ersten Mal seit 1949 vorkommen. Welche das sind,
ermittelt die Seite [Bundestag Wortschatz](https://ungeschneuer.github.io/plenum_first_said_website/)
([Quellcode](https://github.com/ungeschneuer/plenum_first_said_website)): Sie zählt jedes Wort aller
Plenarprotokolle und führt gebeugte Formen auf ihre Grundform zurück. Plural, Genitiv und andere Formen eines
schon gesagten Wortes gelten damit nicht als neu. Weibliche Formen sind eigene Wörter.

Die Seite veröffentlicht die Wörter, die in den Protokollen der letzten 90 Tage zum ersten Mal vorkommen
(`data/neue-woerter.json`). Der Workflow `.github/workflows/bot.yml` läuft stündlich: `parser/bot.py` nimmt neue
Wörter in die Warteschlange auf und postet höchstens eines, danach wartet der Bot zufällig 55 bis 120 Minuten.
Warteschlange und bereits gepostete Wörter stehen in `state/bot.json`, das der Workflow committet. Wörter aus
Protokollen, die älter als 30 Tage sind, werden nicht mehr gepostet. Beim ersten Lauf werden die vorhandenen
Kandidaten nur vermerkt, damit nichts doppelt erscheint, was der frühere Bot schon gepostet hat.

Aus Gründen der Unterhaltung werden einige Wörter aussortiert: Wörter unter fünf Buchstaben, Wörter mit Ziffern
oder Großbuchstaben im Wortinneren (Abkürzungen, zusammengeklebte Wörter), kleingeschriebene Bindestrich-Wörter, die
von Zeilenumbrüchen stammen können, und Varianten eines anderen neuen Wortes.

Der Account [@FSBT_Kontext](https://mastodon.social/@FSBT_Kontext) antwortet auf jeden Post mit Kontext: Sitzung,
Datum, Redner:in, Video bei Open Parliament TV, PDF des Protokolls und der Verlauf des Wortes auf Bundestag
Wortschatz. Ab der 19. Wahlperiode kommt die Person, die das Wort zuerst gesagt hat, aus den strukturierten
Protokollen des Bundestages, wenn Open Parliament TV sie nicht kennt. Bei Wörtern aus Reden der AfD setzt der Bot
eine Inhaltswarnung.

## Einrichtung

Der Bot braucht zwei Secrets im Repository: `MASTODON_FIRST_ACCESSTOKEN` (@BT_First_Said) und
`MASTODON_KONTEXT_ACCESSTOKEN` (@FSBT_Kontext). Ohne sie pflegt er die Warteschlange, postet aber nicht. Wie man
die Tokens erstellt, beschreibt [Mastodon.py](https://github.com/halcy/Mastodon.py). Für lokale Versuche liegen die
Namen der Variablen in `example.env`; Tests laufen mit `python -m unittest discover --start-directory tests`.

## Open Parliament TV API
Open Parliament TV bereitet selber die Protokolle für ihr eigenes Projekt auf, den Text mit der Videoaufzeichung zu verbinden. Dies nutze ich: 

1. Zum erneuten Abgleich ob das Wort **wirklich** noch nicht gesagt wurde (seit 2017).
2. Um dem Wort mehr Kontext zu geben.

Hierbei gibt es einige Limitierungen. Da die Protokolle weiterhin nicht vollkommen automatisiert verarbeitet werden können, hat OPTV immer wieder einen Delay von ein paar Tagen. Außerdem wird nur der Text verarbeitet, der wirklich gesagt wurde und nicht die Teile, die schriftlich eingereicht werden. 

[Webseite zur API](https://de.openparliament.tv/api/)  
[Webseite zum Projekt](https://openparliament.tv/)  
[GitHub](https://github.com/OpenParliamentTV)  

## Lizenz und Danksagung

Das Projekt steht unter der [GNU General Public License 3](https://www.gnu.org/licenses/gpl-3.0.de.html).  
Das Projekt entsteht im Rahmen eines Nachwuchs-Stipendiums des [Bayerische Staatministeriums für Wissenschaft und Kunst](https://www.stmwk.bayern.de/) zur Förderung der künstlerischen Entfaltung. Außerdem noch ein großes Danke an [jk](https://github.com/hejjoe), der meinen Bot deutlich aufmerksamer beobachtet als ich selbst. 



