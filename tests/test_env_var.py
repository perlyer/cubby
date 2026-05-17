from cubby_tool import commands


def test_env_var_name_is_upper_snake_without_prefix():
    assert commands._env_var_name("apitoken") == "APITOKEN"
    assert commands._env_var_name("db-password") == "DB_PASSWORD"
    assert commands._env_var_name("DB_URL") == "DB_URL"


def test_resolve_env_var_prefers_the_override():
    env_map = {"db-pass": "PGPASSWORD"}
    assert commands._resolve_env_var(env_map, "db-pass") == "PGPASSWORD"
    assert commands._resolve_env_var(env_map, "apitoken") == "APITOKEN"


def test_env_var_clash_detects_a_taken_variable():
    env_map = {"db-pass": "PGPASSWORD"}
    names = ["db-pass", "apitoken"]
    # APITOKEN is the default of apitoken — setting db-pass to APITOKEN clashes
    assert commands._env_var_clash(env_map, names, "APITOKEN", "db-pass") == "apitoken"
    # PGPASSWORD is db-pass's own override — not a clash for db-pass itself
    assert commands._env_var_clash(env_map, names, "PGPASSWORD", "db-pass") is None
    # a free name
    assert commands._env_var_clash(env_map, names, "FREE_VAR", "db-pass") is None
