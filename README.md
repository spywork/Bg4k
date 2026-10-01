# BG4K

Rimuove lo sfondo e salva un PNG trasparente con il lato lungo di **3840 pixel**, mantenendo le proporzioni. Funziona offline, senza interfaccia durante l'elaborazione, su Windows, macOS e Linux.

## Scarica

I programmi compilati sono in **[Releases](https://github.com/spywork/Bg4k/releases/latest)**.

| Sistema | Pacchetto | Uso |
| --- | --- | --- |
| Windows 10/11, 64 bit | BG4K_Windows_x86_64.zip | Trascina le foto su BG4K.exe. |
| macOS 14+, Apple Silicon (M1 e successivi) | BG4K_macOS_arm64.zip | Trascina le foto su BG4K.app. |
| macOS 15+, Intel | BG4K_macOS_x86_64.zip | Trascina le foto su BG4K.app. |
| Linux x86_64, glibc 2.35+ (Ubuntu 22.04+ e compatibili) | BG4K_Linux_x86_64.tar.gz | Installa il collegamento e scegli **Apri con BG4K**. |

Su Mac vedi il processore da **menu Apple → Informazioni su questo Mac**. Versioni macOS precedenti non verificate. Linux ARM e distribuzioni musl (come Alpine) non supportati.

## Uso

Estrai il pacchetto e metti il programma in una cartella **scrivibile**, ad esempio Immagini/BG4K, non una cartella di sistema. I risultati sono salvati accanto all'exe, all'app o al binario, **non nella cartella della foto**:

    foto.jpg → foto_bg4k.png

Su Windows trascina una o più foto sull'exe. Su Mac trascinale sull'icona dell'app nel Finder o usa **Apri con**. Il doppio clic senza foto termina senza finestre.

### Linux

Dopo aver estratto il tar.gz, esegui una volta dalla cartella del programma:

    ./Installa_collegamento.sh

Poi seleziona le foto e scegli **Apri con → BG4K** nel gestore file. Il collegamento è registrato solo per il tuo utente, senza sudo. Il trascinamento dipende dall'ambiente desktop. Se sposti il programma, riesegui lo script. Per rimuovere la registrazione, cancella ~/.local/share/applications/bg4k.desktop (o il file equivalente in $XDG_DATA_HOME/applications).

Uso diretto, anche per più foto:

    ./BG4K "/percorso/foto.jpg" "/percorso/altra foto.png"

## Note e limiti

- Modello IS-Net incluso: circa 200 MB, nessun Python, Internet o GPU richiesti per l'uso. Consigliati 8 GB di RAM.
- Le app non hanno firma di uno sviluppatore certificato. Mac usa una firma ad-hoc, senza notarizzazione Apple. Il sistema può richiedere di autorizzare l'apertura iniziale; su Mac usa le opzioni previste in **Impostazioni di Sistema → Privacy e sicurezza** per l'app che hai scelto di scaricare.
- I test automatici eseguono il binario reale su ogni sistema. Il trascinamento nel Finder e i diversi desktop Linux richiedono una verifica manuale sul computer dell'utente.
- Una foto verticale arriva a 3840 pixel di altezza, una orizzontale a 3840 di larghezza. Nessun ritaglio o bordo aggiunto.
- Il PNG conserva la trasparenza anche per ingressi JPG. Lanczos e una lieve nitidezza ingrandiscono senza ricostruire dettagli reali assenti.
- La rimozione automatica può sbagliare bordi, capelli e oggetti trasparenti.
- Formati: JPG/JPEG, PNG, WEBP, BMP e TIFF; primo fotogramma/pagina. HEIC e RAW non supportati.
- Gli originali ricevuti in ingresso sono protetti. Gli output con lo stesso nome vengono sostituiti senza conferma; sorgenti con lo stesso nome base producono lo stesso output.
- Errori in BG4K_errori.log accanto al programma. Una cartella non scrivibile impedisce anche il salvataggio del registro.
- Le foto restano sul computer. Orientamento EXIF applicato, metadati originali non copiati.

## Compilazione

Usa Python 3.12 **sul sistema di destinazione**:

    python -m pip install -r requirements-build.txt
    python build.py
    python test_smoke.py

build.py scarica il modello e verifica la checksum SHA-256. Pacchetti in release/. Solo compilazione e test richiedono Internet. Su Mac servono gli strumenti Apple, incluso codesign; il runner GitHub li include. Per il test Linux serve desktop-file-validate (desktop-file-utils su Ubuntu).

Per nuove versioni: **Actions → Compila e pubblica BG4K → Run workflow**, inserisci un tag nuovo come v1.2.0 e lascia attiva la pubblicazione. La release è pubblicata soltanto dopo compilazione e test riusciti su tutti i sistemi. Disattiva la pubblicazione per ottenere solo gli artefatti di prova.

## Licenze

Codice BG4K: MIT, vedi [LICENSE](LICENSE). Modello IS-Net e dipendenze: [LICENZE.txt](LICENZE.txt). Nei pacchetti sono aggiunte le licenze delle dipendenze effettivamente compilate.
