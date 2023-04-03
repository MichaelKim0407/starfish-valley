from processors import LanguageProcessor


def prepare_data(source, output, version_name):
    LanguageProcessor.run_all(source, output, version_name)


def main(args=None):
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('--source', default='/source')
    parser.add_argument('--output', default='/data')
    parser.add_argument('--version-name', default='Latest')
    args = parser.parse_args(args)
    prepare_data(**vars(args))


if __name__ == '__main__':
    main()
