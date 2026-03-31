#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from general.database import own_animals
import pprint

def debug_animals():
    try:
        # Check total count of animals
        total_count = own_animals.count_documents({'function': {'$ne': 'ID_counter'}})
        print(f'Total animals in database: {total_count}')
        
        # Get all animals to see the data structure
        all_animals = list(own_animals.find({'function': {'$ne': 'ID_counter'}}))
        print(f'\nAll animals data ({len(all_animals)} animals):')
        for i, animal in enumerate(all_animals):
            print(f'{i+1}. Animal ID: {animal.get("own_animal_id")}, User ID: {animal.get("user_id")}, Name: {animal.get("own_animal_name")}')
        
        # Check if there are animals for different user_ids
        user_ids = own_animals.distinct('user_id', {'function': {'$ne': 'ID_counter'}})
        print(f'\nUser IDs found: {user_ids}')
        
        # Count animals per user
        for user_id in user_ids:
            count = own_animals.count_documents({'user_id': user_id, 'function': {'$ne': 'ID_counter'}})
            print(f'User {user_id}: {count} animals')
            
            # Show animals for this user
            user_animals = list(own_animals.find({'user_id': user_id, 'function': {'$ne': 'ID_counter'}}))
            print(f'  Animals for user {user_id}:')
            for animal in user_animals:
                print(f'    - {animal.get("own_animal_id")}: {animal.get("own_animal_name")}')
        
        # Check if there are any documents with function field
        function_docs = list(own_animals.find({'function': {'$exists': True}}))
        print(f'\nDocuments with function field: {len(function_docs)}')
        for doc in function_docs:
            print(f'  Function: {doc.get("function")}, ID: {doc.get("own_animal_id", "N/A")}')
            
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_animals()
