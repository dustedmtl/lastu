CREATE TABLE IF NOT EXISTS lemmas (
       lemma VARCHAR(256) NOT NULL,
       pos VARCHAR(16) NOT NULL,
       lemmafreq INTEGER NOT NULL,
       lemmalen INTEGER NOT NULL,
       amblemma FLOAT NOT NULL,
       PRIMARY KEY (lemma, pos)
);

CREATE INDEX IF NOT EXISTS lpos ON lemma(pos);
CREATE INDEX IF NOT EXISTS lfreq ON lemmas(lemmafreq);
CREATE INDEX IF NOT EXISTS llen ON lemmas(lemmalen);
CREATE INDEX IF NOT EXISTS lamb ON lemmas(amblemma);

