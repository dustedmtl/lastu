CREATE TABLE IF NOT EXISTS wordfreqs (
       lemma VARCHAR(256) NOT NULL,
       form VARCHAR(256) NOT NULL,
       pos VARCHAR(16) NOT NULL,
       frequency INTEGER NOT NULL,
       len INTEGER NOT NULL,
       feats VARCHAR(256) NOT NULL,
       nouncase VARCHAR(16),
       nnumber VARCHAR(16),
       derivation VARCHAR(256),
       tense VARCHAR(16),
       person VARCHAR(16),
       verbform VARCHAR(16),
       clitic VARCHAR(16),
       PRIMARY KEY (lemma, form, pos, feats)
);

CREATE INDEX IF NOT EXISTS wpos ON wordfreqs(pos);
CREATE INDEX IF NOT EXISTS wlemma ON wordfreqs(lemma, form, pos);
CREATE INDEX IF NOT EXISTS wform ON wordfreqs(form);
CREATE INDEX IF NOT EXISTS wfreq ON wordfreqs(frequency);
CREATE INDEX IF NOT EXISTS wlen ON wordfreqs(len);
CREATE INDEX IF NOT EXISTS wcase ON wordfreqs(nouncase);
CREATE INDEX IF NOT EXISTS wnumber ON wordfreqs(nnumber);
CREATE INDEX IF NOT EXISTS wder ON wordfreqs(derivation);
CREATE INDEX IF NOT EXISTS wtense ON wordfreqs(tense);
CREATE INDEX IF NOT EXISTS wperson ON wordfreqs(person);
CREATE INDEX IF NOT EXISTS wverbform ON wordfreqs(verbform);

CREATE TABLE IF NOT EXISTS wordfeats (
       lemma VARCHAR(256) NOT NULL,
       form VARCHAR(256) NOT NULL,
       pos VARCHAR(16) NOT NULL,
       frequency INTEGER NOT NULL,
       feats VARCHAR(256) NOT NULL,
       PRIMARY KEY (lemma, form, pos, feats)
);

CREATE INDEX IF NOT EXISTS w2pos ON wordfeats(pos);
CREATE INDEX IF NOT EXISTS w2lemma ON wordfeats(lemma, form, pos);
CREATE INDEX IF NOT EXISTS w2form ON wordfeats(form);
CREATE INDEX IF NOT EXISTS w2freq ON wordfeats(frequency);
