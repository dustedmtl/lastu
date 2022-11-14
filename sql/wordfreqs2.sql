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
CREATE INDEX IF NOT EXISTS idx_wordfreqs_basic2 on wordfreqs(lemma, form, posx, feats);
CREATE INDEX IF NOT EXISTS idx_wordfreqs_feats_pos on wordfreqs(feats, pos);
CREATE INDEX IF NOT EXISTS idx_wordfreqs_feats_posx on wordfreqs(feats, posx);
CREATE INDEX IF NOT EXISTS idx_wordfreqs_featid_lemma on wordfreqs(featid, lemma);
CREATE INDEX IF NOT EXISTS idx_wordfreqs_featid_form on wordfreqs(featid, form);

--CREATE INDEX IF NOT EXISTS wpos ON wordfreqs(pos);
--CREATE INDEX IF NOT EXISTS wform ON wordfreqs(form);
--CREATE INDEX IF NOT EXISTS wfreq ON wordfreqs(frequency);
CREATE INDEX IF NOT EXISTS idx_wordfreqs_freq_lemma ON wordfreqs(frequency DESC, lemma);
CREATE INDEX IF NOT EXISTS idx_wordfreqs_freq_form ON wordfreqs(frequency DESC, form);
CREATE INDEX IF NOT EXISTS idx_wordfreqs_freq_revform ON wordfreqs(frequency DESC, revform);
CREATE INDEX IF NOT EXISTS idx_wordfreqs_freq_pos ON wordfreqs(frequency DESC, pos);
CREATE INDEX IF NOT EXISTS idx_wordfreqs_freq_len ON wordfreqs(frequency DESC, len);

CREATE INDEX IF NOT EXISTS idx_wordfreqs_freqx_lemma ON wordfreqs(frequencyx DESC, lemma);
CREATE INDEX IF NOT EXISTS idx_wordfreqs_freqx_form ON wordfreqs(frequencyx DESC, form);
CREATE INDEX IF NOT EXISTS idx_wordfreqs_freqx_revform ON wordfreqs(frequencyx DESC, revform);
CREATE INDEX IF NOT EXISTS idx_wordfreqs_freqx_posx ON wordfreqs(frequencyx DESC, posx);
CREATE INDEX IF NOT EXISTS idx_wordfreqs_freqx_len ON wordfreqs(frequency DESC, len);

CREATE INDEX IF NOT EXISTS idx_wordfreqs_form_pos ON wordfreqs(form, pos);
CREATE INDEX IF NOT EXISTS idx_wordfreqs_form_posx ON wordfreqs(form, posx);
CREATE INDEX IF NOT EXISTS idx_wordfreqs_form_freq ON wordfreqs(form, frequency);
CREATE INDEX IF NOT EXISTS idx_wordfreqs_form_freqx ON wordfreqs(form, frequencyx);

CREATE INDEX IF NOT EXISTS idx_wordfreqs_form_rev ON wordfreqs(form, revform);
CREATE INDEX IF NOT EXISTS idx_wordfreqs_rev_form ON wordfreqs(revform, form);
