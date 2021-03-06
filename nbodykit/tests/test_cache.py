from nbodykit import GlobalCache
from nbodykit.lab import UniformCatalog

def test_cache():

    cat = UniformCatalog(nbar=10000, BoxSize=1.0)
    cat['test'] = cat['Position'] ** 5
    test = cat['test'].compute()

    # cache should no longer be empty
    cache = GlobalCache.get()
    assert cache.cache.total_bytes > 0

    # resize
    GlobalCache.resize(100)
    assert cache.cache.total_bytes < 100
