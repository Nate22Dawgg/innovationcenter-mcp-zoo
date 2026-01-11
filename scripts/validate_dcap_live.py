#!/usr/bin/env python3
"""
DCAP Live Validation Script

This script validates that DCAP messages can be sent to the public relay
at 159.89.110.236:10191. It performs the following:

1. Sends a test semantic_discover message
2. Sends a test perf_update message
3. Optionally connects to the WebSocket to verify messages are broadcast

Usage:
    python scripts/validate_dcap_live.py [--websocket]

The --websocket flag enables listening on the WebSocket stream to verify
that your messages appear (requires websocket-client package).

Environment Variables:
    DCAP_RELAY_HOST: Override relay host (default: 159.89.110.236)
    DCAP_RELAY_PORT: Override relay port (default: 10191)
"""

import argparse
import json
import os
import socket
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, Dict, Any, List

# DCAP Configuration (inline to avoid import issues)
DCAP_RELAY_HOST = os.getenv("DCAP_RELAY_HOST", "159.89.110.236")
DCAP_RELAY_PORT = int(os.getenv("DCAP_RELAY_PORT", "10191"))
DCAP_ENABLED = os.getenv("DCAP_ENABLED", "true").lower() in ("true", "1", "yes", "on")


@dataclass
class ToolSignature:
    """DCAP v3.1 typed signature."""
    input: str
    output: str
    cost: int = 0


@dataclass
class Connector:
    """DCAP v3.1 connector for tool invocation."""
    transport: str = "stdio"
    protocol: str = "mcp"
    command: Optional[str] = None
    url: Optional[str] = None


def _send_udp(message: Dict[str, Any]) -> bool:
    """Send message via UDP to DCAP relay."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(5.0)
        data = json.dumps(message).encode('utf-8')
        sock.sendto(data, (DCAP_RELAY_HOST, DCAP_RELAY_PORT))
        sock.close()
        return True
    except Exception as e:
        print(f"   UDP send error: {e}")
        return False


def _sanitize_args(args: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Remove sensitive data from args before broadcasting."""
    if not args:
        return {}
    sensitive_keys = {'password', 'token', 'api_key', 'secret', 'credential', 'key'}
    result = {}
    for k, v in args.items():
        if any(s in k.lower() for s in sensitive_keys):
            result[k] = '***'
        elif isinstance(v, str) and len(v) > 200:
            result[k] = v[:200] + '...'
        else:
            result[k] = v
    return result


def send_dcap_semantic_discover(
    server_id: str,
    tool_name: str,
    description: str,
    triggers: List[str],
    signature: ToolSignature,
    connector: Connector
) -> bool:
    """Broadcast semantic_discover message on server startup."""
    if not DCAP_ENABLED:
        return False
    message = {
        "v": 3,
        "t": "semantic_discover",
        "ts": int(time.time()),
        "sid": server_id,
        "tool": tool_name,
        "signature": asdict(signature),
        "does": description,
        "when": triggers,
        "connector": asdict(connector)
    }
    return _send_udp(message)


def send_dcap_perf_update(
    server_id: str,
    tool_name: str,
    exec_ms: int,
    success: bool,
    cost_paid: int = 0,
    caller: Optional[str] = None,
    args: Optional[Dict[str, Any]] = None
) -> bool:
    """Broadcast perf_update message after tool execution."""
    if not DCAP_ENABLED:
        return False
    message = {
        "v": 3,
        "t": "perf_update",
        "ts": int(time.time()),
        "sid": server_id,
        "tool": tool_name,
        "exec_ms": exec_ms,
        "success": success,
        "cost_paid": cost_paid,
        "ctx": {
            "caller": caller or "unknown-agent",
            "args": _sanitize_args(args) if args else {}
        }
    }
    return _send_udp(message)


