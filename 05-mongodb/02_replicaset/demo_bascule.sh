#!/usr/bin/env bash
# Démonstration : on arrête le primaire, les survivants en élisent un nouveau.

# Sous Windows : exécuter depuis Git Bash (clic droit dans le dossier →
# « Git Bash Here »), et non depuis PowerShell ni l'invite de commandes.

set -euo pipefail

primaire() {
  for c in rs_mongo1 rs_mongo2 rs_mongo3; do
    if docker exec "$c" mongosh --quiet --eval 'rs.isMaster().ismaster' 2>/dev/null | grep -q true; then
      echo "$c"; return
    fi
  done
  echo "aucun"
}

echo "→ Primaire actuel : $(primaire)"
echo
echo "→ État initial"
docker exec rs_mongo2 mongosh --quiet --eval \
  'rs.status().members.forEach(m => print("   " + m.name.padEnd(16) + " " + m.stateStr))'

ACTUEL=$(primaire)
echo
echo "→ Arrêt du primaire ($ACTUEL) — simulation d'une panne serveur"
docker stop "$ACTUEL" >/dev/null

echo "→ Élection en cours…"
for i in $(seq 1 30); do
  sleep 2
  NOUVEAU=$(primaire)
  if [ "$NOUVEAU" != "aucun" ] && [ "$NOUVEAU" != "$ACTUEL" ]; then
    echo "   Nouveau primaire élu après ~$((i * 2)) s : $NOUVEAU"
    break
  fi
done

echo
echo "→ Les données sont-elles toujours accessibles ?"
docker exec "$NOUVEAU" mongosh --quiet --eval \
  'db = db.getSiblingDB("demo"); print("   Documents lisibles : " + db.actes.countDocuments())'

echo
echo "→ Redémarrage du serveur tombé"
docker start "$ACTUEL" >/dev/null
sleep 10
docker exec "$NOUVEAU" mongosh --quiet --eval \
  'rs.status().members.forEach(m => print("   " + m.name.padEnd(16) + " " + m.stateStr))'
echo
echo "Le serveur revenu redevient secondaire et se resynchronise."
