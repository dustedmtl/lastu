CREATE TABLE IF NOT EXISTS lemmas (
       lemma VARCHAR(256) NOT NULL,
       pos VARCHAR(16) NOT NULL,
       lemmafreq INTEGER NOT NULL,
       lemmalen INTEGER NOT NULL,
       amblemma FLOAT NOT NULL,
       PRIMARY KEY (lemma, pos)
);

CREATE INDEX IF NOT EXISTS lfreqpos ON lemmas(lemmafreq, pos);
CREATE INDEX IF NOT EXISTS lfreqlemma ON lemmas(lemmafreq, lemma);
CREATE INDEX IF NOT EXISTS lfreqlen ON lemmas(lemmafreq, lemmalen);
CREATE INDEX IF NOT EXISTS lreqamb ON lemmas(lemmafreq, amblemma);

