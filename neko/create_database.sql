SET search_path TO public;

DO $$
    IF NOT EXISTS(
        SELECT schema_name FROM information_schema.schemata
        WHERE schema_name = 'nekozilla'
    )
    THEN
        EXECUTE 'CREATE SCHEMA nekozilla';
    END IF;
END
$$;