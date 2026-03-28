# Airfoil Tools

[![Latest Release](https://img.shields.io/github/v/release/giuliodori/airfoil-tools)](https://github.com/giuliodori/airfoil-tools/releases/latest)


Airfoil Tools e' una GUI desktop per generare profili NACA a 4 cifre, classico profilo dell'aerodinamica usato in ali, idrofoil e superfici portanti. Esporta in `.pts` e `.dxf` e stima `lift` e `drag`.

![gui](images/gui.png)
![Manta](images/manta.jpg)

## Installazione semplice (exe consigliato)

Per la maggior parte degli utenti e' sufficiente l'eseguibile.

### 1) Download

Scarica la cartella con l'eseguibile da GitHub:

```text
https://github.com/giuliodori/airfoil-tools/releases/latest
```

Se hai clonato o scaricato lo ZIP del repository, il file principale su Windows e':
- `airfoil-tools\dist\airfoil-tools.exe`

### 2) Avvio

- Fai doppio click su `airfoil-tools\dist\airfoil-tools.exe`.
- La GUI si apre e puoi subito generare ed esportare i profili.

Avvio rapido alternativo dalla cartella del repository:
- Doppio click su `airfoil-tools.bat`

## Codice sorgente Python (opzionale)

Usa questa sezione solo se vuoi eseguire da sorgente.

### Requisiti (solo sorgente)

- Python 3.10+
- `numpy`
- `matplotlib`
- `ezdxf` (necessario per l'export `.dxf`)

Installa le dipendenze:

```bash
python -m pip install numpy matplotlib ezdxf
```

Esegui:

```bash
python airfoil_tools.py
```

Su Windows puoi anche usare:
- `airfoil-tools.bat`

## Esempi di CAD per `.pts` e `.dxf`

### CAD/3D con supporto DXF

- AutoCAD
- CREO Parametric
- Fusion 360
- Inventor
- SolidWorks
- FreeCAD
- Rhino
- BricsCAD
- DraftSight
- QCAD
- LibreCAD
- Onshape (workflow DXF)

### Software per file di punti (`.pts`/XYZ)

- CloudCompare
- MeshLab
- MATLAB
- GNU Octave
- Python (NumPy / Pandas)
- CATIA (import punti)
- Siemens NX (import punti)
- Autodesk Alias (point set)

## La storia dei profili NACA: il "LEGO" dell'aerodinamica

Se stai progettando un'ala che deve sollevare un aereo, un idrofoil o un alettone che deve tenere incollata a terra una Formula 1, prima o poi ti imbatterai in quattro lettere fondamentali: `NACA`.

I profili NACA sono diventati un riferimento storico perche' hanno portato ordine in un campo che, nei primi decenni dell'aviazione, era spesso guidato da tentativi, esperienza pratica e molte prove in galleria del vento. Tra la fine degli anni '20 e l'inizio degli anni '30, la National Advisory Committee for Aeronautics sviluppo' un sistema semplice ma potentissimo: descrivere la forma del profilo con una sigla numerica, invece di affidarsi solo a nomi o disegni.

### 1) Com'e' nato tutto: ordine nel caos

Prima degli anni '30, scegliere un profilo alare era molto meno standardizzato. La NACA introdusse famiglie di profili codificate e pubblicate in cataloghi tecnici, cosi' gli ingegneri poterono finalmente selezionare una geometria in modo ripetibile, confrontabile e documentato. In pratica, fu come passare da prototipi artigianali a componenti di libreria.

### 2) La serie a 4 cifre: il pane quotidiano dei maker

La serie NACA a 4 cifre e' la piu' famosa ed e' ancora oggi una delle piu' facili da capire e usare.

Prendiamo `NACA 2412`:

- `2`: curvatura massima pari al 2% della corda
- `4`: posizione della curvatura massima al 40% della corda
- `12`: spessore massimo pari al 12% della corda

Questa codifica semplice rende i profili NACA molto pratici per modellismo, studio preliminare, stampa 3D, taglio CNC e primi dimensionamenti. Il `NACA 0012`, per esempio, e' simmetrico ed e' un classico per piani di coda, timoni, appendici e test sperimentali.

### 3) La caccia alla velocita': la serie 6

Negli anni '40, con l'aumento delle velocita', l'attenzione si sposto' sempre di piu' sulla resistenza aerodinamica. Da qui nacquero le serie laminate, come la Serie 6, progettate per favorire un flusso piu' regolare e ridurre la resistenza in specifici intervalli di funzionamento.

Un caso celebre e' il `P-51 Mustang`, spesso associato alla famiglia di profili laminari NACA: una parte importante delle sue prestazioni ad alta velocita' e della sua autonomia dipendeva anche da queste scelte aerodinamiche.

### 4) Non solo ali: F1, MotoGP e condotti NACA

I profili NACA non sono utili solo in aeronautica.

- I profili simmetrici, come `NACA 0012`, sono adatti anche ad alettoni, pinne e superfici che devono generare carico aerodinamico con comportamento pulito e prevedibile.
- I `NACA ducts`, le prese d'aria incassate a bassa resistenza, sono ancora oggi usati in auto sportive, moto da corsa e applicazioni tecniche dove serve raffreddamento con minimo disturbo aerodinamico.

### 5) L'evoluzione moderna: profili supercritici

Con l'arrivo dei velivoli ad alte prestazioni e del trasporto commerciale moderno, la ricerca si e' spostata verso profili piu' sofisticati, come i supercritici, ottimizzati per ritardare gli effetti compressibili e migliorare l'efficienza vicino ai regimi transonici.

Questo non rende obsoleti i profili NACA classici: al contrario, li rende ancora piu' preziosi come base di studio, confronto e progettazione preliminare.

### Perche' usarli ancora oggi

Per un progettista, un maker o chi sta sviluppando un primo concetto aerodinamico, i profili NACA restano una garanzia:

- hanno decenni di dati sperimentali alle spalle
- sono facili da descrivere, generare e confrontare
- permettono di partire da una geometria nota prima di passare a CFD o test piu' avanzati

Se usi un `NACA 4412`, per esempio, non stai partendo da una forma arbitraria: stai usando un riferimento storico ben documentato, utile per ottenere un primo dimensionamento credibile gia' nelle fasi iniziali del progetto.

### Perche' questo tool e' utile

`airfoil-tools` nasce proprio per questo: prendere una geometria nota e renderla subito utilizzabile.

Con pochi passaggi puoi:

- generare il profilo
- esportarlo in formati semplici per CAD e modellazione
- ottenere una stima immediata di `lift` e `drag`

Questo riduce il tempo necessario per passare dall'idea a un primo modello tecnico, lasciando piu' spazio alla verifica, all'iterazione e alla costruzione.

## Note sui profili NACA 4 cifre

I profili NACA a 4 cifre sono una famiglia storica di profili alari descritta da quattro numeri che codificano la geometria in modo semplice e riproducibile. Restano un riferimento solido per studio preliminare, didattica e comparazioni rapide: sono facili da comunicare, da generare e da confrontare.

### Significato delle cifre

Le quattro cifre sono `M P TT`:

- `M` (prima cifra) e' il massimo camber in percentuale della corda.
- `P` (seconda cifra) e' la posizione del massimo camber in decimi di corda.
- `TT` (ultime due cifre) e' lo spessore massimo in percentuale della corda.

Esempio:

`NACA 2412` significa camber massimo 2% a 40% di corda, spessore 12%.



### Come si leggono al volo e dove si usano

Profili simmetrici (camber zero) per applicazioni dove serve comportamento simmetrico:

- `NACA 0012` e `NACA 0015` per superfici di coda, timoni e profili generici.

Profili con camber moderato per ali e piccoli velivoli:

- `NACA 2412` e `NACA 4412` per ali leggere e applicazioni generiche dove serve buona portanza.

Profili piu' spessi per robustezza strutturale o basse velocita':

- `NACA 0018` e `NACA 4418` per strutture con vincoli di spessore o Reynolds piu' bassi.

## Licenza

Questo progetto e' rilasciato con doppia licenza:

- GNU General Public License v3.0 (GPL-3.0-only) per uso open-source
- Licenza commerciale per uso proprietario o closed-source

Per licenze commerciali:
- info@duilio.cc
