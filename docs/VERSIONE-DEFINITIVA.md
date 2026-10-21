# PocketKanji — versione definitiva personale

Accettata dall'utente il 21 ottobre 2026. Questa versione costituisce il riferimento definitivo: non aggiungere funzionalita', cambiare interfaccia o modificare le regole di studio senza una nuova richiesta esplicita.

Configurazione accettata:
- 500 kanji nell'ordine della libreria fornita.
- Kanji sul fronte, lettura e parola di riferimento, significati ed esempi tradotti in inglese sul retro.
- Sessioni da 10 nuove carte; ripassi prioritari.
- Stack conosciute e da consolidare, con stato non ancora studiate.
- Interfaccia in italiano, colore principale blu scuro.
- Rimossi il blocco introduttivo della schermata Oggi e il sottotitolo sotto PocketKanji.
- Progressi salvati nel browser; backup JSON ed esportazioni CSV.
- Nessuna sincronizzazione automatica con Google Drive e nessun database separato dal browser.
- Avvio Windows tramite Avvia PocketKanji.cmd; cartella e file necessari inclusi nel pacchetto.
- Su Mac avvio locale tramite `Avvia PocketKanji.command`, verificato su macOS con Python 3.

Il pacchetto definitivo non contiene i progressi del browser: esportarli dall'app per trasferirli su un altro computer. L'eventuale backup del 20 ottobre presente nella cartella del progetto e' un salvataggio storico, non una copia continuamente aggiornata.

Le diciture interne "prototipo" e "v0.1" sono rimaste quelle dell'interfaccia approvata. Non indicano modifiche ulteriori da effettuare.

Aggiornamento richiesto il 21 ottobre 2026:
- Ogni carta contiene i campi strutturati `kun_readings` e `on_readings` con kana e romaji.
- Il retro e la scheda di dettaglio mostrano prima Kun'yomi e poi On'yomi, affiancati su desktop e impilati su schermi piccoli.
- Le letture già curate sono state controllate rispetto a KANJIDIC2; non sono state importate in massa letture rare o nominali.
- La carta 日 include ひ / か, ニチ / ジツ e gli esempi 日, 日曜日, 毎日.
- Quiz, intervalli di ripasso, ID delle carte e chiave `localStorage` restano invariati.
- I backup della versione precedente restano importabili tramite il confronto stabile di ID, ordine e kanji.
- Gli esempi evidenziano kanji e segmento fonetico soltanto tramite allineamenti verificati; i casi ambigui restano senza evidenziazione.
- Il kanji principale usa Noto Sans JP incluso localmente, senza SVG o trasformazioni grafiche e senza modifiche a dimensione, colore o posizione.
