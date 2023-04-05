import os
import typing
from functools import cached_property

from returns import returns

from utils import Merge, merge
from . import t
from .base import JsonFileProcessor
from .fish import FishProcessor, AbstractExtendFishProcessor


class BundleProcessorMixin(AbstractExtendFishProcessor):
    @property
    def _raw_bundles(self) -> typing.Iterator:
        raise NotImplementedError

    def _process_bundle(self, raw_bundle) -> typing.Iterator[tuple[t.Fish.Id, t.Bundle]]:
        raise NotImplementedError

    @cached_property
    @returns(list)
    def _bundles(self) -> list[tuple[t.Fish.Id, t.Bundle]]:
        for raw_bundle in self._raw_bundles:
            yield from self._process_bundle(raw_bundle)

    def __iter__(self) -> typing.Iterator[tuple[t.Fish.Id, t.Bundle]]:
        yield from self._bundles

    @cached_property
    @returns(merge)
    def _fish_bundles(self) -> dict[t.Fish.Id, t.Bundle]:
        yield from self

    def extend_fish(self, fish: t.Fish) -> None:
        if fish.id not in self._fish_bundles:
            return
        fish.bundles = self._fish_bundles[fish.id]


class BundleProcessor(JsonFileProcessor, BundleProcessorMixin):
    FILENAME = os.path.join('Data', 'Bundles')

    @property
    def _raw_bundles(self) -> typing.Iterator:
        yield from self._raw_data.values()

    @cached_property
    def _fish_processor(self) -> FishProcessor:
        return self.parent.get_processor(FishProcessor)

    def _parse_items(self, value: str) -> typing.Iterator[t.Fish.Id]:
        elems = value.split(' ')
        for i in range(0, len(elems), 3):
            item_id = elems[i]
            if item_id not in self._fish_processor:
                continue
            yield item_id

    def _process_bundle(self, value: str) -> typing.Iterator[tuple[t.Fish.Id, t.Bundle]]:
        # https://stardewvalleywiki.com/Modding:Bundles
        (
            name,
            reward,
            items,
            color,
            *other_fields,
        ) = value.split('/')

        if self.parent.lang_code is not None:
            localized_name = other_fields[-1]
        else:
            localized_name = name
        bundle = t.Bundle(
            en_name=name,
            name=localized_name,
        )

        for fish_id in self._parse_items(items):
            yield fish_id, bundle


class RemixedBundleNameProcessor(JsonFileProcessor):
    FILENAME = os.path.join('Strings', 'BundleNames')

    def __getitem__(self, en_name: t.Bundle.EnName) -> t.Bundle.Name | None:
        return self._raw_data.get(en_name)


class RemixedBundleProcessor(JsonFileProcessor, BundleProcessorMixin):
    FILENAME = os.path.join('Data', 'RandomBundles')
    USE_LOCALE = False

    @property
    def _raw_bundles(self) -> typing.Iterator:
        for area in self._raw_data:
            for bundle_set in area['BundleSets']:
                yield from bundle_set['Bundles']
            yield from area['Bundles']

    @cached_property
    def _fish_processor(self) -> FishProcessor:
        return self.parent.get_processor(FishProcessor)

    def _parse_items(self, value: str) -> typing.Iterator[t.Fish.Id]:
        for elem in value.split(','):
            elem = elem.strip()
            count, item_en_name = elem.split(' ', maxsplit=1)
            item_id = self._fish_processor.get_id_from_en_name(item_en_name)
            if item_id is None:
                continue
            yield item_id

    @cached_property
    def _bundle_name_processor(self) -> RemixedBundleNameProcessor:
        return self.parent.get_processor(RemixedBundleNameProcessor)

    def _process_bundle(self, raw_bundle) -> typing.Iterator[tuple[t.Fish.Id, t.Bundle]]:
        en_name = raw_bundle['Name']
        bundle = t.Bundle(
            en_name=en_name,
            name=self._bundle_name_processor[en_name],
        )

        for fish_id in self._parse_items(raw_bundle['Items']):
            yield fish_id, bundle


class AllBundleProcessor(BundleProcessorMixin):
    PROCESSORS = (
        BundleProcessor,
        RemixedBundleProcessor,
    )

    @property
    def _processors(self) -> list[BundleProcessorMixin]:
        for processor_cls in self.PROCESSORS:
            yield self.parent.get_processor(processor_cls)

    @cached_property
    @returns(list)
    def _bundles(self) -> list[tuple[t.Fish.Id, t.Bundle]]:
        for processor in self._processors:
            yield from processor

    @cached_property
    @returns(Merge(dedup_key=lambda bundle: bundle.en_name))
    def _fish_bundles(self) -> dict[t.Fish.Id, t.Bundle]:
        yield from self
