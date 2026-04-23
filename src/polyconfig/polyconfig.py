import logging
import os
from collections.abc import Callable, Iterable
from contextlib import suppress
from functools import partial
from pathlib import Path
from typing import Any

from addict import Dict


def strautocast(value: str) -> Any:  # noqa: ANN401, PLR0911
    if not isinstance(value, str):
        return value
    value_lower = value.strip().lower()
    if value_lower in {"true", "t", "yes", "y", "on"}:
        return True
    if value_lower in {"false", "f", "no", "n", "off"}:
        return False
    if value_lower in {"none", "null", "nil"}:
        return None
    with suppress(ValueError):
        return int(value_lower)
    with suppress(ValueError):
        return float(value_lower)
    return value


class Config(dict):
    _MISSING = object()
    _INHERITED = object()

    def __init__(
        self,
        raise_if_missing: bool = True,
        objects: dict | None = None,
        verbose: bool = True,
    ) -> None:
        self._dicts: dict[str, dict[str, str]] = {}
        self.bool = partial(self.__call__, cast=bool)
        self.int = partial(self.__call__, cast=int)
        self.raise_if_missing: bool = raise_if_missing
        self.objects = objects
        self.verbose = verbose

    def load_environ(self) -> None:
        self.update(os.environ)

    def load_env_file(self, path: str, raise_if_missing: bool = False) -> bool:
        file = Path(path)
        if not file.exists():
            if raise_if_missing:
                msg = f"Env file '{path}' not found"
                raise FileNotFoundError(msg)
            return False

        for raw_line in file.read_text().splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            raw_key, raw_value = line.split("=", 1)
            key = raw_key.strip()
            value = raw_value.strip()
            if value and (value[0] == value[-1] == "'" or value[0] == value[-1] == '"'):
                value = value[1:-1]
            self[key] = value
            d = self._dicts.get(path, {})
            d[key] = value
            self._dicts[path] = d
        return True

    def load_env_files(self, paths: Iterable[str], raise_if_missing: bool | None = None) -> bool:
        results: list[bool] = [self.load_env_file(path, raise_if_missing) for path in paths]
        return all(results)

    def __call__[T](
        self,
        env_name: str,
        default: T | object = _MISSING,
        cast: Callable | object = _MISSING,
        raise_if_missing: bool | object = _INHERITED,
    ) -> T:
        if raise_if_missing is self._INHERITED:
            raise_if_missing = self.raise_if_missing

        if raise_if_missing and default is self._MISSING:
            raw_value = self[env_name]
        else:
            raw_value = self.get(env_name) if default is self._MISSING else self.get(env_name, default)
        if cast is self._MISSING:
            return strautocast(raw_value)
        if cast:
            return cast(strautocast(raw_value))
        return raw_value  # if not cast -> return raw_value

    def obj[T](
        self,
        env_name: str,
        default_object: T | object = _MISSING,
        raise_if_missing: bool | object = _INHERITED,
    ) -> T:
        if raise_if_missing is self._INHERITED:
            raise_if_missing = self.raise_if_missing

        value = self(env_name, None, raise_if_missing=not default_object)
        if value is None and default_object is None:
            raise KeyError(env_name)

        logger = self.objects["logger"] if "logger" in self.objects else logging.getLogger(__name__)

        if value:
            try:
                obj: T = self.objects[value]
                if self.verbose:
                    logger.info(f"PolyConfig: found '{value}' for '{env_name}'")
            except KeyError:
                if default_object is self._MISSING:
                    raise
                obj = default_object
                if self.verbose:
                    logger.warning(
                        f"PolyConfig: could not find '{value}' for '{env_name}', default to '{default_object}'"
                    )
        else:
            if default_object is self._MISSING:
                raise ValueError
            obj = default_object
            if self.verbose:
                logger.info(f"PolyConfig: empty value for '{env_name}', default to '{default_object}'")
        return obj


class DotTreeConfig(Dict):
    def generate_static_classes(
        self,
        target_file: str,
        begin_comment: str = "# BeginGenerated",
        end_comment: str = "# EndGenerated",
        line_end: str = "\n",
        base_class_name: str = "Config",
        fn_open: Callable = open,
        fn_print: Callable = print,
    ) -> None:
        with fn_open(target_file, "r") as f:
            old_lines: list[str] = f.readlines()

        try:
            start = old_lines.index(f"{begin_comment}{line_end}")
            end = old_lines.index(f"{end_comment}{line_end}")
        except Exception as e:
            fn_print(f"Error generating static classes to file {target_file} due to {e!s}")
        else:
            generated: list[str] = []
            self.generate_dataclass(base_class_name, self, generated, [], line_end)
            generated = [f"{line}" for line in generated]
            new_content = old_lines[: start + 1] + generated + old_lines[end:]

            if old_lines != new_content:
                with fn_open(target_file, "w") as f:
                    f.writelines(new_content)

    def generate_dataclass(
        self,
        name: str,
        data: dict,
        list_buffer: list[str],
        hierarchy: list | None = None,
        line_end: str = "\n",
    ) -> None:
        if hierarchy is None:
            hierarchy = []
        fields = []
        new_hierarchy = hierarchy[:]
        new_hierarchy.extend([name])

        for key, value in data.items():
            result = self.attribute_typing(key, value, list_buffer, new_hierarchy)
            type_hint, default = result
            fields.append(f"    {key}: {type_hint} = {default}")

        list_buffer.append(f"@dataclass{line_end}")
        list_buffer.append(f"class {''.join(hierarchy)}{name}:{line_end}")
        if not fields:
            list_buffer.append(f"    pass{line_end}")
        for field in fields:
            list_buffer.append(f"{field}{line_end}")
        list_buffer.append(line_end)
        list_buffer.append(line_end)

    def attribute_typing(
        self,
        key: str,
        value: Any,
        classes: list[str],
        hierarchy: list | None = None,
    ) -> tuple | None:
        if hierarchy is None:
            hierarchy = []
        if isinstance(value, dict):
            class_name = self.snake_case_to_camel_case(key)
            self.generate_dataclass(class_name, value, classes, hierarchy)
            class_name = f"{''.join(hierarchy)}{class_name}"
            return class_name, f"field(default_factory={class_name})"
        if value is None:
            return None, "None"
        return type(value).__name__, f"field(default_factory={type(value).__name__})"

    def snake_case_to_camel_case(self, key: str) -> str:
        return "".join(word.capitalize() for word in key.replace("-", "_").split("_"))
