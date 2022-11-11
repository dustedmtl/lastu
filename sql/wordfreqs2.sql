CREATE TABLE IF NOT EXISTS wordfreqs (
       id INTEGER NOT NULL,
       lemma VARCHAR(256) NOT NULL,
       form VARCHAR(256) NOT NULL,
       pos VARCHAR(16) NOT NULL,
       posx VARCHAR(16) NOT NULL,
       frequency INTEGER NOT NULL,
       feats VARCHAR(256) NOT NULL,
       featid INTEGER NOT NULL,
       PRIMARY KEY (id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_wordfreqs_basic on wordfreqs(lemma, form, pos, feats);
CREATE INDEX IF NOT EXISTS idx_wordfreqs_basic2 on wordfreqs(lemma, form, posx, feats);
--CREATE INDEX IF NOT EXISTS idx_wordfreqs_feats_pos on wordfreqs(feats, pos);
--CREATE INDEX IF NOT EXISTS idx_wordfreqs_feats_posx on wordfreqs(feats, posx);
CREATE INDEX IF NOT EXISTS idx_wordfreqs_featid_lemma on wordfreqs(featid, lemma);
CREATE INDEX IF NOT EXISTS idx_wordfreqs_featid_form on wordfreqs(featid, form);

--CREATE INDEX IF NOT EXISTS wpos ON wordfreqs(pos);
--CREATE INDEX IF NOT EXISTS wform ON wordfreqs(form);
--CREATE INDEX IF NOT EXISTS wfreq ON wordfreqs(frequency);
CREATE INDEX IF NOT EXISTS idx_wordfreqs_freq_lemma ON wordfreqs(frequency DESC, lemma);
CREATE INDEX IF NOT EXISTS idx_wordfreqs_freq_form ON wordfreqs(frequency DESC, form);
CREATE INDEX IF NOT EXISTS idx_wordfreqs_freq_pos ON wordfreqs(frequency DESC, pos);
CREATE INDEX IF NOT EXISTS idx_wordfreqs_freq_posx ON wordfreqs(frequency DESC, posx);

CREATE INDEX IF NOT EXISTS idx_wordfreqs_form_pos ON wordfreqs(form, pos);
CREATE INDEX IF NOT EXISTS idx_wordfreqs_form_posx ON wordfreqs(form, posx);

