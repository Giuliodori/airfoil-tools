# TODO operativo - Manta AirLab (DB-first)

Obiettivo: consolidare il passaggio da workflow solo NACA a workflow `NACA + Library` con dati reali da `database/airfoil.db`, mantenendo preview/export veloci.

## Stato generale

- Fasi 1-7: completate.
- Fase 8: in corso (rifiniture UX selezione Library e ranking).
- Prossime: robustezza interpolazione, rifiniture GUI/documentazione, hardening release.

## Fase 1 - Fondazione dati DB (completata)

- Modulo `airfoil_db_sqlite.py` con query per:
  - profili validi
  - geometria (`x_json`/`y_json` con fallback `raw_dat`)
  - polari (`cl`, `cd`, `cm`, `reynolds`, `alpha_deg`)
  - rating e usage metadata

## Fase 2 - Selettore Source in GUI (completata)

- `Source: NACA / Library`.
- Selezione profilo Library con aggiornamento preview immediato.
- Workflow NACA preservato.

## Fase 3 - Pipeline geometria unica (completata)

- Dispatcher unico geometria (`generate_profile_xy`).
- Trasformazioni riusate in entrambe le modalità:
  - chord/scale
  - curvature
  - rotation
  - mirror
- Export coerente alla geometria visualizzata (`.pts/.csv/.dxf/.stl`).

## Fase 4 - Aero da polari DB + ND (completata)

- Interpolazione:
  - logaritmica su Reynolds
  - lineare su alpha
- Coefficienti adattativi:
  - `re_scale`, `alpha_offset`, `cl_scale`, `cd_scale`
- Regole fuori dominio:
  - preview/export sempre disponibili
  - `Lift/Drag/L/D = ND` quando troppo lontani dai dati validi
  - soglie ND configurabili in Advanced options

## Fase 5 - Override XFOIL live (completata)

- Pulsante `XFOIL Simulation` in GUI.
- Override dei coefficienti con risultato reale XFOIL.
- Fallback automatico in caso di errore/non convergenza.
- Clear override automatico al cambio input.
- Stato inline in GUI (no popup bloccanti), progress bar e timeout visibile.

## Fase 6 - Modello fluido con temperatura (completata)

- Campo temperatura `1..40 °C`.
- Reynolds e forze aggiornati con proprietà del fluido dipendenti da temperatura.
- Visualizzazione mantenuta in `lift/drag` (kg) e vettori come metodo NACA.

## Fase 7 - Setup runtime asset (completata)

- `setup` ora aggiorna/scarica `database/airfoil.db` all’ultima release quando rilanciato (se non usi `--skip-airfoil-db`).
- Download DB più sicuro tramite file temporaneo + replace atomico.

## Fase 8 - Selezione profilo avanzata (in corso)

1. Finestra separata per selezione interattiva profili Library (ridurre complessità della main GUI).
2. Ricerca testuale rapida.
3. Ordinamento per rating principali.
4. Filtri per utilizzo (`usage`) per scremare a monte.
5. Ranking con pesi (slider) sulle caratteristiche principali.

## Fase 9 - Prossime implementazioni

1. Rifinitura interpolazione:
   - supporto robusto a passi Re/alpha non uniformi nel DB
   - miglior gestione extrapolation con criteri ND più chiari
2. Integrazione XFOIL avanzata:
   - miglior diagnostica (`non converge`, `geometria non valida`, `xfoil non trovato`)
   - eventuale persistenza controllata dei risultati simulati
3. Verifica allineamento tabellare vs live su casi campione.

## Fase 10 - Chiusura release

1. Test regressione:
   - NACA workflow invariato
   - Library workflow stabile
   - export in curvatura coerente in tutte le modalità
2. Rifiniture UI/colors.
3. Aggiornamento documentazione (`README.md`, `key_advantages.md`, `CLI.md` se necessario).
4. Tag release e note di changelog.
