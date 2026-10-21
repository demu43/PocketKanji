# PocketKanji

PocketKanji è una web app locale per studiare 500 kanji con schede, sessioni di ripasso, ricerca, statistiche ed esportazione dei progressi.

L'applicazione è autonoma: HTML, CSS, JavaScript e dati delle carte sono incorporati in `PocketKanji.html`. Non richiede account, database o servizi cloud e non invia dati su Internet.

## Funzionalità

- 500 schede in ordine didattico.
- Letture **Kun'yomi** in hiragana e **On'yomi** in katakana.
- Romaji sotto ogni lettura, disattivabile dall'interfaccia.
- Un vocabolo d'esempio verificato per ogni lettura mostrata, con lettura completa in hiragana e traduzione inglese.
- Evidenziazione del kanji studiato e del segmento fonetico corrispondente mediante intervalli verificati, senza ricerca testuale approssimativa.
- Indicazioni discrete per vocaboli avanzati e per mutazioni fonetiche o letture contestuali.
- Kanji principali delle flashcard e della Libreria resi con il font giapponese Noto Sans JP incluso localmente.
- Layout delle letture affiancato su desktop e impilato su mobile.
- Sessioni da 10 carte nuove e fino a 20 ripassi dovuti.
- Progressi, cronologia e impostazioni salvati nel browser.
- Backup JSON ed esportazioni CSV.
- Compatibilità con i backup creati prima dell'aggiunta delle letture Kun/On.
- Nessuna sincronizzazione automatica o dipendenza remota.

## Avvio

### macOS

1. Conserva la repository in una posizione stabile.
2. Fai doppio clic su `Avvia PocketKanji.command`.
3. Lascia aperta la finestra del Terminale mentre usi l'app.

Il launcher richiede Python 3 e serve l'app soltanto su `127.0.0.1`, scegliendo la prima porta libera tra 8765 e 8775.

### Windows 10/11

Fai doppio clic su `Avvia PocketKanji.cmd`. Il launcher usa Windows PowerShell e non richiede installazioni aggiuntive.

### Linux

Dalla cartella della repository:

```sh
python3 -m http.server 8765 --bind 127.0.0.1
```

Apri quindi <http://127.0.0.1:8765/PocketKanji.html>.

## Progressi e backup

I progressi sono salvati nel `localStorage` del browser con la chiave `pocketkanji.prototype.v1`.

Per ritrovarli automaticamente usa sempre:

- lo stesso browser;
- lo stesso host `127.0.0.1`;
- la stessa porta, normalmente 8765;
- una finestra non privata.

Prima di cambiare computer o aggiornare i file, apri **Progressi → Esporta backup**. Sul computer di destinazione usa **Progressi → Importa backup**.

## Aggiornamento di un'installazione esistente

1. Esporta un backup JSON dalla versione in uso.
2. Chiudi il vecchio server o la finestra del Terminale.
3. Aggiorna la repository o sostituisci i file del programma.
4. Riavvia PocketKanji con il launcher del sistema operativo.
5. Controlla i progressi e importa il backup solo se necessario.

I 500 ID delle carte e lo schema dei progressi restano stabili fra la versione precedente e quella con letture Kun/On.

## Struttura

```text
PocketKanji.html                 applicazione e libreria delle carte
Avvia PocketKanji.command       launcher macOS
Avvia-PocketKanji-macOS.sh      server locale macOS
Avvia PocketKanji.cmd           launcher Windows
Avvia-PocketKanji.ps1           server locale Windows
docs/                            istruzioni, analisi e attribuzione dati
tools/                           strumenti di aggiornamento e controllo
assets/                          font Noto Sans JP e relativa licenza OFL
```

## Verifica locale

```sh
python3 tools/check_data.py
```

Il controllo verifica numero e ID delle carte, copertura completa degli esempi, formato kana, carta `日`, compatibilità del salvataggio e regole responsive essenziali.

## Fonti delle letture

La selezione didattica delle letture è stata verificata rispetto a [KANJIDIC2](https://www.edrdg.org/wiki/KANJIDIC_Project.html). I vocaboli e le traduzioni derivano da [JMdict](https://www.edrdg.org/wiki/Main_Page.html), mentre l'associazione fra kanji e porzione letta usa [JmdictFurigana](https://github.com/Doublevil/JmdictFurigana). Queste risorse sono distribuite secondo CC BY-SA 4.0. Le liste N5 usate come priorità sono criteri didattici, non liste ufficiali del JLPT.

Il font incluso è [Noto Sans JP](https://github.com/google/fonts/tree/main/ofl/notosansjp), distribuito secondo SIL Open Font License 1.1; la licenza è conservata in `assets/OFL-NotoSansJP.txt`.

Consulta [docs/ATTRIBUZIONE-DATI.md](docs/ATTRIBUZIONE-DATI.md) per i dettagli.

## Sicurezza

I launcher ascoltano esclusivamente sull'indirizzo locale `127.0.0.1`. Non modificare il bind in `0.0.0.0`, perché renderebbe l'app raggiungibile dalla rete locale senza alcuna necessità.
