#!/usr/bin/env python3
import asyncio
import nats

async def test_connection():
    try:
        nc = await nats.connect("nats://localhost:4224")
        print(f"✅ Connected to NATS server")
        print(f"   Server ID: {nc.connected_server_id}")
        print(f"   Max payload: {nc.max_payload}")
        await nc.close()
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())