from cubby_tool import commands


def test_env_var_name_is_upper_snake_without_prefix():
    assert commands._env_var_name("apitoken") == "APITOKEN"
    assert commands._env_var_name("db-password") == "DB_PASSWORD"
    assert commands._env_var_name("DB_URL") == "DB_URL"


def test_resolve_env_var_prefers_the_override():
    env_map = {"db-pass": "PGPASSWORD"}
    assert commands._resolve_env_var(env_map, "db-pass") == "PGPASSWORD"
    assert commands._resolve_env_var(env_map, "apitoken") == "APITOKEN"
