#!/bin/bash
# Initialisation de Superset au premier démarrage.
#
# Les trois commandes sont sans effet si elles ont déjà été exécutées :
# le script peut donc être rejoué sans dommage.
pip install --no-cache-dir psycopg2-binary
set -e

echo "→ Mise à niveau de la base de métadonnées"
superset db upgrade

echo "→ Création du compte administrateur"
superset fab create-admin \
    --username "${ADMIN_USERNAME}" \
    --firstname Admin --lastname ANSD \
    --email admin@ansd.sn \
    --password "${ADMIN_PASSWORD}" || true

echo "→ Initialisation des rôles et permissions"
superset init

echo "→ Superset démarre sur le port 8088"
exec superset run -h 0.0.0.0 -p 8088 --with-threads
