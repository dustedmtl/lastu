
CREATE UNIQUE INDEX IF NOT EXISTS idx_wordfreqs_basic on wordfreqs(lemma, form, pos, feats);
CREATE INDEX IF NOT EXISTS idx_wordfreqs_basic2 on wordfreqs(lemma, form, posx, feats);
--CREATE INDEX IF NOT EXISTS idx_wordfreqs_featid_lemma on wordfreqs(featid, lemma);
--CREATE INDEX IF NOT EXISTS idx_wordfreqs_featid_form on wordfreqs(featid, form);

--CREATE INDEX IF NOT EXISTS wpos ON wordfreqs(pos);
--CREATE INDEX IF NOT EXISTS wform ON wordfreqs(form);
--CREATE INDEX IF NOT EXISTS wfreq ON wordfreqs(frequency);
CREATE INDEX IF NOT EXISTS idx_wordfreqs_freq_lemma ON wordfreqs(frequency DESC, lemma);
CREATE INDEX IF NOT EXISTS idx_wordfreqs_freq_form ON wordfreqs(frequency DESC, form);
CREATE INDEX IF NOT EXISTS idx_wordfreqs_freq_revform ON wordfreqs(frequency DESC, revform);
--CREATE INDEX IF NOT EXISTS idx_wordfreqs_freq_pos ON wordfreqs(frequency DESC, pos);
CREATE INDEX IF NOT EXISTS idx_wordfreqs_freq_len ON wordfreqs(frequency DESC, len DESC);

CREATE INDEX IF NOT EXISTS idx_wordfreqs_freqx_lemma ON wordfreqs(frequencyx DESC, lemma);
CREATE INDEX IF NOT EXISTS idx_wordfreqs_freqx_form ON wordfreqs(frequencyx DESC, form);
CREATE INDEX IF NOT EXISTS idx_wordfreqs_freqx_revform ON wordfreqs(frequencyx DESC, revform);
--CREATE INDEX IF NOT EXISTS idx_wordfreqs_freqx_posx ON wordfreqs(frequencyx DESC, posx);
CREATE INDEX IF NOT EXISTS idx_wordfreqs_freqx_len ON wordfreqs(frequencyx DESC, len DESC);

CREATE INDEX IF NOT EXISTS idx_wordfreqs_form_pos ON wordfreqs(form, pos);
CREATE INDEX IF NOT EXISTS idx_wordfreqs_form_posx ON wordfreqs(form, posx);
CREATE INDEX IF NOT EXISTS idx_wordfreqs_form_freq ON wordfreqs(form, frequency DESC);
CREATE INDEX IF NOT EXISTS idx_wordfreqs_form_freqx ON wordfreqs(form, frequencyx DESC);

CREATE INDEX IF NOT EXISTS idx_wordfreqs_revform_freq ON wordfreqs(revform, frequency DESC);
CREATE INDEX IF NOT EXISTS idx_wordfreqs_revform_freqx ON wordfreqs(revform, frequencyx DESC);

CREATE INDEX IF NOT EXISTS idx_wordfreqs_form_rev ON wordfreqs(form, revform);
CREATE INDEX IF NOT EXISTS idx_wordfreqs_rev_form ON wordfreqs(revform, form);

-- Indexes necessary to database building
CREATE INDEX IF NOT EXISTS idx_wordfreqs_feats_pos on wordfreqs(feats, pos);
--CREATE INDEX IF NOT EXISTS idx_wordfreqs_featid on wordfreqs(featid);
--CREATE INDEX IF NOT EXISTS idx_wordfreqs_feats_pos_featid_partial on wordfreqs(feats, pos, featid) where featid = 0;
--CREATE INDEX IF NOT EXISTS idx_wordfreqs_lemma_posx on wordfreqs(lemma, posx);
CREATE INDEX IF NOT EXISTS idx_wordfreqs_lemma_posx_freq on wordfreqs(lemma, posx, frequency DESC);
