from typing import List
from elasticsearch import Elasticsearch, ElasticsearchException

class Query:
    '''
    A class used to interact with an Elasticsearch cluster for querying documents by their IDs.

    Attributes
    ----------
    es : Elasticsearch
        An instance of the Elasticsearch client.

    Methods
    -------
    search(ids: List[str]) -> List[dict]
        Queries the Elasticsearch index for documents matching the provided list of IDs and
        returns their source content.
    '''
    def __init__(self, **kwargs) -> None:
        '''
        Initializes the Query class with an Elasticsearch client instance.

        Parameters
        ----------
        **kwargs : dict
            A dictionary of parameters to configure the Elasticsearch client.
        '''
        self.es = Elasticsearch(**kwargs, headers={"Content-Type": "application/json"})
    
    def search(self, ids: List[str]):
        '''
        Queries the Elasticsearch index for documents matching the provided list of IDs.

        Parameters
        ----------
        ids : List[str]
            A list of document IDs to be queried in the Elasticsearch index.

        Returns
        -------
        List[dict]
            A list of source content from the documents matching the provided IDs.

        Raises
        ------
        ElasticsearchException
            If no results are found for any of the provided IDs.
        '''
        sources = []
        for id in ids:
            full_resp = self.es.search(
                index="ipd-news-online*",
                body={
                    "query": {
                        "match": {
                            "_id": id
                        }
                    }
                }
            )
            hits = full_resp.get("hits").get("hits")
            
            if not hits:
                msg = {"query": {"match": {"_id": id}}, "response": full_resp}
                raise ElasticsearchException(f"No results found for query: {msg}")
            
            for hit in hits:
                source = hit.get("_source")
                sources.append(source)

        return sources