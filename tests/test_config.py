from pathlib import Path
from uuid import UUID, uuid4

import pytest

from polyconfig import Config, Inherited, Missing, MissingEnvsError

path = Path(__file__).parent


class TestInherited:
    def test_repr(self) -> None:
        inherited = Inherited()
        assert repr(inherited) == "<INHERITED>"


class TestMissing:
    def test_repr(self) -> None:
        missing = Missing()
        assert repr(missing) == "<MISSING>"


class TestConfigCall:
    def test_load_env_file_exists(self) -> None:
        cfg = Config()
        loaded = cfg.load_env_file(f"{path}/.env")
        assert loaded

    def test_load_env_file_not_exist_no_raise(self) -> None:
        cfg = Config()
        loaded = cfg.load_env_file(f"{path}/{uuid4()}")
        assert not loaded

    def test_load_env_file_not_exist_raise(self) -> None:
        cfg = Config()
        with pytest.raises(FileNotFoundError):
            cfg.load_env_file(f"{path}/{uuid4()}", raise_if_missing=True)

    def test_load_env_file(self) -> None:
        cfg = Config()
        cfg.load_env_file(f"{path}/.env")
        assert cfg("ENV") == "auto as string"
        assert cfg("ENV_BOOL_TRUE")
        assert not cfg("ENV_BOOL_FALSE")
        assert cfg("ENV_INT_ZERO") == 0
        assert cfg("ENV_INT_ONE") == 1
        assert cfg("ENV_INT_MANY") == 3
        assert cfg("ENV_BOOL_TRUE_SIGNLE_QUOTE")
        assert cfg("ENV_BOOL_TRUE_DOUBLE_QUOTE")
        assert cfg("VALUE") == 2
        assert cfg("VALUE_EMPTY") == ""

    def test_cast(self) -> None:
        cfg = Config()
        cfg.load_env_file(f"{path}/.env")
        assert cfg("VALUE", cast=str) == "2"
        assert cfg("VALUE", cast=None) == "2"

    def test_load_env_files(self) -> None:
        cfg = Config()
        cfg.load_env_file(f"{path}/.env")
        cfg.load_env_files([f"{path}/.env", f"{path}/.env2"])
        assert cfg("VALUE") == 3

    def test_load_environ(self) -> None:
        cfg = Config()
        cfg.load_env_file(f"{path}/.env")
        cfg.load_environ()
        assert cfg("USER") != "c243b92e-da63-4994-8e03-a0cccd0f0112"


class TestConfigObj:
    def test_obj(self) -> None:
        cfg = Config(objects={"Path": Path, "uuid4": uuid4})
        cfg.load_env_file(f"{path}/.env")
        assert isinstance(cfg.obj("Path")("."), Path)
        assert isinstance(cfg.obj("uuid4")(), UUID)

    def test_variable_not_exists(self) -> None:
        cfg = Config(objects={"Path": Path, "uuid4": uuid4}, raise_if_missing=False)
        cfg.load_env_file(f"{path}/.env")
        non_exist = cfg.obj("PathXYZ")
        assert repr(non_exist) == "<MISSING>"
        with pytest.raises(MissingEnvsError) as e:
            cfg.raise_missing()
        assert str(e.value) == "Could not found env variables: PathXYZ"

    def test_variable_exists_obj_not_exist(self) -> None:
        cfg = Config(objects={"Path": Path, "uuid4": uuid4})
        cfg.load_env_file(f"{path}/.env")
        with pytest.raises(ValueError):
            assert cfg.obj("Path1")
        with pytest.raises(ValueError):
            assert cfg.obj("uuid0")

    def test_variable_exists_obj_not_exist_default(self) -> None:
        cfg = Config(objects={"Path": Path, "uuid4": uuid4})
        cfg.load_env_file(f"{path}/.env")
        with pytest.raises(KeyError):
            assert cfg.obj("Path1", None)
        assert cfg.obj("uuid0", []) == []

    def test_variable_exists_value_bad_no_default(self) -> None:
        cfg = Config(objects={"Path": Path, "uuid4": uuid4})
        cfg.load_env_file(f"{path}/.env")
        with pytest.raises(KeyError):
            cfg.obj("uuid_bad")
        cfg.obj("uuid_bad", None)


class TestConfigRaiseMissing:
    def test_raise(self) -> None:
        cfg = Config(objects={"Path": Path, "uuid4": uuid4}, raise_if_missing=False)
        cfg.load_env_file(f"{path}/.env")
        e1 = cfg("MISSING_ENV_1")
        e2 = cfg("MISSING_ENV_2", "default_missing")
        e3 = cfg("MISSING_ENV_3")
        assert repr(e1) == "<MISSING>"
        assert e2 == "default_missing"
        assert repr(e3) == "<MISSING>"
        expect = "Could not found env variables: MISSING_ENV_1, MISSING_ENV_2 (default_missing), MISSING_ENV_3"
        with pytest.raises(MissingEnvsError) as e:
            cfg.raise_missing()
        assert str(e.value) == expect
