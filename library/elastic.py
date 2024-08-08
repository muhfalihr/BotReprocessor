import re
import logging
from typing import List, Dict

from elasticsearch.helpers import scan

from tenacity import retry, stop_after_attempt, wait_fixed
from elasticsearch import Elasticsearch as elasticsearch
from elasticsearch import ElasticsearchException as elasticsearch_exception

class Query:
    def __init__(self, **config) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.elastic = elasticsearch( **config, timeout=120 )
    
    def _query_terms(self, field: str, ids: list):
        return { "query": { "terms": { field: ids } } }
    
    def _query_filter(self, field: str, gt_lt: Dict[str, str]):
        return { "query": { "range": { field: gt_lt } } }

    def search(self, ids: List[str], index_pattern: str):
        sources = []
        existing_ids = []

        field_id = "id" if re.match(pattern=r'(ipd.*|^printed-news-raw-.*|^tv-news-raw-2024.*)', string=index_pattern) else "_id"
        query = self._query_terms( field_id, ids )
        
        try:
            for hit in scan( self.elastic, query, index=index_pattern, scroll="5m", size=100 ):
                if re.match(pattern=r'ipd.*', string=index_pattern):
                    source = hit[ "_source" ]
                    id_doc = hit[ "_source" ][ field_id ]
                    sources.append(source)
                    existing_ids.append(id_doc)

                elif re.match(pattern=r'^logging-result.*|error-(?!.*news).*', string=index_pattern):
                    source = hit[ "_source" ][ "raw" ]
                    id_doc = hit[ "_source" ][ field_id ]
                    if "error_status" in source: source.pop("error_status")
                    sources.append(source)
                    existing_ids.append(id_doc)
                
                elif re.match(pattern=r'error-.*news.*', string=index_pattern):
                    source = hit[ "_source" ][ "data" ]
                    id_doc = hit[ "_source" ][ field_id ]
                    if "error_status" in source: source.pop("error_status")
                    sources.append(source)
                    existing_ids.append(id_doc)
                
                elif re.match(pattern=r'(^printed-news-raw-.*|^tv-news-raw-2024.*)', string=index_pattern):
                    source = hit[ "_source" ]
                    id_doc = hit[ "_source" ][ field_id ]
                    sources.append(source)
                    existing_ids.append(id_doc)
            
        
        except ( elasticsearch_exception, Exception ) as err:
            self.logger.error(f"Elasticsearch error : {err}")
        
        ids_not_found = [ id for id in ids if id not in existing_ids ]

        return sources, existing_ids, ids_not_found
    
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def _scan_filter(self, index: str, gt_lt, **field):
        field_id = field[ "id" ]
        field_time = field[ "time" ]
        filter = self._query_filter( field_time, gt_lt )
        ids = [ hit[ "_source" ][ field_id ] for hit in scan( self.elastic, filter, index=index, scroll="5m", size=10 ) ]
        return ids
    
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def _scan_queries(self, index: str, value, **field):
        field_id = field[ "id" ]
        query = self._query_terms( field_id, value )
        ids = [ hit[ "_source" ][ field_id ] for hit in scan( self.elastic, query, index=index, scroll="5m", size=10 ) ]  
        return ids

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def get_ids_doc(self, index: str, gt_lt, **field):
        return self._scan_filter( index, gt_lt, **field )
    
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def id_comparison_doc(self, index: str, ids: list, **field):
        ids_query_result = self._scan_queries( index, ids, **field )
        ids_result = [ id for id in ids if id not in ids_query_result ]
        return ids_result