#!/usr/bin/env bash
# Préparation hors ligne des images — À EXÉCUTER AVANT LA FORMATION
#
# Objectif : éviter que trente postes téléchargent simultanément plusieurs
# gigaoctets derrière un parefeu. Les images sont exportées dans une
# archive, distribuée par clé USB, puis chargées sur chaque poste.
#
#   Sur votre machine :   ./preparer_images.sh
#   Sur chaque poste :    docker load -i images_formation.tar
set -euo pipefail

IMAGES=(
  "python:3.12-slim"      # module 04 — base et image Jupyter
  "postgres:16"           # module 04
  "mongo:7"               # module 05
  "mongo-express:1"       # module 05
)

echo "→ Téléchargement des images"
for image in "${IMAGES[@]}"; do
  echo "   $image"
  docker pull "$image"
done

echo "→ Construction de l'image Jupyter de la formation"
docker build -t formation-jupyter:1.0 .

echo "→ Export vers images_formation.tar"
docker save -o images_formation.tar "${IMAGES[@]}" formation-jupyter:1.0

echo
echo "Terminé : $(du -h images_formation.tar | cut -f1)"
echo "Copiez cette archive sur clé USB, puis sur chaque poste :"
echo "    docker load -i images_formation.tar"
