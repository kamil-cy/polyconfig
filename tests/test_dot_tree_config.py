from dataclasses import dataclass, field
from pathlib import Path
from typing import Self

import pytest

from polyconfig import DotTreeConfig, Missing

# this stub of class should be between marks for generated content
# class Config: ...

# 🡇🡇🡇 puts something between BeginGenerated/EndGenerated then it will be overwritten


# fmt: off
# BeginGenerated
@dataclass
class ConfigABC:
    value: str = field(default_factory=str)
    none: None = None


@dataclass
class ConfigAB:
    value1: str = field(default_factory=str)
    value2: str = field(default_factory=str)
    c: ConfigABC = field(default_factory=ConfigABC)


@dataclass
class ConfigA:
    value: str = field(default_factory=str)
    b: ConfigAB = field(default_factory=ConfigAB)


@dataclass
class Config:
    a: ConfigA = field(default_factory=ConfigA)


# EndGenerated
# fmt: on


class AppConfig(DotTreeConfig, Config):
    pass


class TestDotTreeConfig:
    def test_success(self) -> None:
        config = AppConfig()
        config.a.value = "a.value"
        config.a.b.value1 = "a.b.value1"
        config.a.b.value2 = "a.b.value2"
        config.a.b.c.value = "a.b.c.value"
        config.a.b.c.none = None
        config.a  # 🡄🡄🡄 put dot here any autocompletion for b and value should be enabled
        config.generate_static_classes(__file__)

    def test_success_mock(self) -> None:
        class Mock:
            def __init__(self, file: str, mode: str) -> None:
                self.file = file
                self.mode = mode

            def __enter__(self) -> Self:
                return self

            def __exit__(self, exc_type, exc, tb) -> None:
                pass

            def readlines(self) -> list[str]:
                with open(self.file, self.mode) as f:
                    return f.readlines()

            def writelines(self, data: str) -> None:
                pass

        config = AppConfig()
        config.a.value = "a.value"
        config.generate_static_classes(
            Path(__file__).parent / ".env2",
            fn_open=lambda file, mode: Mock(file, mode),
        )

    def test_fails_file_not_found(self) -> None:
        config = AppConfig()
        config.a.value = "a.value"
        with pytest.raises(FileNotFoundError):
            config.generate_static_classes("")

    def test_fails_no_marks(self) -> None:
        config = AppConfig()
        config.a.value = "a.value"
        config.generate_static_classes(
            Path(__file__).parent / ".env",
            fn_print=lambda _: None,
        )

    def test_generate_dataclass_valid_dict(self) -> None:
        buffer: list[str] = []
        config = AppConfig()
        config.a.value = "a.value"
        config.generate_dataclass("MyClass", {"a": 1}, buffer)
        assert buffer == ["@dataclass\n", "class MyClass:\n", "    a: int = field(default_factory=int)\n", "\n", "\n"]

    def test_generate_dataclass_invalid_dict(self) -> None:
        buffer: list[str] = []
        config = AppConfig()
        config.a.value = "a.value"
        config.generate_dataclass("MyClass", {}, buffer)
        assert buffer == ["@dataclass\n", "class MyClass:\n", "    pass\n", "\n", "\n"]

    def test_attribute_typing(self) -> None:
        config = AppConfig()
        config.a.value = "a.value"
        result = config.attribute_typing("a", 1, [], None)
        assert result == ("int", "field(default_factory=int)")


class TestDotTreeConfigPreventGeneratingIfMissingEnvs:
    def test_generate_static_classes(self) -> None:
        config = AppConfig()
        config.a.value = "a.value"
        config.attribute_typing("a", Missing(), [], None)
        config.generate_static_classes(__file__)
        assert hasattr(config, "missing")

    def test_generate_dataclass(self) -> None:
        buffer: list[str] = []
        config = AppConfig()
        config.attribute_typing("a", Missing(), [], None)
        config.generate_dataclass("MyClass", {}, buffer)
        assert hasattr(config, "missing")
        assert buffer == []

    def test_attribute_typing(self) -> None:
        config = AppConfig()
        result = config.attribute_typing("a", Missing(), [], None)
        assert result == ("Missing", "field(default_factory=Missing)")
        assert hasattr(config, "missing")
