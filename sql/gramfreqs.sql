CREATE TABLE IF NOT EXISTS initgramfreqs (
       form VARCHAR(256) NOT NULL,
       frequency INTEGER NOT NULL,
       PRIMARY KEY (form)
);

CREATE TABLE IF NOT EXISTS fingramfreqs (
       form VARCHAR(256) NOT NULL,
       frequency INTEGER NOT NULL,
       PRIMARY KEY (form)
);

CREATE TABLE IF NOT EXISTS bigramfreqs (
       form VARCHAR(256) NOT NULL,
       frequency INTEGER NOT NULL,
       PRIMARY KEY (form)
);

CREATE TABLE IF NOT EXISTS wordbigramfreqs (
       form VARCHAR(256) NOT NULL,
       frequency INTEGER NOT NULL,
       PRIMARY KEY (form)
);
