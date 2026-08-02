#!/usr/bin/env bash
# Initialise le jeu de réplicas et y insère quelques documents de démonstration.
#
# Sous Windows : exécuter depuis Git Bash (clic droit dans le dossier →
# « Git Bash Here »), et non depuis PowerShell ni l'invite de commandes.

set -euo pipefail

echo "→ Attente du démarrage des trois serveurs"
sleep 5

echo "→ Initialisation du jeu de réplicas rsANSD"
docker exec rs_mongo1 mongosh --quiet --eval '
  rs.initiate({
    _id: "rsANSD",
    members: [
      { _id: 0, host: "mongo1:27017", priority: 3 },
      { _id: 1, host: "mongo2:27017", priority: 2 },
      { _id: 2, host: "mongo3:27017", priority: 1 }
    ]
  })
'

echo "→ Attente de l'élection du primaire"
for _ in $(seq 1 30); do
  if docker exec rs_mongo1 mongosh --quiet --eval 'rs.isMaster().ismaster' 2>/dev/null | grep -q true; then
    break
  fi
  sleep 2
done

echo "→ Insertion de documents de démonstration"
docker exec rs_mongo1 mongosh --quiet --eval '
  db = db.getSiblingDB("demo");
  db.actes.insertMany([
    { numero: "NAI-DK-2026-001", region: "Dakar",   type: "naissance" },
    { numero: "NAI-TH-2026-002", region: "Thiès",   type: "naissance" },
    { numero: "MAR-SL-2026-003", region: "Saint-Louis", type: "mariage" }
  ]);
  print("Documents insérés : " + db.actes.countDocuments());
'

echo
echo "→ État du jeu de réplicas"
docker exec rs_mongo1 mongosh --quiet --eval '
  rs.status().members.forEach(m =>
    print("   " + m.name.padEnd(16) + " " + m.stateStr))
'
