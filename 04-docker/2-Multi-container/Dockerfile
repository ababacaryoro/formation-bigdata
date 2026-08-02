# Formation Big Data — ANSD / Data Innovation Lab
# Image de travail : JupyterLab + le nécessaire pour interroger PostgreSQL.
#
# Quatre instructions suffisent. Vous construirez votre propre image sur ce
# modèle au jour 5, pour containeriser le script de votre projet.

FROM python:3.12-slim

# 1. Les bibliothèques dont nous avons besoin
RUN pip install --no-cache-dir \
        jupyterlab==4.* \
        pandas \
        sqlalchemy \
        psycopg2-binary

# 2. Le dossier de travail à l'intérieur du conteneur
WORKDIR /home/travail

# 3. Le port sur lequel JupyterLab écoute
EXPOSE 8888

# 4. La commande lancée au démarrage du conteneur
CMD ["jupyter", "lab", \
     "--ip=0.0.0.0", \
     "--port=8888", \
     "--no-browser", \
     "--allow-root", \
     "--IdentityProvider.token=formation", \
     "--ServerApp.root_dir=/home/travail"]
