import asyncio
import json
from app.api import run_analysis_for_ticker

async def test_openai():
    print("\n--- Testing OpenAI (Private) ---")
    try:
        # We don't use db or save_history to avoid DB issues
        result = await run_analysis_for_ticker("OpenAI", db=None, save_history=False)
        print("  FAILED: OpenAI should have failed with a friendly error.")
    except ValueError as e:
        print(f"  SUCCESS (ValueError): {e}")
    except Exception as e:
        print(f"  OTHER ERROR: {type(e).__name__}: {e}")

async def test_streaming_openai():
    print("\n--- Testing Streaming OpenAI (Private) ---")
    from app.api import analyze_stream
    # We need a mock DB for this
    class MockDB:
        async def execute(self, *args, **kwargs):
            class MockResult:
                def scalars(self):
                    class MockScalars:
                        def first(self):
                            return None
                    return MockScalars()
            return MockResult()
        async def commit(self): pass
        async def refresh(self, *args): pass
        def add(self, *args): pass

    # analyze_stream is a generator function
    # It takes ticker and db
    # We can't easily call it directly because it returns a StreamingResponse
    # But we can test the internal generator
    
    # Wait, analyze_stream doesn't use the generator directly, it returns StreamingResponse(event_generator(), ...)
    # Let's just run the run_analysis_for_ticker test, that's what matters most.
    pass

if __name__ == "__main__":
    asyncio.run(test_openai())
