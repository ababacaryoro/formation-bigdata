-- Formation Big Data — ANSD / Data Innovation Lab
-- Module 09 — table de restitution et données de démonstration.
--
-- Ce script s'exécute UNE SEULE FOIS, au tout premier démarrage de PostgreSQL,
-- sur un répertoire de données vide. Si vous le modifiez, il faut recréer le
-- volume :   docker compose down -v && docker compose up -d
--
-- Il reproduit ce que produirait le DAG Airflow : des effectifs d'actes d'état
-- civil, par jour, par région et par type.

CREATE TABLE IF NOT EXISTS agregats_actes (
    jour        DATE,
    region      TEXT,
    type_acte   TEXT,
    effectif    BIGINT,
    calcule_le  TIMESTAMP DEFAULT now()
);

-- Quatorze régions × trois types d'actes × quatorze jours = 588 lignes.
-- Tous les types sont explicites : on évite ainsi tout mélange entre
-- « numeric » et « double precision », que PostgreSQL n'apprécie pas toujours.
INSERT INTO agregats_actes (jour, region, type_acte, effectif, calcule_le)
SELECT
    serie.jour,
    r.region,
    t.type_acte,
    GREATEST(
        1,
        CAST(
            ROUND(
                CAST(r.poids AS float8)
                * CAST(t.part AS float8)
                * CAST(2600 AS float8)
                -- variation aléatoire d'un jour à l'autre
                * (CAST(0.82 AS float8) + random() * CAST(0.36 AS float8))
                -- légère progression au fil de la quinzaine
                * (CAST(1 AS float8)
                   + CAST(0.012 AS float8)
                     * CAST(serie.jour - (CURRENT_DATE - 13) AS float8))
            ) AS bigint
        )
    ) AS effectif,
    now() AS calcule_le
FROM (
    SELECT CAST(gs AS date) AS jour
    FROM generate_series(
        CAST(CURRENT_DATE - 13 AS timestamp),
        CAST(CURRENT_DATE AS timestamp),
        interval '1 day'
    ) AS gs
) AS serie
CROSS JOIN (VALUES
    ('Dakar',       0.230), ('Thiès',       0.130), ('Diourbel',    0.110),
    ('Kaolack',     0.072), ('Saint-Louis', 0.065), ('Louga',       0.060),
    ('Fatick',      0.055), ('Kolda',       0.050), ('Tambacounda', 0.050),
    ('Ziguinchor',  0.043), ('Matam',       0.042), ('Kaffrine',    0.040),
    ('Sédhiou',     0.035), ('Kédougou',    0.018)
) AS r(region, poids)
CROSS JOIN (VALUES
    ('naissance', 0.72), ('mariage', 0.12), ('deces', 0.16)
) AS t(type_acte, part);

-- Un index sur les colonnes les plus filtrées
CREATE INDEX IF NOT EXISTS idx_agregats_jour   ON agregats_actes (jour);
CREATE INDEX IF NOT EXISTS idx_agregats_region ON agregats_actes (region);

-- Contrôle, visible dans les journaux du conteneur au premier démarrage
DO $$
DECLARE n bigint;
BEGIN
    SELECT COUNT(*) INTO n FROM agregats_actes;
    RAISE NOTICE 'Table agregats_actes initialisée : % lignes', n;
END $$;
