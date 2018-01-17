SET search_path TO nekozilla;

-- Note, BIGINT is 64bit signed
CREATE TABLE IF NOT EXISTS tags (
  pk             SERIAL         PRIMARY KEY NOT NULL UNIQUE,

  name           VARCHAR(30)    NOT NULL
                                CONSTRAINT not_whitespace_name CHECK (
                                  TRIM(name) <> ''
                                ),

  -- Snowflake; if null we assume a global tag.
  guild          BIGINT         DEFAULT NULL,

  -- Date/time created
  created        TIMESTAMP      NOT NULL DEFAULT NOW(),

  -- Optional last date/time modified
  last_modified  TIMESTAMP      DEFAULT NULL,

  -- Snowflake
  author         BIGINT         NOT NULL,

  -- Whether the tag is considered NSFW.
  is_nsfw        BOOLEAN        DEFAULT FALSE,

  -- Tag content. Allow up to 1800 characters.
  content        VARCHAR(1800)  CONSTRAINT not_whitespace_cont CHECK (
                                  TRIM(content) <> ''
                                )
);
