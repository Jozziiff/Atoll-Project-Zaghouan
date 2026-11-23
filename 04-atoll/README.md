# Atoll : projet, captures et exports

| Élément | Contenu |
|---|---|
| [`Zaghouan_LTE.ATL`](Zaghouan_LTE.ATL) | le projet Atoll 3.3 (réseau, prédictions, simulations Monte-Carlo) |
| [`captures/`](captures/) | les réglages d'Atoll, écran par écran, dans l'ordre du travail : `S01` import et modèles · `S02` réseau · `S03` prédictions · `S04` trafic et Monte-Carlo · `S05` optimisation (ACP, ANR) |
| [`exports/`](exports/) | les livrables, nommés par numéro de livrable (voir ci-dessous) |
| `analyse_couverture.py`, `zones_raster.py` | lisent les rasters exportés d'Atoll et calculent la couverture par zone (ville indoor, campagne outdoor, en surface et en population) : la même mesure pour chaque action d'optimisation |
| `dcfi.py` | trace la DCFI à partir des débits de chaque utilisateur exportés des simulations Monte-Carlo |

## Les exports

Les numéros suivent l'ordre des livrables du § 4.2 du sujet.

| Préfixe | Livrable | Fichiers |
|---|---|---|
| `L-01` | couverture par niveau de signal (indoor, outdoor) | `L-01_signal_*` |
| `L-01b` | couverture par C/(I+N) en DL (charge 100 %, charge simulée, réseau final…) | `L-01b_CINR_DL_*`, `L-01b_histogramme_*` |
| `L-02` | histogramme de la couverture par niveau de signal | `L-02_histogramme_*` |
| `L-04` | couverture par émetteur | `L-04_par_emetteur_*` |
| `L-05` | recouvrement et son histogramme | `L-05_*` |
| `L-07` / `L-08` | débit DL / UL et leurs histogrammes | `L-07_*`, `L-08_*` |
| `L-11` | DCFI pour 10, 100 et 1 000 utilisateurs, et avant / après optimisation | `L-11_DCFI*.png`, `dcfi.md`, `dcfi_final.md` |
| `L-12` | optimisation, une carte et un tableau par étape | `trous_couverture_<étape>.png`, `couverture_zones_<étape>.md` |
| — | données des simulations (un fichier par tirage, une ligne par utilisateur) | `montecarlo/` |
| — | rasters exportés d'Atoll, lus par nos scripts | `raster/` |

Les légendes (L-3, L-6, L-9) sont visibles sur les captures de carte d'Atoll, dans le panneau « Legend ».

Étapes d'optimisation, dans l'ordre : `initial` → `tilt6` (tilt urbain 6°) → `sansR02` (R02 éteint) → `R07` et `R07az` (rejetées) → `R11` → `R12` → `acp` → `final`, puis `tilt8` (rejetée).
