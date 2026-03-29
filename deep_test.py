import asyncio
import os
import json
import requests
from main import BrowserManager, action_list_installed_apps, action_open_local_app, action_find_file, action_write_file

async def test_youtube():
    print("\n[TEST] YouTube Playback...")
    bm = BrowserManager()
    try:
        page = await bm.navigate("https://www.youtube.com/results?search_query=lofi+music")
        # Reuse singleton
        result = await bm.click_youtube_video()
        print(f"Result: {result}")
        if "SUCCESS" in result:
            print("[OK] YouTube Tool: FUNCTIONAL")
        else:
            print("[FAIL] YouTube Tool: FAILED")
    except Exception as e:
        print(f"[ERROR] YouTube test crashed: {e}")
    finally:
        await bm.close()

async def test_file_ops():
    print("\n[TEST] File System Operations...")
    test_file = "autoflow_test.txt"
    test_content = "This is a stability test for AutoFlow."
    try:
        # Write
        res_write = action_write_file(f"{test_file}:{test_content}")
        print(f"Write: {res_write}")
        
        # Find
        res_find = action_find_file(test_file)
        print(f"Find: {res_find}")
        
        if "SUCCESS" in res_write and "autoflow_test.txt" in res_find:
            print("[OK] File Ops: FUNCTIONAL")
        else:
            print("[FAIL] File Ops: FAILED")
    except Exception as e:
        print(f"[ERROR] File Ops test crashed: {e}")

async def test_status_api():
    print("\n[TEST] Status API...")
    try:
        res = requests.get("http://127.0.0.1:8000/status", timeout=5)
        print(f"Status Data: {json.dumps(res.json(), indent=2)}")
        if res.status_code == 200:
            print("[OK] Status API: FUNCTIONAL")
    except Exception as e:
        print(f"[FAIL] Status API unreachable: {e}. (Ensure main.py is running!)")

def test_local_apps():
    print("\n[TEST] Local App Registry...")
    try:
        res = action_list_installed_apps("Chrome")
        print(f"App Search: {res}")
        if "Chrome" in res:
            print("[OK] App Registry: FUNCTIONAL")
    except Exception as e:
        print(f"[FAIL] App Registry test: {e}")

async def run_suite():
    print("========================================")
    print("     AutoFlow Deep Testing Suite")
    print("========================================\n")
    
    await test_status_api()
    test_local_apps()
    await test_file_ops()
    await test_youtube()
    
    print("\n========================================")
    print("       TEST RUN COMPLETE")
    print("========================================")

if __name__ == "__main__":
    asyncio.run(run_suite())
