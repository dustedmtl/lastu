CREATE TABLE IF NOT EXISTS features (
       featid INTEGER NOT NULL,
       feats VARCHAR(256) NOT NULL,
       pos VARCHAR(16) NOT NULL,
       nouncase VARCHAR(16),
       nnumber VARCHAR(16),
--       gender VARCHAR(16),
--       definite VARCHAR(16),
       mood VARCHAR(16),
       tense VARCHAR(16),
--       aspect VARCHAR(16),
       voice VARCHAR(16),
       person VARCHAR(16),
       verbform VARCHAR(16),
--       partform VARCHAR(16),
       clitic VARCHAR(16),
       derivation VARCHAR(256),
       posspers VARCHAR(16),
       possnum VARCHAR(16),
       PRIMARY KEY (featid)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_features_feats_pos ON features(feats, pos);
CREATE INDEX IF NOT EXISTS idx_features_case ON features(nouncase);
CREATE INDEX IF NOT EXISTS idx_features_posspers ON features(posspers);
CREATE INDEX IF NOT EXISTS idx_features_nnumber ON features(nnumber);
CREATE INDEX IF NOT EXISTS idx_features_clitic ON features(clitic);
CREATE INDEX IF NOT EXISTS idx_features_derivation ON features(derivation);
--CREATE INDEX IF NOT EXISTS idx_features_basic2 ON features(feats, nouncase);
--CREATE INDEX IF NOT EXISTS idx_features_case1 ON features(nouncase, feats, pos);
--CREATE INDEX IF NOT EXISTS idx_features_case2 ON features(nouncase, feats, posx);
--CREATE INDEX IF NOT EXISTS idx_features_number1 ON features(nnumber, feats, pos);
--CREATE INDEX IF NOT EXISTS idx_features_number2 ON features(nnumber, feats, posx);

--CREATE INDEX IF NOT EXISTS wnumber ON wordfreqs(nnumber);
--CREATE INDEX IF NOT EXISTS wder ON wordfreqs(derivation);
--CREATE INDEX IF NOT EXISTS wtense ON wordfreqs(tense);
--CREATE INDEX IF NOT EXISTS wperson ON wordfreqs(person);
--CREATE INDEX IF NOT EXISTS wverbform ON wordfreqs(verbform);
--CREATE INDEX IF NOT EXISTS wclitic ON wordfreqs(clitic);
--CREATE INDEX IF NOT EXISTS wposspers ON wordfreqs(posspers);
--CREATE INDEX IF NOT EXISTS wpossnum ON wordfreqs(possnum);
--CREATE INDEX IF NOT EXISTS wamb ON wordfreqs(ambform);


CREATE TABLE IF NOT EXISTS derivations (
       featid INTEGER NOT NULL,
       derivation VARCHAR(256),
       PRIMARY KEY (featid, derivation)
);

CREATE INDEX IF NOT EXISTS derivation ON derivations(derivation);

CREATE TABLE IF NOT EXISTS clitics (
       featid INTEGER NOT NULL,
       clitic VARCHAR(256),
       PRIMARY KEY (featid, clitic)
);

CREATE INDEX IF NOT EXISTS clitic ON clitics(clitic);

CREATE TABLE IF NOT EXISTS nouncases (
       featid INTEGER NOT NULL,
       nouncase VARCHAR(256),
       PRIMARY KEY (featid, nouncase)
);

CREATE INDEX IF NOT EXISTS nouncase ON nouncases(nouncase);

