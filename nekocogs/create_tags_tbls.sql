SET search_path TO nekozilla;

CREATE TABLE IF NOT EXISTS tags (
  -- Tag names must be unique, so might as well
  -- use this for the PK.
  name           VARCHAR(30)    PRIMARY KEY
                                CONSTRAINT not_whitespace_name CHECK (
                                  TRIM(name) <> ''
                                ),

  -- Date/time created
  created        TIMESTAMP      NOT NULL DEFAULT NOW(),

  -- Optional last date/time modified
  last_modified  TIMESTAMP      DEFAULT NULL,

  -- Snowflake
  author         BIGINT         NOT NULL,

  -- Snowflake; if null we assume a global tag.
  guild          BIGINT         ,

  -- Whether the tag is considered NSFW.
  is_nsfw        BOOLEAN        DEFAULT FALSE,

  -- Tag content. Allow up to 1800 characters.
  content        VARCHAR(1800)  CONSTRAINT not_whitespace_cont CHECK (
                                  TRIM(content) <> ''
                                )
);
