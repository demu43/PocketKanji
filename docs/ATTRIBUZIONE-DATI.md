# Attribuzione dei dati sulle letture

Le letture giapponesi presenti in PocketKanji sono state controllate rispetto a **KANJIDIC2**, progetto dell'Electronic Dictionary Research and Development Group (EDRDG).

- Progetto: <https://www.edrdg.org/wiki/KANJIDIC_Project.html>
- Licenza della fonte: Creative Commons Attribution-ShareAlike 4.0
- La selezione e l'ordine delle letture mostrati da PocketKanji sono adattamenti didattici: privilegiano le forme già usate nella libreria e quelle utili al livello iniziale, senza includere automaticamente tutte le letture disponibili nella fonte.
- Le parti del dataset delle letture derivate da KANJIDIC2 sono distribuite secondo la medesima licenza CC BY-SA 4.0.

KANJIDIC2 distingue le letture `ja_kun` (normalmente in hiragana) dalle letture `ja_on` (in katakana). Le letture riservate ai nomi propri (`nanori`) non sono state aggiunte alle schede principali.

## Vocaboli ed esempi d'uso

Gli esempi associati alle letture sono stati costruiti usando **JMdict_e**, il dizionario giapponese-inglese mantenuto dall'EDRDG, e **JmdictFurigana**, che collega le porzioni in kanji alle rispettive porzioni della lettura.

- JMdict/EDICT: <https://www.edrdg.org/wiki/Main_Page.html>
- JmdictFurigana: <https://github.com/Doublevil/JmdictFurigana>
- Licenza dei dati derivati: Creative Commons Attribution-ShareAlike 4.0

I marcatori di priorità di JMdict vengono usati come indizio di frequenza, non come livello JLPT ufficiale. PocketKanji applica inoltre una preferenza didattica al lessico elementare e ai vocaboli già presenti nella propria libreria. Non esiste una lista ufficiale completa di vocaboli JLPT N5 pubblicata dall'ente JLPT.

Le letture contestuali e le mutazioni fonetiche non separabili automaticamente sono mantenute in un piccolo elenco revisionato manualmente. La scheda le segnala con una nota d'uso; per esempio `か` in `三日（みっか）`, `シツ → しっ` in `失敗（しっぱい）` e `ハイ → ぱい` in `一杯（いっぱい）`.

Le fonti complete non sono caricate dall'app durante l'uso: PocketKanji rimane autonomo e incorpora soltanto i campi selezionati necessari alle schede.
