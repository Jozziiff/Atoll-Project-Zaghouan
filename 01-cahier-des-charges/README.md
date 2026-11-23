# Cahier des charges

Zone d'étude, norme retenue, objectifs et hypothèses du dimensionnement.
Chaque valeur a une source ; le code de l'Étape 1 ([`02-dimensionnement/params.py`](../02-dimensionnement/params.py)) et la configuration d'Atoll reprennent exactement ces valeurs (les identifiants A3, B1, D4… sont repris dans les commentaires du code).

**Sources :** `Atoll` = valeurs par défaut des modèles LTE d'Atoll 3.3 (captures dans [`04-atoll/captures/`](../04-atoll/captures/)) · `3GPP` = TS 36.101 · `Cours` = cours de planification (Dr Afif) · `INTT` = Instance Nationale des Télécommunications, tableau de bord trimestriel TR4-2025 · `Hyp.` = hypothèse de travail, justifiée dans la colonne valeur.

---

## 1. La zone : Zaghouan

| | |
|---|---|
| Emprise | 10 × 10 km, UTM 32N (EPSG:32632), X 596 – 606 km, Y 4 022 – 4 032 km |
| Population | **25 359 habitants** (WorldPop 2020) |
| Relief | Djebel Zaghouan, crête SO – NE, point culminant de la zone **1 238 m** (MNT Copernicus) ; ville vers 150 – 250 m |
| Occupation du sol | prairies 38 %, forêt 27,5 %, arbustes 13,3 %, cultures 13 %, bâti 6,6 %, sol nu 1,3 %, eau 0,1 % (ESA WorldCover) |
| Contexte télécom | Zaghouan a accueilli en 2016 le premier pilote de partage de réseau d'accès d'Afrique du Nord (Tunisie Télécom + Ooredoo) |

| Zone | Définition | Surface | Habitants | Stratégie |
|---|---|---|---|---|
| **Centre urbain** | densité ≥ 1 000 hab/km² | 8,57 km² | 13 590 | dimensionnement par la **capacité**, objectif **indoor** |
| **Rural** | le reste de la zone | 76,95 km² | 11 476 | dimensionnement par la **couverture**, objectif **outdoor** |
| **Massif** | altitude ≥ 600 m (parc national) | 14,48 km² | 292 | aucun site, aucun objectif |

Pourquoi cette zone : un centre urbain et une périphérie rurale permettent de traiter les deux parties du sujet (§ 3.2 et § 3.3), et le massif crée de vraies zones d'ombre radio, donc un vrai travail d'optimisation.

## 2. Norme et spectre

| # | Paramètre | Valeur | Source |
|---|---|---|---|
| A1 | Norme | **LTE** (E-UTRA), FDD, OFDMA en DL / SC-FDMA en UL | — |
| A2 | Bande | **Bande 3** : UL 1 710 – 1 785 MHz, DL 1 805 – 1 880 MHz (2 × 75 MHz) | 3GPP, Atoll |
| A3 | Canal | **20 MHz**, 100 blocs de ressources ; EARFCN 1300 → centre DL **1 815 MHz**, UL **1 720 MHz** | Atoll |
| A4 | Réutilisation | **K = 1** : toutes les cellules sur la même porteuse de 20 MHz | Cours (C/I), calcul |
| A5 | Bande de comparaison | Bande 20 (800 MHz) : 2 × 30 MHz pour trois opérateurs, soit **≤ 10 MHz** chacun | 3GPP |

**Pourquoi le LTE :** le sujet demande des cartes de débit DL / UL et des simulations Monte-Carlo ; dans Atoll 3.3, ces outils existent pour l'UMTS, le WiMAX et le LTE, pas pour le GSM. Fin 2025, 84 % des smartphones tunisiens sont compatibles 4G contre 9 % compatibles 5G (INTT) : le LTE reste la couche qui porte le trafic dans une ville comme Zaghouan.

## 3. Équipements

