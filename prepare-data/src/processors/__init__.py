def process(game_data_dir, output, game_version):
    from .languages import LanguageProcessor
    return LanguageProcessor.run_all(game_data_dir, output, game_version)
