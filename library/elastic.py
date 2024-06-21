from typing import List
from elasticsearch import Elasticsearch

class Query:
    def __init__(self, **kwargs) -> None:
        self.es = Elasticsearch(**kwargs, headers={"Content-Type": "application/json"})
    
    def search(self, ids: List[str]):
        responses = [
            doc.get("_source")
            for id in ids
            for doc in self.es.search(
                index="ipd-news-online*",
                body={
                    "query": {
                        "match": {
                            "_id": id
                        }
                    }
                }
            ).get("hits").get("hits")
        ]
        return responses