# PocketKanji — analisi tecnica e avvio

Verifica eseguita il 21 ottobre 2026.

Aggiornamento letture verificato il 21 ottobre 2026: le 500 carte includono ora campi separati per Kun'yomi e On'yomi, con romaji e layout responsivo. La selezione conserva le letture didattiche già presenti, verificate rispetto a KANJIDIC2, e non importa automaticamente letture rare o nominali.

## Stack

PocketKanji non è un servizio con backend tradizionale. È una web app statica e locale composta da:

- HTML5, CSS e JavaScript puro, tutti inclusi in `PocketKanji.html`;
- il font Noto Sans JP incluso localmente nella cartella `assets` per il kanji principale delle flashcard;
- una libreria JSON incorporata nello stesso file con 500 carte (`pk0001`–`pk0500`);
- `localStorage` del browser per progressi, cronologia e impostazioni;
- esportazione e importazione di backup JSON;
- esportazioni CSV generate nel browser;
- un piccolo server HTTP in ascolto soltanto su `127.0.0.1`.

Non risultano framework, package manager, servizi cloud, database, API remote, font remoti o altre risorse Internet necessarie durante l'uso.

La chiave di salvataggio è `pocketkanji.prototype.v1`. I dati appartengono all'origine del browser: browser, protocollo, host e porta devono rimanere coerenti per ritrovare automaticamente i progressi.

## Verifica funzionale

Su macOS la pagina è stata servita tramite `127.0.0.1:8765` e aperta nel browser. Sono stati verificati:

- caricamento delle 500 carte;
- avvio di una sessione da 10 carte;
- visualizzazione del retro della carta;
- registrazione di una valutazione;
- aggiornamento dei contatori e della cronologia;
- assenza di errori o avvisi della pagina nel browser durante il test;
- importazione riuscita di un backup costruito con la libreria precedente;
- mantenimento degli stessi 500 ID e dello stesso schema dei progressi;
- visualizzazione affiancata su desktop e impilata a 390 px di larghezza;
- quiz e pulsanti di valutazione invariati.

L'avviatore Windows è stato ispezionato ma non eseguito, perché il test è avvenuto su macOS.

## Dipendenze per sistema operativo

### Windows 10 o 11

- Browser moderno.
- Windows PowerShell (`powershell.exe`), già incluso normalmente nel sistema.
- Avvio: doppio clic su `Avvia PocketKanji.cmd`.

Lo script cerca una porta libera tra 8765 e 8775, apre il browser, ascolta solo su loopback e termina dopo otto ore senza richieste.

### macOS

- Browser moderno.
- Python 3 per il launcher locale incluso in questa copia.
- Avvio: doppio clic su `Avvia PocketKanji.command`.

Su questo Mac è stato rilevato Python 3.9.6. Il launcher usa la prima porta libera tra 8765 e 8775 e non espone il servizio alla rete locale.

### Linux

- Browser moderno.
- Python 3.
- Avvio manuale, dalla cartella dell'app:

```sh
python3 -m http.server 8765 --bind 127.0.0.1
```

Aprire quindi `http://127.0.0.1:8765/PocketKanji.html`.

## Configurazione consigliata

- Tenere la cartella in una posizione stabile.
- Usare sempre lo stesso browser e l'indirizzo `127.0.0.1` con la stessa porta.
- Non usare una finestra privata.
- Non aprire abitualmente il file HTML con `file://`, perché crea un archivio separato da quello usato tramite localhost.
- Non modificare il bind da `127.0.0.1` a `0.0.0.0`: non serve e renderebbe il servizio raggiungibile dalla rete.
- Esportare periodicamente un backup JSON dalla pagina **Progressi**.

## Trasferimento corretto

1. Sul computer vecchio aprire PocketKanji nel browser abituale.
2. Da **Progressi**, esportare un backup JSON.
3. Copiare sul computer nuovo sia la cartella dell'app sia il backup JSON.
4. Avviare l'app con il metodo previsto per il nuovo sistema operativo.
5. Da **Progressi**, importare il backup JSON e confermare.

Il solo archivio ZIP non trasferisce i progressi già presenti nel browser.

## Diagnostica rapida

- **La pagina non si apre:** controllare che Python 3 o PowerShell siano disponibili e che almeno una porta tra 8765 e 8775 sia libera.
- **I progressi sembrano spariti:** verificare browser, host e porta; poi importare l'ultimo backup JSON.
- **Windows segnala un errore:** leggere `PocketKanji-errore.txt` nella cartella dell'app.
- **macOS segnala un errore:** leggere il percorso del log mostrato dal launcher nel Terminale.
- **I kanji hanno un aspetto diverso:** è una differenza del font giapponese disponibile nel sistema, non dei dati delle carte.
