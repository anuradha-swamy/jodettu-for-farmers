#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from general.database import machines
import pprint

def debug_machines():
    try:
        # Check total count of machines
        total_count = machines.count_documents({})
        print(f'Total documents in machines collection: {total_count}')
        
        # Get all documents to see what's there
        all_docs = list(machines.find({}))
        print(f'\nAll documents in machines collection:')
        for i, doc in enumerate(all_docs):
            print(f'{i+1}. {doc}')
        
        # Check what the current service method would return
        exclude_filter = {"function": {"$ne": "ID_counter"}}
        doc_cursor = machines.find(exclude_filter)
        docs = doc_cursor.to_list(length=None)
        result = [{**doc, "_id": str(doc["_id"])} for doc in docs]
        print(f'\nWhat get_all_machines should return ({len(result)} documents):')
        for i, doc in enumerate(result):
            print(f'{i+1}. {doc}')
            
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_machines()
