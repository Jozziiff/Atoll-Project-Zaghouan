#!/usr/bin/env bash
# Build the 3 Atoll-ready layers for the Zaghouan study extent (EPSG:32632).
# Run from projet-atoll/:  bash 03-cartes/scripts/make_atoll_maps.sh
set -euo pipefail

RAW=03-cartes/raw
OUT=03-cartes/atoll
rm -rf "$OUT" && mkdir -p "$OUT"
TE="596000 4022000 606000 4032000"   # study extent (m), 10 x 10 km
SRS=EPSG:32632
# Atoll 3.3 TIFF reader is old/strict ("Unsupported bit depth" otherwise):
#  - contiguous layout (PlanarConfiguration=1) → NO "INTERLEAVE=BAND"
#  - no colour palette on the clutter (PhotometricInterpretation=MinIsBlack)
#  - PixelIsArea georeferencing (not PixelIsPoint)
CO="-co COMPRESS=NONE -co INTERLEAVE=PIXEL -co TFW=YES"

# 1) Terrain: Copernicus GLO-30 -> 25 m grid (native ~25 m E-W at 36°N; 25 divides 10 000 → 400x400 px)
gdalwarp -q -overwrite -t_srs $SRS -te $TE -tr 25 25 -r bilinear -ot Float32 \
  "$RAW/Copernicus_DSM_COG_10_N36_00_E010_00_DEM.tif" "$OUT/tmp_dem.tif"
gdal_translate -q -ot Int16 -a_nodata -32768 -mo AREA_OR_POINT=Area $CO "$OUT/tmp_dem.tif" "$OUT/MNT_Zaghouan_25m.tif"

# 2) Land cover: ESA WorldCover 10 m, nearest neighbour (class codes must not be interpolated) → 1000x1000 px
gdalwarp -q -overwrite -t_srs $SRS -te $TE -tr 10 10 -r near -ot Byte \
  "$RAW/ESA_WorldCover_10m_2021_v200_N36E009_Map.tif" "$OUT/tmp_lc.tif"
#    re-write through gdal_calc → plain greyscale Byte, palette dropped, values unchanged
gdal_calc.py --quiet --overwrite -A "$OUT/tmp_lc.tif" --calc="A" --type=Byte --NoDataValue=0 \
  --co COMPRESS=NONE --co INTERLEAVE=PIXEL --co TFW=YES --outfile "$OUT/Clutter_Zaghouan_10m.tif"
# fallback BIL (if Atoll refuses the GeoTIFF clutter)
gdal_translate -q -of EHdr "$OUT/Clutter_Zaghouan_10m.tif" "$OUT/Clutter_Zaghouan_10m_secours.bil"

# 3) Population: WorldPop people/pixel → density (inhabitants/km²), 100 m → 100x100 px.
#    Sum-preserving resampling ("sum"), then x100 (one 100 m pixel = 0.01 km²). Int16 keeps precision as density.
gdalwarp -q -overwrite -t_srs $SRS -te $TE -tr 100 100 -r sum -ot Float32 \
  "$RAW/tun_ppp_2020.tif" "$OUT/tmp_pop.tif"
gdal_calc.py --quiet --overwrite -A "$OUT/tmp_pop.tif" --calc="numpy.round(numpy.maximum(A,0)*100)" \
  --type=Int16 --NoDataValue=none --co COMPRESS=NONE --co INTERLEAVE=PIXEL --co TFW=YES \
  --outfile "$OUT/Population_Zaghouan_100m_densite.tif"

rm -f "$OUT"/tmp_*.tif

# ESRI .prj next to each layer + clutter legend (.mnu: "code<TAB>name")
for f in MNT_Zaghouan_25m Clutter_Zaghouan_10m Clutter_Zaghouan_10m_secours Population_Zaghouan_100m_densite; do
  gdalsrsinfo -o wkt_esri $SRS > "$OUT/$f.prj"
done
printf '10\tArbres\n20\tArbustes\n30\tPrairies\n40\tCultures\n50\tZones_baties\n60\tSol_nu\n80\tEau\n90\tZones_humides\n' \
  | tee "$OUT/Clutter_Zaghouan_10m.mnu" > "$OUT/Clutter_Zaghouan_10m_secours.mnu"

echo "Done → $OUT"
