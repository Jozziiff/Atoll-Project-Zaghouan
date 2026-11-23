# Étape 1: dimensionnement analytique (généré par `calc.py`, ne pas éditer à la main)

## 1. Zone d'étude (E1-2, E1-4)

| Zone | Définition | Surface (km²) | Population (WorldPop 2020) |
|---|---|---|---|
| Centre urbain | densité ≥ 1000 hab/km² | 8.57 | 13,590 |
| Massif / parc (sans objectif) | altitude ≥ 600 m | 14.48 | 292 |
| Rural (objectif outdoor) | le reste | 76.95 | 11,476 |
| Total | 10 × 10 km | 100 | 25,359 |

## 2. Marges (E1-2, E1-3)

Pente de Hata pour h_b = 30 m : 44,9 − 6,55·log h_b = 35.2 dB/décade → **α = 3.52**.

| Zone | σ (dB) | Objectif surface | Proba. en bord de cellule | Marge de masque (dB) |
|---|---|---|---|---|
| urbain | 8 | 95% | 86.1% | 8.7 |
| rural | 6 | 95% | 83.5% | 5.9 |

## 3. Bilan de liaison → rayon de cellule (R-1)

Utilisateur en bord de cellule au bearer 4 (SINR ≥ -1.0 dB) : UL 128 kbps → **2 RB** (82.3 kbps/RB), DL 1024 kbps → **15 RB** (68.6 kbps/RB).

Modèle COST-231 Hata, h_b = 30 m, h_m = 1.5 m, ville moyenne (C_m = 0) : L(1 km) = 135.5 dB à 1720 MHz (UL), 136.3 dB à 1815 MHz (DL).

### Urbain (indoor, antenne tri-secteur)

| UL | valeur | DL | valeur |
|---|---|---|---|
| Puissance UE (dBm) | 23.00 | Puissance eNB par RB (46 dBm / 100 RB) | 26.00 |
| Pertes corporelles (dB) | 0.00 | Gain antenne − pertes (18 − 1 dB) | 17.00 |
| PIRE UE (dBm) | 23.00 | PIRE par RB (dBm) | 43.00 |
| Bruit thermique sur 2 RB + NF eNB 5 dB (dBm) | -113.44 | Bruit thermique sur 1 RB + NF UE 8 dB (dBm) | -113.45 |
| SINR requis, bearer 4 (dB) | -1.00 | SINR requis, bearer 4 (dB) | -1.00 |
| Sensibilité (dBm) | -114.44 | Sensibilité (dBm) | -114.45 |
| Gain antenne eNB − pertes (18 − 1 dB) | 17.00 | Marge de masque (dB) | -8.68 |
| Marge de masque (dB) | -8.68 | Marge d'interférence (dB) | -3.00 |
| Marge d'interférence (dB) | -2.00 | Pertes indoor (dB) | -15.00 |
| Pertes indoor (dB) | -15.00 | Marge d'évanouissement rapide (dB) | 0.00 |
| Marge d'évanouissement rapide (dB) | 0.00 | **MAPL (dB)** | 130.77 |
| **MAPL (dB)** | 128.76 | **Rayon R (km)** | 0.70 |
| **Rayon R (km)** | 0.64 |  |  |

→ Liaison limitante : **UL** (MAPL UL 128.8 dB vs DL 130.8 dB, écart 2.0 dB).

### Rural (outdoor, antenne tri-secteur)

| UL | valeur | DL | valeur |
|---|---|---|---|
| Puissance UE (dBm) | 23.00 | Puissance eNB par RB (46 dBm / 100 RB) | 26.00 |
| Pertes corporelles (dB) | 0.00 | Gain antenne − pertes (18 − 1 dB) | 17.00 |
| PIRE UE (dBm) | 23.00 | PIRE par RB (dBm) | 43.00 |
| Bruit thermique sur 2 RB + NF eNB 5 dB (dBm) | -113.44 | Bruit thermique sur 1 RB + NF UE 8 dB (dBm) | -113.45 |
| SINR requis, bearer 4 (dB) | -1.00 | SINR requis, bearer 4 (dB) | -1.00 |
| Sensibilité (dBm) | -114.44 | Sensibilité (dBm) | -114.45 |
| Gain antenne eNB − pertes (18 − 1 dB) | 17.00 | Marge de masque (dB) | -5.85 |
| Marge de masque (dB) | -5.85 | Marge d'interférence (dB) | -3.00 |
| Marge d'interférence (dB) | -2.00 | Pertes indoor (dB) | 0.00 |
| Pertes indoor (dB) | 0.00 | Marge d'évanouissement rapide (dB) | 0.00 |
| Marge d'évanouissement rapide (dB) | 0.00 | **MAPL (dB)** | 148.59 |
| **MAPL (dB)** | 146.58 | **Rayon R (km)** | 2.23 |
| **Rayon R (km)** | 2.06 |  |  |

→ Liaison limitante : **UL** (MAPL UL 146.6 dB vs DL 148.6 dB, écart 2.0 dB).

**Sensibilité** : avec la marge d'évanouissement du cours (10 dB), R urbain = 0.33 km au lieu de 0.64 km → ×3.7 sites.

## 4. Nombre de sites par la couverture (R-2)

Surface couverte par un site : A_site = k·R² (omni k = 2,6 ; tri-secteur k = 1,95 ; 6 secteurs k = 2,6). Chaque configuration a son propre R car le gain d'antenne change le bilan.

