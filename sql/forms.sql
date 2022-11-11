CREATE TABLE IF NOT EXISTS forms (
       form VARCHAR(256) NOT NULL,
       frequency INTEGER NOT NULL,
       len INTEGER NOT NULL,
       numforms INTEGER NOT NULL,
       hood INTEGER NOT NULL,
       revform VARCHAR(256) NOT NULL,
       PRIMARY KEY (form)
);

CREATE INDEX IF NOT EXISTS idx_forms_form_freq ON forms(form, frequency);
CREATE INDEX IF NOT EXISTS idx_forms_form_numforms ON forms(form, numforms);
CREATE INDEX IF NOT EXISTS idx_forms_form_len ON forms(form, len);
CREATE INDEX IF NOT EXISTS idx_forms_len_form ON forms(len, form);
CREATE INDEX IF NOT EXISTS idx_forms_form_hood ON forms(form, hood);
CREATE INDEX IF NOT EXISTS idx_forms_hood_form ON forms(hood, form);
CREATE INDEX IF NOT EXISTS idx_forms_form_rev ON forms(form, revform);
CREATE INDEX IF NOT EXISTS idx_forms_rev_form ON forms(revform, form);

CREATE TABLE IF NOT EXISTS lemmaforms (
       lemma VARCHAR(256) NOT NULL,
       form VARCHAR(256) NOT NULL,
       pos VARCHAR(256) NOT NULL,
       frequency INTEGER NOT NULL,
       formpct FLOAT NOT NULL,
       formsum INTEGER NOT NULL,
       PRIMARY KEY (lemma, form, pos)
);

CREATE INDEX IF NOT EXISTS idx_lemmaforms_lemma_form_freq ON lemmaforms(lemma, form, frequency);
CREATE INDEX IF NOT EXISTS idx_lemmaforms_form_frequency ON lemmaforms(form, frequency);
