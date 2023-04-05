from dataclasses import dataclass
from typing import TypeVar, Sequence, Mapping

LangCode = TypeVar('LangCode', bound=str | None)
LocaleDict = dict[LangCode, str | None]
Translatable = LocaleDict | str | None


@dataclass(slots=True)
class Result:
    version: str
    lang_code: LangCode
    language: str
    fish: Mapping['Fish.Id', 'Fish'] = None


@dataclass(slots=True)
class Fish:
    Id = TypeVar('Id', bound=str)
    id: Id

    EnName = TypeVar('EnName', bound=str)
    en_name: EnName

    Name = TypeVar('Name', bound=str)
    name: Name

    Hour = TypeVar('Hour', bound=int)
    TimeRange = tuple[Hour, Hour]
    TimeRanges = Sequence[TimeRange]
    time_ranges: TimeRanges

    Weather = TypeVar('Weather', bound=str)
    Weathers = Sequence[Weather]
    weather: Weathers

    SkillLevel = TypeVar('SkillLevel', bound=int)
    min_level: SkillLevel

    Depth = TypeVar('Depth', bound=int)
    max_depth: Depth
    spawn_multi: float
    depth_multi: float

    Behavior = TypeVar('Behavior', bound=str)
    behavior: Behavior

    Difficulty = TypeVar('Difficulty', bound=int)
    difficulty: Difficulty

    FishSize = TypeVar('FishSize', bound=int)
    SizeRange = tuple[FishSize, FishSize]
    size_range: SizeRange

    locations: Sequence['Location'] = None
    bundles: Sequence['Bundle'] = None
    gifts: Mapping['Character.PreferenceType', Sequence['Character']] = None


@dataclass(slots=True)
class Location:
    Key = TypeVar('Key', bound=str)
    key: Key

    Variation = TypeVar('Variation', bound=str)
    variation: Variation
    variation_orig: Variation

    Name = TypeVar('Name', bound=str)
    name: Name

    Season = TypeVar('Season', bound=str)
    season: Season


@dataclass(slots=True)
class Bundle:
    EnName = TypeVar('EnName', bound=str)
    en_name: EnName

    Name = TypeVar('Name', bound=str)
    name: Name


@dataclass(slots=True)
class Character:
    Key = TypeVar('Key', bound=str)
    key: Key

    Name = TypeVar('Name', bound=str)
    name: Name

    PreferenceType = TypeVar('PreferenceType', bound=str)
    LOVES = 'loves'
    LIKES = 'likes'
