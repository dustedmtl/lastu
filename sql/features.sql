CREATE TABLE IF NOT EXISTS derivations (
       lemma VARCHAR(256) NOT NULL,
       form VARCHAR(256) NOT NULL,
       pos VARCHAR(16) NOT NULL,
       feats VARCHAR(256) NOT NULL,
       derivation VARCHAR(256),
       PRIMARY KEY (lemma, form, pos, feats, derivation)
);

CREATE INDEX IF NOT EXISTS derivation ON derivations(derivation);

CREATE TABLE IF NOT EXISTS clitics (
       lemma VARCHAR(256) NOT NULL,
       form VARCHAR(256) NOT NULL,
       pos VARCHAR(16) NOT NULL,
       feats VARCHAR(256) NOT NULL,
       clitic VARCHAR(256),
       PRIMARY KEY (lemma, form, pos, feats, clitic)
);

CREATE INDEX IF NOT EXISTS clitic ON clitics(clitic);
