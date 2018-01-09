"""
Provides a global "dictionary" for various API tokens accessed in cogs.

This reads a file called tokens.json found in the current working directory.

This is not an asynchronous API wrapper. Thus, this info should be retrieved
in the constructors of cogs and stored appropriately.
"""
import copy
import json

import neko


__all__ = ['Tokens', 'get_token']


file = 'tokens.json'


@neko.singleton
class Tokens(neko.Loggable):
    """
    Holds a dictionary. The keys are case insensitive and the type behaves
    as if it were immutable.
    """
    def __init__(self):
        try:
            self.logger.info(f'Reading external tokens from {file}')
            with open(file) as fp:
                data = json.load(fp)

                if not isinstance(data, dict):
                    raise TypeError('Expected map of names to keys.')
                else:
                    # Ensure no duplicates of keys (case insensitive)
                    mapping = (*map(str.lower, data.keys()),)
                    if len(mapping) != len({*mapping}):
                        raise ValueError('Duplicate keys found.')
                    else:
                        self.__tokens = {}
                        for k, v in data.items():
                            self.__tokens[k.lower()] = v

        except FileNotFoundError:
            raise FileNotFoundError(f'Cannot find {file}') from None

    def __getitem__(self, api_name):
        try:
            return copy.deepcopy(self.__tokens[api_name])
        except KeyError:
            raise KeyError(f'No API key for {api_name} exists.') from None


def get_token(name):
    return Tokens()[name]