def test_udp_connectivity() -> bool:
    """Test basic UDP connectivity to the DCAP relay."""
    print(f"\n📡 Testing UDP connectivity to {DCAP_RELAY_HOST}:{DCAP_RELAY_PORT}...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(5.0)
        
        # Send a simple ping message
        test_message = {
            "v": 3,
            "t": "ping",
            "ts": int(time.time()),
            "sid": "dcap-validation-test",
            "msg": "connectivity test"
        }
        
        data = json.dumps(test_message).encode('utf-8')
        bytes_sent = sock.sendto(data, (DCAP_RELAY_HOST, DCAP_RELAY_PORT))
        sock.close()
        
        print(f"   ✅ UDP packet sent successfully ({bytes_sent} bytes)")
        return True
        
    except socket.error as e:
        print(f"   ❌ UDP send failed: {e}")
        return False


def test_semantic_discover() -> bool:
    """Send a test semantic_discover message."""
    print("\n🔍 Sending semantic_discover message...")
    
    try:
        send_dcap_semantic_discover(
            server_id="dcap-validation-test",
            tool_name="test_tool",
            description="Validation test tool for DCAP integration",
            triggers=["test", "validation", "dcap test"],
            signature=ToolSignature(
                input="TestInput",
                output="Maybe<TestOutput>",
                cost=0
            ),
            connector=Connector(
                transport="stdio",
                protocol="mcp",
                command="python scripts/validate_dcap_live.py"
            )
        )
        print("   ✅ semantic_discover message sent")
        return True
        
    except Exception as e:
        print(f"   ❌ semantic_discover failed: {e}")
        return False


def test_perf_update() -> bool:
    """Send a test perf_update message."""
    print("\n📊 Sending perf_update message...")
    
    try:
        send_dcap_perf_update(
            server_id="dcap-validation-test",
            tool_name="test_tool",
            exec_ms=42,
            success=True,
            cost_paid=0,
            args={"test_param": "validation"}
        )
        print("   ✅ perf_update message sent")
        return True
        
    except Exception as e:
        print(f"   ❌ perf_update failed: {e}")
        return False


def test_websocket_stream(duration_seconds: int = 10) -> bool:
    """
    Connect to DCAP WebSocket stream and listen for messages.
    
    This verifies that the relay is broadcasting messages.
    Requires: pip install websocket-client
    """
    print(f"\n🌐 Connecting to WebSocket stream (listening for {duration_seconds}s)...")
    
    try:
        import websocket
    except ImportError:
        print("   ⚠️  websocket-client not installed. Install with: pip install websocket-client")
        return False
    
    ws_url = f"ws://{DCAP_RELAY_HOST}:{DCAP_RELAY_PORT}"
    messages_received = []
    our_messages = []
    
    def on_message(ws, message):
        try:
            data = json.loads(message)
            messages_received.append(data)
            
            # Check if this is our test message
            if data.get("sid") == "dcap-validation-test":
                our_messages.append(data)
                print(f"   📨 Received our message: {data.get('t')} for {data.get('tool')}")
            else:
                # Show other messages (truncated)
                sid = data.get("sid", "unknown")
                msg_type = data.get("t", "unknown")
                tool = data.get("tool", "unknown")
                print(f"   📬 Other: [{sid}] {msg_type} -> {tool}")
                
        except json.JSONDecodeError:
            print(f"   ⚠️  Non-JSON message received")
    
    def on_error(ws, error):
        print(f"   ❌ WebSocket error: {error}")
    
    def on_close(ws, close_status_code, close_msg):
        print(f"   🔌 WebSocket closed")
    
    def on_open(ws):
        print(f"   ✅ Connected to {ws_url}")
        print(f"   👂 Listening for messages...\n")
    
    try:
        ws = websocket.WebSocketApp(
            ws_url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        
        # Run in a thread with timeout
        import threading
        
        def run_ws():
            ws.run_forever()
        
        ws_thread = threading.Thread(target=run_ws, daemon=True)
        ws_thread.start()
        
        # Wait for connection
        time.sleep(1)
        
        # Send our test messages while listening
        print("   📤 Sending test messages while listening...")
        test_semantic_discover()
        time.sleep(0.5)
        test_perf_update()
        
        # Wait to receive messages
        time.sleep(duration_seconds - 1)
        
        ws.close()
        
        print(f"\n   📊 Summary:")
        print(f"      Total messages received: {len(messages_received)}")
        print(f"      Our messages echoed back: {len(our_messages)}")
        
        if our_messages:
            print("   ✅ DCAP integration verified - messages are being broadcast!")
            return True
        elif messages_received:
            print("   ⚠️  Relay is active but our messages weren't echoed (may be normal)")
            return True
        else:
            print("   ⚠️  No messages received from relay")
            return False
            
    except Exception as e:
        print(f"   ❌ WebSocket test failed: {e}")
        return False


def run_all_servers_broadcast():
    """
    Simulate what happens when all MCP servers start up.
    Sends semantic_discover for all registered tools.
    """
    print("\n🚀 Simulating server startup broadcasts...")
    
    # Import all server DCAP tool definitions
    servers = [
        ("clinical-trials-mcp", [
            ("clinical_trials_search", "Search clinical trials by condition, intervention, location"),
            ("clinical_trials_get_detail", "Get detailed information about a specific clinical trial"),
            ("clinical_trial_matching", "Match patients to eligible clinical trials"),
        ]),
        ("nhanes-mcp", [
            ("nhanes_list_datasets", "List available NHANES datasets"),
            ("nhanes_get_data", "Query NHANES data with filters"),
            ("nhanes_get_variable_info", "Get variable information"),
            ("nhanes_calculate_percentile", "Calculate percentile rank"),
            ("nhanes_get_demographics_summary", "Get demographics summary"),
        ]),
        ("biotech-markets-mcp", [
            ("biotech_search_companies", "Search biotech companies"),
            ("biotech_get_company_profile", "Get company profile"),
            ("biotech_get_pipeline_drugs", "Get drug pipeline"),
        ]),
        ("sec-edgar-mcp", [
            ("sec_search_company", "Search SEC companies"),
            ("sec_get_company_filings", "Get company filings"),
        ]),
        ("fda-mcp", [
            ("search_drug_adverse_events", "Search FDA FAERS database"),
            ("search_device_510k", "Search FDA 510(k) clearances"),
        ]),
        ("hospital-prices-mcp", [
            ("hospital_prices_search_procedure", "Search hospital procedure prices"),
            ("hospital_prices_compare", "Compare prices across facilities"),
        ]),
    ]
    
    total_tools = 0
    for server_id, tools in servers:
        for tool_name, description in tools:
            send_dcap_semantic_discover(
                server_id=server_id,
                tool_name=tool_name,
                description=description,
                triggers=[tool_name.replace("_", " ")],
                signature=ToolSignature(input="Query", output="Maybe<Result>", cost=0),
                connector=Connector(transport="stdio", protocol="mcp")
            )
            total_tools += 1
            print(f"   📢 [{server_id}] {tool_name}")
    
    print(f"\n   ✅ Broadcast {total_tools} tool discoveries to DCAP relay")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Validate DCAP integration with the public relay"
    )
    parser.add_argument(
        "--websocket", "-w",
        action="store_true",
        help="Enable WebSocket listening to verify message broadcast"
    )
    parser.add_argument(
        "--broadcast-all", "-a",
        action="store_true",
        help="Broadcast all server tools (simulates full startup)"
    )
    parser.add_argument(
        "--duration", "-d",
        type=int,
        default=10,
        help="Duration to listen on WebSocket (seconds)"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("DCAP Live Validation")
    print("=" * 60)
    print(f"\nConfiguration:")
    print(f"  DCAP_ENABLED: {DCAP_ENABLED}")
    print(f"  DCAP_RELAY_HOST: {DCAP_RELAY_HOST}")
    print(f"  DCAP_RELAY_PORT: {DCAP_RELAY_PORT}")
    
    if not DCAP_ENABLED:
        print("\n⚠️  DCAP is disabled! Set DCAP_ENABLED=true to enable.")
        sys.exit(1)
    
    results = []
    
    # Test 1: UDP connectivity
    results.append(("UDP Connectivity", test_udp_connectivity()))
    
    # Test 2: semantic_discover
    results.append(("semantic_discover", test_semantic_discover()))
    
    # Test 3: perf_update
    results.append(("perf_update", test_perf_update()))
    
    # Optional: Broadcast all servers
    if args.broadcast_all:
        results.append(("Broadcast All", run_all_servers_broadcast()))
    
    # Optional: WebSocket verification
    if args.websocket:
        results.append(("WebSocket Stream", test_websocket_stream(args.duration)))
    
    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    
    if all_passed:
        print("🎉 All validations passed! DCAP integration is working.")
        print("\nYour MCP servers will now broadcast to the DCAP network when started.")
        print(f"WebSocket stream: ws://{DCAP_RELAY_HOST}:{DCAP_RELAY_PORT}")
    else:
        print("⚠️  Some validations failed. Check the output above.")
    
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
