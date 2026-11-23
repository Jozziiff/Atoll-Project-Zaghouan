# Cartes de la zone (import dans Atoll)

Les trois couches dont Atoll a besoin, découpées sur notre zone de 10 × 10 km et mises au format accepté par Atoll 3.3.
Toutes en UTM 32N (EPSG:32632), origine (596 000, 4 032 000).

## Sources (données ouvertes)

| Couche | Fichier brut | Source | Résolution |
|---|---|---|---|
| Relief | `Copernicus_DSM_COG_10_N36_00_E010_00_DEM.tif` | Copernicus DEM GLO-30 (ESA) | ≈ 30 m |
| Occupation du sol | `ESA_WorldCover_10m_2021_v200_N36E009_Map.tif` | ESA WorldCover 2021 v200 | 10 m |
| Population | `tun_ppp_2020.tif` | WorldPop 2020 (habitants par pixel) | ≈ 100 m |
| Image satellite (présentation 3D seulement) | `s2cloudless/` | Sentinel-2 cloudless 2021, EOX (CC BY 4.0), voir [`raw/s2cloudless/SOURCE.txt`](raw/s2cloudless/SOURCE.txt) | 10 m |

Les fichiers bruts (≈ 175 Mo) ne sont pas dans le dépôt : ils se téléchargent gratuitement aux sources ci-dessus, à placer dans `03-cartes/raw/`.

## Couches prêtes pour Atoll (`atoll/`)

| Fichier | Grille | Valeurs | Import dans Atoll |
|---|---|---|---|
| `MNT_Zaghouan_25m.tif` | 400 × 400, 25 m | altitude 101 – 1 238 m | Altitudes (MNT) |
| `Clutter_Zaghouan_10m.tif` (+ légende `.mnu`) | 1 000 × 1 000, 10 m | classes WorldCover 10 … 90 | Classes d'occupation du sol |
| `Clutter_Zaghouan_10m_secours.bil` | idem | idem | format de secours si le GeoTIFF est refusé |
| `Population_Zaghouan_100m_densite.tif` | 100 × 100, 100 m | **densité** en hab/km², 13 – 3 080 | Population (en densité) |

Total de population sur la zone : **≈ 25 360 habitants**.

## Fabrication

```bash
bash 03-cartes/scripts/make_atoll_maps.sh   # découpe, reprojection, format Atoll → 03-cartes/atoll/
python3 03-cartes/scripts/preview.py        # aperçu 20 × 20 km → 03-cartes/preview/
```

Points d'attention rencontrés :

- **Format :** le lecteur TIFF d'Atoll 3.3 est strict (« Unsupported bit depth ») : entiers 16 bits ou octets, sans compression, pixels contigus, pas de palette, fichier `.tfw` à côté.
- **Population :** un raster d'habitants par pixel doit être ré-échantillonné en **somme**, jamais au plus proche voisin (qui sous-compte). Dans Atoll, la carte doit être importée **en densité** (hab/km²) : importée comme « nombre par pixel », la population apparaissait 100 fois trop grande.
- **Relief :** Copernicus GLO-30 plutôt que SRTM : plus récent (TanDEM-X 2011 – 2015) et plus précis.
