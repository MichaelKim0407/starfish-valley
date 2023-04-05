def process(game_data_dir, output, game_version):
    from .languages import LanguageProcessor
    from .fish import FishProcessor
    from .locations import LocationProcessor
    from .bundles import AllBundleProcessor
    from .gifts import GiftProcessor

    return LanguageProcessor.run_all(
        game_data_dir,
        output,
        game_version,
        (
            FishProcessor,
            LocationProcessor,
            AllBundleProcessor,
            GiftProcessor,
        ),
    )