| Configuration | R urbain (km) | Sites urbains | R rural (km) | Sites ruraux | Total |
|---|---|---|---|---|---|
| Omni 11 dBi | 0.41 | 20 | 1.30 | 18 | 38 |
| 3 x 65° 18 dBi | 0.64 | 11 | 2.06 | 10 | 21 |
| 6 x 33° 21 dBi | 0.78 | 6 | 2.51 | 5 | 11 |

## 5. Dimensionnement par la capacité, centre urbain (U-1 … U-5)

### Traduction GSM → LTE

| PDF (logique GSM) | Notre équivalent LTE | Valeur |
|---|---|---|
| U-1 Fréquences par cellule | 1 porteuse de 20 MHz, réutilisation 1 | 100 RB par cellule |
| U-2 Canaux de trafic = total − 2 de signalisation | ressources par RB = total − PDCCH − signaux de référence | DL 120/168 RE (71%), UL 144/168 (86%) |
| U-3 Abonnés par cellule (Erlang B, GoS) | débit cellule × charge max 80% / débit par abonné | 272 abonnés |
| U-4 Cellules = abonnés / abonnés par cellule | idem | 14 cellules |
| U-5 Sites = cellules / 3 | idem (tri-secteur) | **5 sites** |

### Débit moyen d'une cellule

Formule du cours (diapo 31, 6 interféreurs, α = 3.52) appliquée en **chaque point** de la cellule, puis C/I → bearer Atoll (seuils C2) → efficacité. Pire cas du cours (bord, (q−1)) : -12.6 dB ; distribution réelle : 5 % des points sous -1.4 dB, médiane 5.4 dB.

| Grandeur | Valeur |
|---|---|
| Efficacité moyenne (bits/RE) | 1.89 |
| Surface sous le bearer 4 (non servie au débit de service) | 8.4% |
| Surface au-dessus de 12 dB (MIMO possible, non compté → prudent) | 24% |
| Débit moyen cellule DL / UL (Mbps) | 21.6 / 25.9 |

### Demande

| Grandeur | Calcul | Valeur |
|---|---|---|
| Débit heure chargée par abonné | 9.5 Go × 8 / 30 j × 10% / 3600 s | 70.4 kbps (DL 63.3, UL 7.0) |
| Abonnés LTE, centre urbain | 13,590 × 0.939 × 0.3 × 0.93 | 3,560 |
| Demande DL heure chargée, centre | abonnés × débit DL | 225 Mbps |
| Abonnés LTE, hors centre (rural + massif) | 11,769 hab. | 3,083 |

## 6. Nombre final de sites (E1-5, E1-6)

| Zone | Couverture | Capacité | Retenu | Contrainte dimensionnante |
|---|---|---|---|---|
| Centre urbain | 11 | 5 | 11 | couverture indoor |
| Rural | 10 | 4 | 10 | couverture outdoor |
| **Total** |  |  | **21** |  |

## 7. Motif de réutilisation et plan de fréquences (E1-7, E1-8, R-3 … R-5)

Formules du cours : D = √(3K)·R, q = D/R, C/I = (q − 1)^α / 6 (α = 3.52).

| K | (i,j) | q | C/I pire cas (dB) | GSM ≥ 9 dB | LTE ≥ -1.0 dB | MHz par cellule |
|---|---|---|---|---|---|---|
| 1 | 1,0 | 1.73 | -12.6 | non | non | 20.0 |
| 3 | 1,1 | 3.00 | 2.8 | non | oui | 6.7 |
| 4 | 2,0 | 3.46 | 6.0 | non | oui | 5.0 |
| 7 | 2,1 | 4.58 | 11.7 | oui | oui | 2.9 |
| 9 | 3,0 | 5.20 | 14.2 | oui | oui | 2.2 |

**Choix : K = 1** (même porteuse de 20 MHz, EARFCN 1300, sur toutes les cellules). Le pire cas du cours dit K = 3, mais il place les 6 interféreurs au plus près en même temps ; la distribution réelle (section 5) montre seulement 8% de la surface sous le seuil, et K = 1 donne 3× plus de spectre par cellule. Le bord de cellule est géré par l'ordonnanceur, le tilt et l'azimut (Étape 2).

| R-4 / R-5 | Valeur |
|---|---|
| Porteuses disponibles | 1 × 20 MHz (bande 3, par opérateur) |
| Canaux par porteuse | 100 RB |
| Fréquences par site | 1 porteuse, réutilisée sur les 3 secteurs |
| Allocation (LTE) | même fréquence partout ; on planifie les **PCI** : site s → PCI 3s, 3s+1, 3s+2 (les 3 secteurs d'un site ont des PCI mod 3 différents) |

## 8. Pourquoi 1800 et pas 800 ?

Mêmes marges, mêmes antennes, même puissance par RB : seuls le modèle (Okumura-Hata à 800) et la largeur de bande changent. Hypothèse prudente pour 800 : même perte indoor (en réalité plus faible).

| Bande | R urbain (km) | R rural (km) | Sites couverture | Sites capacité (centre) | Total aujourd'hui | Sites capacité dans 5 ans (×2.3) | Total dans 5 ans |
|---|---|---|---|---|---|---|---|
| 800 MHz, 10 MHz | 1.22 | 3.91 | 6 | 9 | 12 | 21 | 24 |
| 1800 MHz, 20 MHz | 0.64 | 2.06 | 21 | 5 | 21 | 11 | 21 |

