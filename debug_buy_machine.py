#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.machine_services import MachineServices
import asyncio

async def debug_buy_machine():
    try:
        print("Testing buy_machine function...")
        machine_id = "DEL_01"
        print(f"Testing with machine_id: {machine_id}")
        
        # Test the buy_machine function
        result = await MachineServices.buy_machine(machine_id)
        print(f"Success! Result: {result}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_buy_machine())