| # | Paramètre | Valeur | Source |
|---|---|---|---|
| B1 | Puissance eNodeB | **46 dBm** (40 W) : garde la puissance par sous-porteuse du modèle Atoll (RS EPRE 15,2 dBm) sur 20 MHz : 15,2 + 10 log 1 200 = 46 | Atoll + calcul |
| B2 | Facteur de bruit eNodeB | **5 dB** (valeur utilisée par le modèle de station d'Atoll) | Atoll |
| B3 | Antenne tri-secteur | **65°, 18 dBi** (retenue) | Atoll |
| B4 | Antenne omni (comparaison) | 11 dBi | Atoll |
| B5 | Antenne 6 secteurs (comparaison) | 33°, 21 dBi | Atoll |
| B6 | Pertes émission / réception | **1 dB** : tête radio déportée en haut du mât (au lieu de 2,3 dB pour 30 m de câble) | Atoll + hyp. |
| B7 | Amplificateur de mât | non utilisé (inutile avec une tête radio déportée) | — |
| B8 | Hauteur / tilt | **30 m** ; tilt électrique **4°** urbain, **2°** rural ; 2 × 2 MIMO | Atoll |
| B9 | Puissance terminal | **23 dBm** (classe 3) | 3GPP, Atoll |
| B10 | Facteur de bruit terminal | 8 dB | Atoll |
| B11 | Gain / pertes terminal | 0 dBi / 0 dB | Atoll |
| B12 | Terminal | catégorie 5, MIMO 2 × 2 | Atoll |
| B13 | Perte de corps | 3 dB en VoIP, 0 dB en données | Atoll |

## 4. Services et seuils radio

| Service (Atoll) | DL max / min | UL max / min |
|---|---|---|
| VoIP | 12,2 / 12,2 kbps | 12,2 / 12,2 kbps |
| Internet mobile | 128 / 64 kbps | 64 / 32 kbps |
| **Internet haut débit** | **1 024** / 0 kbps | **128** / 0 kbps |

| # | Paramètre | Valeur | Source |
|---|---|---|---|
| C1 | **Débit en bord de cellule** | **1 024 kbps DL, 128 kbps UL** = le service « Internet haut débit » d'Atoll, donc vérifiable directement sur les cartes de débit | Atoll + hyp. |
| C2 | Seuils SINR des bearers | bearer 1 : −6,5 dB … **bearer 4 : −1 dB** … bearer 15 : +17,6 dB. Le bearer 4 (QPSK 1/3) est le plus robuste accepté par nos services → **SINR minimal −1 dB** en bord de cellule | Atoll |

## 5. Propagation et marges

| # | Paramètre | Valeur | Source |
|---|---|---|---|
| D1 | Modèle (Étape 1) | **COST-231 Hata** (1 500 – 2 000 MHz) ; Okumura-Hata pour la comparaison à 800 MHz | littérature |
| D2 | Modèle (Atoll) | **Cost-Hata avec diffraction** sur le MNT : même formule que l'Étape 1, plus l'effet du relief | Atoll |
| D3 | Effet de masque σ | **8 dB** urbain, **6 dB** rural (dans Atoll : bâti 8, végétation 7, terrain ouvert 6) | hyp. (valeurs usuelles) |
| D4 | Probabilité de couverture | **95 % de la surface** (formule de Jakes, pente α = 3,52) → marge **8,7 dB** urbain (86,1 % au bord), **5,9 dB** rural (83,5 % au bord) | calcul |
| D5 | Évanouissement rapide | **0 dB** : les seuils SINR des bearers (C2) viennent de courbes qui incluent déjà le canal à évanouissements, la diversité et la retransmission ; Atoll n'en ajoute pas non plus. Avec les 10 dB du cours, le rayon urbain passerait de 0,64 à 0,33 km (≈ 3,7 fois plus de sites) | Cours + justification |
| D6 | Marge d'interférence | **2 dB UL, 3 dB DL** (réseau chargé, K = 1) | hyp. |
| D7 | Pénétration indoor à 1 800 MHz | **15 dB** bâti dense, **10 dB** autres classes | hyp. (valeurs usuelles) |

## 6. Objectifs de couverture

| # | Zone | Objectif |
|---|---|---|
| E1 | Centre urbain | **95 % de la surface en indoor**, débit de bord C1 |
| E2 | Rural | **95 % de la surface en outdoor** |
| E3 | Massif (parc national) | pas d'objectif, pas de site |

## 7. Trafic

| # | Paramètre | Valeur | Source |
|---|---|---|---|
| F1 | Population urbaine | 13 590 habitants | WorldPop 2020 |
| F3 | Pénétration data mobile | **93,9 %** par habitant | INTT |
| F4 | Part de marché | **30 %** : part médiane des trois opérateurs (Ooredoo 43,5 %, Tunisie Télécom 30,4 %, Orange 25,8 %) | INTT |
| F5 | Terminaux LTE | **93 %** (84 % 4G + 9 % 5G) | INTT |
| F6 | Volume mensuel | **9,5 Go / abonné / mois** (6,8 Go fin 2023 : +40 % en 2 ans) | INTT |
| F7 | Heure chargée | 10 % du trafic journalier | hyp. (valeur usuelle) |
| F8 | Répartition DL / UL | 90 % / 10 % | hyp. |
| F10 | Charge maximale d'une cellule | **80 %** à l'heure chargée (équivalent LTE du taux de blocage d'Erlang B) | hyp. |

**Demande urbaine à l'heure chargée :** 13 590 habitants × 93,9 % × 30 % × 93 % ≈ **3 560 abonnés LTE**, × 63,3 kbps en DL par abonné ≈ **225 Mbps**. Détail du calcul dans [`02-dimensionnement/resultats.md`](../02-dimensionnement/resultats.md).

**Lien avec le Monte-Carlo :** un utilisateur actif « Internet haut débit » demande environ 1 Mbps, donc 225 Mbps correspondent à **quelques centaines d'utilisateurs simultanés**. Les charges imposées par le sujet se lisent ainsi : **10** = réseau presque vide, **100** = charge normale, **1 000** = au-delà de l'heure chargée (test de stress).
