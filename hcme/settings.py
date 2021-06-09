from dynaconf import Dynaconf, constants

config = Dynaconf(
    envvar_prefix="HCME",
    load_dotenv=True,
    warn_dynaconf_global_settings=True,
    environments=True,
    default_env="hcme",
    lowercase_read=False,
    default_settings_paths=constants.DEFAULT_SETTINGS_FILES,
)

BEAM_DIR = config.get("BEAM_DIR")
JAVA_EXEC_PATH = config.get("JAVA_EXEC_PATH")
