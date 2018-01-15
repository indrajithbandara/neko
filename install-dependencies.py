import sys

import pip


vi = sys.version_info
if vi[0] < 3 or vi[0] == 3 and vi[1] < 6:
    print('Please install python3.6')

base_args = ['install']

if len(sys.argv) > 1 and sys.argv[1] in ('-h', '--help'):
    print(
        f'USAGE: {sys.argv[0]} [-h|--help|-U]',
        '    -h|--help  Shows this message',
        '    -U         Force reinstall dependencies',
        ''
        'Installs dependencies for the neko Discord bot.',
        sep='\n')

if len(sys.argv) > 1 and sys.argv[1] == '-U':
    base_args.append('-U')


with open('dependencies.txt') as fp:
    dependencies = filter(lambda dep: dep.strip(), fp.read().split('\n'))


for dependency in dependencies:
    print(f'pip {" ".join(base_args)} {dependency}')
    pip.main([*base_args, dependency])
