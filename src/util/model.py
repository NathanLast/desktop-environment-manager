from typing import Any, cast, Type, Self, ClassVar, Optional, Generic, TypeVar
from enum import Enum
from dataclasses import dataclass
from abc import ABC
import warnings


@dataclass
class Model(ABC):
    """protocol-style class that enables the conversion and restoration of
    objects to and from dict. inheriting classes should be dataclasses
     themselves, without defining any init logic"""

    _TYPE_ATTR_NAME: ClassVar[str] = "__model_type__"
    _SUB_CLASSES: ClassVar[dict[str, type["Model"]]] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.__name__ in Model._SUB_CLASSES:
            warnings.warn(
                f"created two or more models with identical names '{cls.__name__}'"
            )
        Model._SUB_CLASSES[cls.__name__] = cls

    def to_dict(self) -> dict:
        obj = {self._TYPE_ATTR_NAME: self.__class__.__name__}
        for attr, val in self.__dict__.items():
            # ignore dunder attributes besides the model type
            if (
                attr.startswith("__")
                and attr.endswith("__")
                and attr != self._TYPE_ATTR_NAME
            ):
                continue
            obj[attr] = self._to_dict_helper(val)
        return obj

    @classmethod
    def _to_dict_helper(cls, obj) -> Any:
        if isinstance(obj, Model):
            return obj.to_dict()

        if isinstance(obj, EnumModel):
            return obj.to_dict()

        if isinstance(obj, list):
            return [cls._to_dict_helper(item) for item in obj]

        if isinstance(obj, dict):
            return {key: cls._to_dict_helper(val) for key, val in obj.items()}

        if not isinstance(obj, (int, float, str, type(None))):
            raise Exception(f"cannot parse to dict the object '{obj}'")

        return obj

    @classmethod
    def from_dict(
        cls, d: Optional[dict], construct_default_on_none: bool = True
    ) -> Self:
        is_d_empty = d is None or d == {}

        if construct_default_on_none and is_d_empty:
            try:
                return cls()
            except TypeError:
                raise ValueError(
                    f"cannot instantiate default for Model '{cls.__name__}': "
                    "no trivial constructor (requires arguments)"
                )

        if is_d_empty:
            raise Exception(
                f"cannot parse from dict the object '{d}' to an instance of '{cls.__name__}'"
            )

        parsed_obj = cls._from_dict_helper(d)
        if not isinstance(parsed_obj, cls):
            raise Exception(
                f"invalid object. expected instance of '{cls.__name__}' "
                f"but got '{type(parsed_obj).__name__}': {d}"
            )
        return parsed_obj

    @classmethod
    def _from_dict_helper(cls, d: dict) -> Any:
        if isinstance(d, list):
            return [cls._from_dict_helper(item) for item in d]

        if isinstance(d, dict) and cls._TYPE_ATTR_NAME in d:
            # model object
            obj_cls = cls._SUB_CLASSES[d.pop(cls._TYPE_ATTR_NAME)]
            obj = obj_cls.__new__(cast(Type[Self], obj_cls))
            obj.__init__(  # type: ignore
                **{  # type: ignore
                    attr: cls._from_dict_helper(val) for attr, val in d.items()
                }
            )
            return obj

        if isinstance(d, dict) and EnumModel._TYPE_ATTR_NAME in d:  # type: ignore
            # enum model object
            return EnumModel.from_dict(d)

        if isinstance(d, dict):
            # if reached here, d is a dict but wasn't generated from a
            # Model object or a EnumModel object
            new_obj = {}
            for attr, val in d.items():
                new_obj[attr] = cls._from_dict_helper(val)
            return new_obj

        if not isinstance(d, (int, float, str, type(None))):
            raise Exception(f"cannot parse from dict the object '{d}'")

        return d

    def copy_from(self, other: Self) -> None:
        """copy all public fields of self from other."""
        for attr in self.__dict__:
            if not attr.startswith("_"):
                setattr(self, attr, getattr(other, attr))


class EnumModel(Enum):
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.__name__ in EnumModel._SUB_CLASSES:
            warnings.warn(
                f"created two or more EnumModels with identical names '{cls.__name__}"
            )
        EnumModel._SUB_CLASSES[cls.__name__] = cast(EnumModel, cls)

    def to_dict(self) -> dict:
        return {
            EnumModel._TYPE_ATTR_NAME: self.__class__.__name__,  # type: ignore
            EnumModel._KIND_ATTR_NAME: self.name,  # type: ignore
        }

    @classmethod
    def from_dict(cls, d: dict) -> Self:
        if EnumModel._TYPE_ATTR_NAME not in d:  # type: ignore
            raise Exception(f"cannot parse from dict the object '{d}'")

        obj_cls = EnumModel._SUB_CLASSES[d[EnumModel._TYPE_ATTR_NAME]]  # type: ignore
        return obj_cls[d[EnumModel._KIND_ATTR_NAME]]  # type: ignore


# define outside of class to avoid being registered as enum value
EnumModel._TYPE_ATTR_NAME = "__enum_model_type__"  # type: ignore
# specific enum instance
EnumModel._KIND_ATTR_NAME = "__enum_kind__"  # type: ignore
EnumModel._SUB_CLASSES = {}  # type: ignore


GenericModelType = TypeVar("GenericModelType", bound=Model)


class ModelParameterizedClass(Generic[GenericModelType]):
    """Base class. Inheriting classes must be parameterized by a Model
    object in creation. the parameterized model is available via
     self.model_class property"""

    _model_class: Optional[Type[GenericModelType]] = None

    def __init__(self):
        if self._model_class is None:
            raise Exception(f"Model class not set for {self.__class__.__name__}")

    @property
    def model_class(self) -> Type[GenericModelType]:
        return cast(Type[GenericModelType], self._model_class)

    def __class_getitem__(
        cls, model_type: Any
    ) -> Type["ModelParameterizedClass[GenericModelType]"]:
        if isinstance(model_type, TypeVar):
            return super().__class_getitem__(model_type)  # type: ignore

        # dynamically create a subclass parameterized with the model type
        subclass = type(
            f"{cls.__name__}[{model_type.__name__}]",
            (cls,),
            {"_model_class": model_type},
        )

        return cast(Type[ModelParameterizedClass[GenericModelType]], subclass)
