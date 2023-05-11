CREATE TABLE IF NOT EXISTS wordfreqs (
       id INTEGER NOT NULL,
       lemma VARCHAR(256) NOT NULL,
       form VARCHAR(256) NOT NULL,
       pos VARCHAR(16) NOT NULL,
       posx VARCHAR(16) NOT NULL,
       len INTEGER NOT NULL DEFAULT 0,
       frequency INTEGER NOT NULL,
       frequencyx INTEGER NOT NULL DEFAULT 0,
       feats VARCHAR(256) NOT NULL,
       featid INTEGER NOT NULL,
       hood INTEGER NOT NULL DEFAULT 0,
       revform VARCHAR(256) NOT NULL DEFAULT '',
       ambform FLOAT NOT NULL DEFAULT 0,
       PRIMARY KEY (id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_wordfreqs_basic on wordfreqs(lemma, form, pos, feats);

CREATE TABLE IF NOT EXISTS metadata (
       key VARCHAR(16) NOT NULL,
       value VARCHAR(16) NOT NULL,
       PRIMARY KEY (key)
);
