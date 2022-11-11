CREATE TABLE IF NOT EXISTS wordfreqs (
       lemma VARCHAR(256) NOT NULL,
       form VARCHAR(256) NOT NULL,
       pos VARCHAR(16) NOT NULL,
       posx VARCHAR(16) NOT NULL,
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
       posspers VARCHAR(16),
       possnum VARCHAR(16),
--       ambform FLOAT,
       PRIMARY KEY (lemma, form, pos, feats)
);

--CREATE INDEX IF NOT EXISTS wpos ON wordfreqs(pos);
CREATE INDEX IF NOT EXISTS wlemma ON wordfreqs(lemma, pos);
CREATE INDEX IF NOT EXISTS wlemmax ON wordfreqs(lemma, posx);
--CREATE INDEX IF NOT EXISTS wlemmap ON wordfreqs(lemma, form, posx);
--CREATE INDEX IF NOT EXISTS wform ON wordfreqs(form);
--CREATE INDEX IF NOT EXISTS wfreq ON wordfreqs(frequency);
CREATE INDEX IF NOT EXISTS wlen ON wordfreqs(len);
CREATE INDEX IF NOT EXISTS wcase ON wordfreqs(nouncase);
--CREATE INDEX IF NOT EXISTS wnumber ON wordfreqs(nnumber);
--CREATE INDEX IF NOT EXISTS wder ON wordfreqs(derivation);
CREATE INDEX IF NOT EXISTS wtense ON wordfreqs(tense);
CREATE INDEX IF NOT EXISTS wperson ON wordfreqs(person);
CREATE INDEX IF NOT EXISTS wverbform ON wordfreqs(verbform);
--CREATE INDEX IF NOT EXISTS wclitic ON wordfreqs(clitic);
CREATE INDEX IF NOT EXISTS wposspers ON wordfreqs(posspers);
CREATE INDEX IF NOT EXISTS wpossnum ON wordfreqs(possnum);
--CREATE INDEX IF NOT EXISTS wamb ON wordfreqs(ambform);

CREATE INDEX IF NOT EXISTS wfreq_pos ON wordfreqs(frequency, pos);
CREATE INDEX IF NOT EXISTS wfreq_posx ON wordfreqs(frequency, posx);
CREATE INDEX IF NOT EXISTS wfreq_form ON wordfreqs(frequency, form);
CREATE INDEX IF NOT EXISTS wfreq_case ON wordfreqs(frequency, nouncase);
CREATE INDEX IF NOT EXISTS wfreq_len ON wordfreqs(frequency, len);
--CREATE INDEX IF NOT EXISTS wfreq_der ON wordfreqs(frequency, derivation);
--CREATE INDEX IF NOT EXISTS wfreq_clitic ON wordfreqs(frequency, clitic);

CREATE INDEX IF NOT EXISTS wform_pos ON wordfreqs(form, pos);
CREATE INDEX IF NOT EXISTS wform_posx ON wordfreqs(form, posx);
CREATE INDEX IF NOT EXISTS wform_len ON wordfreqs(form, len);
CREATE INDEX IF NOT EXISTS wform_case ON wordfreqs(form, nouncase);
--CREATE INDEX IF NOT EXISTS wform_der ON wordfreqs(form, derivation);
--CREATE INDEX IF NOT EXISTS wform_clitic ON wordfreqs(form, clitic);

CREATE INDEX IF NOT EXISTS wform_rev ON wordfreqs(form, revform);
CREATE INDEX IF NOT EXISTS wrev_form ON wordfreqs(revform, form);
--CREATE INDEX IF NOT EXISTS windex_posx ON wordfreqs(lemma, form, posx, feats);

--CREATE INDEX IF NOT EXISTS wform_compounds ON wordfreqs(form, compounds);
