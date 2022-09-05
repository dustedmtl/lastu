CREATE TABLE IF NOT EXISTS wordfreqs (
       lemma VARCHAR(256) NOT NULL,
       form VARCHAR(256) NOT NULL,
       pos VARCHAR(16) NOT NULL,
       frequency INTEGER NOT NULL,
       len INTEGER NOT NULL,
       PRIMARY KEY (lemma, form, pos)
);

CREATE INDEX IF NOT EXISTS wpos ON wordfreqs(pos);
CREATE INDEX IF NOT EXISTS wlemma ON wordfreqs(lemma, form);
CREATE INDEX IF NOT EXISTS wform ON wordfreqs(form);
CREATE INDEX IF NOT EXISTS wfreq ON wordfreqs(frequency);
CREATE INDEX IF NOT EXISTS wlen ON wordfreqs(len);
