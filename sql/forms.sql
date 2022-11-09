CREATE TABLE IF NOT EXISTS forms (
       form VARCHAR(256) NOT NULL,
       frequency INTEGER NOT NULL,
       numforms INTEGER NOT NULL,
       hood INTEGER NOT NULL,
       PRIMARY KEY (form)
);

CREATE INDEX IF NOT EXISTS ffreq ON forms(form, frequency);
CREATE INDEX IF NOT EXISTS fnumforms ON forms(form, numforms);
CREATE INDEX IF NOT EXISTS fhood ON forms(form, hood);

CREATE TABLE IF NOT EXISTS lemmaforms (
       lemma VARCHAR(256) NOT NULL,
       form VARCHAR(256) NOT NULL,
       pos VARCHAR(256) NOT NULL,
       frequency INTEGER NOT NULL,
       formpct FLOAT NOT NULL,
       formsum INTEGER NOT NULL,
       PRIMARY KEY (lemma, form, pos)
);

CREATE INDEX IF NOT EXISTS lffreq ON lemmaforms(lemma, form, frequency);
CREATE INDEX IF NOT EXISTS lfrom ON lemmaforms(form, frequency);
