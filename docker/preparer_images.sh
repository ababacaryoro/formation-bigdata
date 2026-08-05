#!/usr/bin/env bash
# Formation Big Data — ANSD / Data Innovation Lab
# PRÉPARATION DES IMAGES — à exécuter sur une machine connectée.
#
# Sous Windows : exécuter depuis Git Bash, non depuis PowerShell : 
# Se positionner dans le dossier docker, puis :
#     bash ./preparer_images.sh
#
# Objectif : éviter que trente postes téléchargent plusieurs gigaoctets derrière
# le pare-feu. Les images sont construites et exportées ici, puis
# distribuées par clé USB et chargées sur chaque poste avec :
#
#     docker load -i images_pipeline_formation_big_data.tar
#
# ═══════════════════════════════════════════════════════════════════════════
#  ARCHITECTURE — LE POINT À NE PAS MANQUER
#
#  Les postes des participants sont des PC Windows, donc en architecture
#  amd64. Si vous préparez l'archive depuis un Mac Apple Silicon (M1 à M4),
#  Docker produirait par défaut des images arm64, QUI NE DÉMARRERONT PAS sur
#  leurs machines.
#
#  Ce script force donc explicitement linux/amd64.
#
#  Conséquence sur un Mac Apple Silicon : la construction passe par une
#  émulation (Rosetta), donc elle est plus lente — comptez le double. C'est un
#  coût ponctuel.
#
#  Pour vos propres démonstrations, vous pouvez garder en parallèle des images
#  natives arm64 : il suffit de relancer un `docker pull` sans l'option
#  --platform, en dehors de ce script.
# ═══════════════════════════════════════════════════════════════════════════
set -euo pipefail

ARCHIVE="./images_pipeline_formation_big_data.tar"
PLATEFORME="linux/amd64"        # architecture des postes Windows

IMAGES_A_TELECHARGER=(
  # Modules 04 et 05
  "python:3.12-slim"
  "postgres:16"
  "mongo:7"
  "mongo-express:1"
  # Socle des projets
  "apache/kafka:4.0.0"
  "provectuslabs/kafka-ui:latest"
  "apache/airflow:3.3.0"
  "apache/superset:4.1.1"
  # Base de l'image Spark
  "apache/spark:4.1.2-scala2.13-java17-python3-ubuntu"
)

echo "════════════════════════════════════════════════════════════"
echo " 1/4 — Téléchargement des images officielles"
echo "════════════════════════════════════════════════════════════"
echo ""
echo " Deux causes d'échec à distinguer :"
echo "   « 502 Bad Gateway »   → panne passagère de Docker Hub, relancez"
echo "   « manifest unknown »  → la version n'existe plus ; vérifiez les"
echo "                           étiquettes disponibles sur hub.docker.com"
echo ""

echecs=()
for image in "${IMAGES_A_TELECHARGER[@]}"; do
  echo "  → $image"
  # Trois tentatives : les erreurs 502 sont fréquentes et passagères
  for essai in 1 2 3; do
    if docker pull --platform "$PLATEFORME" "$image"; then
      break
    fi
    if [ "$essai" -lt 3 ]; then
      echo "     échec (tentative $essai/3), nouvelle tentative dans 10 s…"
      sleep 10
    else
      echecs+=("$image")
    fi
  done
done

if [ ${#echecs[@]} -gt 0 ]; then
  echo
  echo " Images non téléchargées :"
  printf '   - %s\n' "${echecs[@]}"
  echo " Corrigez la liste avant de poursuivre."
  exit 1
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo " 2/4 — Construction de l'image Jupyter (modules 04 et 05)"
echo "════════════════════════════════════════════════════════════"
docker build --platform "$PLATEFORME" \
    -f ./Dockerfile.jupyter -t formation-jupyter:1.0 .

echo ""
echo "════════════════════════════════════════════════════════════"
echo " 3/4 — Construction de l'image Spark avec connecteurs"
echo "════════════════════════════════════════════════════════════"
echo " Cette étape télécharge les connecteurs Kafka, MongoDB et PostgreSQL"
echo " ainsi que TOUTES leurs dépendances transitives, et les fige dans"
echo " l'image. C'est l'étape critique : sans elle, Spark tenterait de les"
echo " télécharger le jour de la formation."
echo ""
docker build --platform "$PLATEFORME" \
    -f ./Dockerfile.spark -t formation-spark:1.0 .

echo ""
echo "════════════════════════════════════════════════════════════"
echo " Contrôle d'architecture avant export"
echo "════════════════════════════════════════════════════════════"
mauvaises=0
for image in "${IMAGES_A_TELECHARGER[@]}" formation-jupyter:1.0 formation-spark:1.0; do
  arch=$(docker image inspect --format '{{.Architecture}}' "$image")
  if [ "$arch" = "amd64" ]; then
    echo "  ✔ $image ($arch)"
  else
    echo "  ✘ $image ($arch) — NE DÉMARRERA PAS sur Windows"
    mauvaises=$((mauvaises + 1))
  fi
done
if [ "$mauvaises" -gt 0 ]; then
  echo ""
  echo " $mauvaises image(s) dans la mauvaise architecture. Export annulé."
  echo " Supprimez-les (docker rmi) et relancez ce script."
  exit 1
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo " 4/4 — Export vers $ARCHIVE"
echo "════════════════════════════════════════════════════════════"
docker save -o "$ARCHIVE" \
  "${IMAGES_A_TELECHARGER[@]}" \
  formation-jupyter:1.0 \
  formation-spark:1.0

echo ""
echo "Terminé : $(du -h "$ARCHIVE" | cut -f1)"
echo ""
echo "Étapes suivantes :"
echo "  1. Lancer le test hors ligne :   ./tester_hors_ligne.sh"
echo "  2. Copier $ARCHIVE sur clé USB"
echo "  3. Sur chaque poste :            docker load -i $ARCHIVE"
