CREATE TABLE IF NOT EXISTS lemmas (
       lemma VARCHAR(256) NOT NULL,
       pos VARCHAR(16) NOT NULL,
       lemmafreq INTEGER NOT NULL,
       lemmalen INTEGER NOT NULL,
       amblemma FLOAT NOT NULL,
       comparts INTEGER NOT NULL DEFAULT 0,
       PRIMARY KEY (lemma, pos)
);

CREATE INDEX IF NOT EXISTS lemmas_freq_pos ON lemmas(lemmafreq, pos);
CREATE INDEX IF NOT EXISTS lemmas_freq_lemma ON lemmas(lemmafreq, lemma);
CREATE INDEX IF NOT EXISTS lemmas_freq_len ON lemmas(lemmafreq, lemmalen);
CREATE INDEX IF NOT EXISTS lemmas_len_lemma ON lemmas(lemmalen, lemma);
CREATE INDEX IF NOT EXISTS lemmas_freq_amb ON lemmas(lemmafreq, amblemma);

CREATE INDEX IF NOT EXISTS lemmas_comparts ON lemmas(comparts);
