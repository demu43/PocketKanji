# Installare l'aggiornamento Kun'yomi / On'yomi

## Sul Mac già in uso

1. Nella versione attuale apri **Progressi** e seleziona **Esporta backup**. È una precauzione: l'aggiornamento mantiene lo stesso archivio del browser.
2. Chiudi la vecchia finestra del Terminale che sta eseguendo PocketKanji.
3. Sostituisci la vecchia cartella del programma con la cartella `PocketKanji` inclusa in questo pacchetto, mantenendola nella posizione abituale.
4. Avvia `Avvia PocketKanji.command`.
5. Apri il preferito di Chrome già salvato oppure usa la pagina aperta automaticamente.
6. Controlla la pagina **Progressi**. Poiché host, porta e browser non cambiano, i progressi dovrebbero essere già presenti.
7. Se non compaiono, usa **Importa backup** e seleziona il JSON esportato al punto 1.

È importante chiudere prima il vecchio Terminale: finché il vecchio server resta attivo, il preferito di Chrome continua a mostrare i file della vecchia cartella.

## Su Windows

1. Copia la cartella `PocketKanji` sul computer Windows.
2. Avvia `Avvia PocketKanji.cmd`.
3. Da **Progressi**, importa il backup JSON proveniente dal Mac.

I backup creati prima di questo aggiornamento sono compatibili: le nuove informazioni sulle letture e i vocaboli d'esempio non cambiano gli ID delle carte né lo schema dei progressi.

Ogni lettura mostrata possiede ora un vocabolo associato. La lettura completa della parola è in hiragana; una nota discreta segnala gli usi contestuali o le mutazioni fonetiche, mentre `Advanced` identifica gli esempi usati soltanto quando non è disponibile un'alternativa elementare adeguata.
