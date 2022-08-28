from scholarly import scholarly, ProxyGenerator

pg = ProxyGenerator()
pg.FreeProxies()
scholarly.use_proxy(pg)

#author = next(scholarly.search_author('Steven A Cholewiak'))
results = next(scholarly.search_keyword('uc'))
scholarly.pprint(results)
