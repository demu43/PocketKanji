# PocketKanji su macOS

## Avvio consigliato

1. Sposta la cartella `PocketKanji` in una posizione stabile, per esempio Documenti.
2. Apri la cartella e fai doppio clic su `Avvia PocketKanji.command`.
3. Il browser predefinito si apre su `http://127.0.0.1:8765/PocketKanji.html` (oppure sulla prima porta libera fino alla 8775).
4. Lascia aperta la finestra del Terminale mentre usi l'app. Per fermare il servizio premi `Ctrl+C` o chiudi quella finestra.

Se il doppio clic non parte, apri Terminale, trascina `Avvia PocketKanji.command` nella finestra e premi Invio.

Il launcher richiede Python 3. Su questo Mac è già presente e il funzionamento è stato verificato con Python 3.9.6.

## Trasferire i progressi

Sul vecchio computer:

1. Apri PocketKanji usando il browser e l'indirizzo abituali.
2. Vai in **Progressi**.
3. Seleziona **Esporta backup** e conserva il file JSON.

Sul nuovo Mac:

1. Avvia PocketKanji con il launcher macOS.
2. Usa sempre lo stesso browser e, se possibile, la stessa porta locale.
3. Vai in **Progressi** e seleziona **Importa backup**.
4. Scegli il file JSON esportato e conferma la sostituzione dei progressi vuoti.

Il file ZIP dell'app non contiene automaticamente i progressi: il backup JSON è indispensabile per trasferirli.

## Dipendenze e sicurezza

- Browser moderno: Safari, Chrome, Firefox o Edge.
- Python 3, usato solo come server HTTP locale.
- Nessun account, database, pacchetto aggiuntivo o collegamento Internet.
- Il server ascolta soltanto su `127.0.0.1`, quindi non è accessibile dagli altri dispositivi della rete.
- Le 500 carte, lo stile e la logica dell'app sono incorporati in `PocketKanji.html`.
- I progressi sono salvati nel `localStorage` del browser con la chiave `pocketkanji.prototype.v1`.

## Attenzioni importanti

- Non usare la navigazione privata.
- Non cancellare i dati del sito `127.0.0.1` se non hai prima esportato un backup.
- Un browser diverso o una porta diversa crea un archivio locale distinto: in quel caso importa il backup JSON.
- Aprire direttamente `PocketKanji.html` usa un archivio distinto da quello di `localhost`; per continuità usa il launcher.
- Non autorizzare l'accesso dalla rete locale: PocketKanji deve restare limitato a questo computer.

## Avvio manuale di emergenza

Da Terminale, dentro la cartella `PocketKanji`:

```sh
python3 -m http.server 8765 --bind 127.0.0.1
```

Poi apri `http://127.0.0.1:8765/PocketKanji.html` nel browser. Per fermare il server premi `Ctrl+C`.
