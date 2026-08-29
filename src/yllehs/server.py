import json
import asyncio
from aiohttp import web, WSMsgType
from typing import TYPE_CHECKING, Set
from yllehs.rpc import RPCError

if TYPE_CHECKING:
    from yllehs.device import VirtualDevice

def create_device_app(device: "VirtualDevice") -> web.Application:
    app = web.Application()
    ws_clients: Set[web.WebSocketResponse] = set()

    # Broadcast notification to connected Home Assistant / RPC WebSockets
    def broadcast_notification(method: str, params: dict):
        if not ws_clients:
            return
        msg = json.dumps({
            "src": f"yllehs-{device.name}",
            "dst": "all",
            "method": method,
            "params": params
        })
        for ws in list(ws_clients):
            if not ws.closed:
                asyncio.create_task(ws.send_str(msg))

    def on_component_event(event_type: str, data: dict):
        if event_type == "status_change":
            # Real Shelly Gen2 NotifyStatus format
            delta = data.get("delta", {})
            params = {
                "ts": data.get("status", {}).get("unixtime", 0),
                data.get("component"): delta
            }
            broadcast_notification("NotifyStatus", params)
        elif event_type == "event":
            # Real Shelly Gen2 NotifyEvent format
            params = {
                "ts": data.get("ts", 0),
                "events": [data.get("info", data)]
            }
            broadcast_notification("NotifyEvent", params)

    # Listen to component updates for WebSocket push
    for comp in device.components.values():
        comp.add_listener(on_component_event)

    # --- Gen 2 & Gen 3 RPC endpoints ---
    async def handle_rpc_post(request: web.Request) -> web.Response:
        try:
            body = await request.json()
        except Exception:
            return web.json_response({"id": 0, "src": "yllehs", "error": {"code": 400, "message": "Invalid JSON"}}, status=400)
        
        rpc_id = body.get("id", 1)
        method = body.get("method")
        params = body.get("params", {})
        
        if not method:
            return web.json_response({"id": rpc_id, "src": "yllehs", "error": {"code": 400, "message": "Missing method"}}, status=400)
        
        try:
            result = await device.rpc_handler.execute(method, params)
            return web.json_response({"id": rpc_id, "src": "yllehs", "result": result})
        except RPCError as e:
            return web.json_response({"id": rpc_id, "src": "yllehs", "error": {"code": e.code, "message": e.message}}, status=200)
        except Exception as e:
            return web.json_response({"id": rpc_id, "src": "yllehs", "error": {"code": 500, "message": str(e)}}, status=200)

    async def handle_rpc_ws_or_get(request: web.Request) -> web.StreamResponse:
        # Check if WebSocket upgrade request (Home Assistant aioshelly connection)
        if request.headers.get("Upgrade", "").lower() == "websocket":
            ws = web.WebSocketResponse()
            await ws.prepare(request)
            ws_clients.add(ws)
            try:
                async for msg in ws:
                    if msg.type == WSMsgType.TEXT:
                        try:
                            req = json.loads(msg.data)
                            rpc_id = req.get("id", 1)
                            method = req.get("method")
                            params = req.get("params", {})
                            src = req.get("src", "client")
                            
                            if not method:
                                await ws.send_str(json.dumps({"id": rpc_id, "src": f"yllehs-{device.name}", "dst": src, "error": {"code": 400, "message": "Missing method"}}))
                                continue
                            
                            try:
                                res = await device.rpc_handler.execute(method, params)
                                await ws.send_str(json.dumps({"id": rpc_id, "src": f"yllehs-{device.name}", "dst": src, "result": res}))
                            except RPCError as e:
                                await ws.send_str(json.dumps({"id": rpc_id, "src": f"yllehs-{device.name}", "dst": src, "error": {"code": e.code, "message": e.message}}))
                            except Exception as e:
                                await ws.send_str(json.dumps({"id": rpc_id, "src": f"yllehs-{device.name}", "dst": src, "error": {"code": 500, "message": str(e)}}))
                        except Exception as e:
                            pass
                    elif msg.type == WSMsgType.ERROR:
                        break
            finally:
                ws_clients.discard(ws)
            return ws

        # HTTP GET RPC Method
        method = request.match_info.get("method")
        params = dict(request.query)
        parsed_params = {}
        for k, v in params.items():
            try:
                parsed_params[k] = json.loads(v)
            except Exception:
                if v.lower() == 'true':
                    parsed_params[k] = True
                elif v.lower() == 'false':
                    parsed_params[k] = False
                elif v.isdigit():
                    parsed_params[k] = int(v)
                else:
                    parsed_params[k] = v

        try:
            result = await device.rpc_handler.execute(method, parsed_params)
            return web.json_response(result)
        except RPCError as e:
            return web.json_response({"code": e.code, "message": e.message}, status=400)
        except Exception as e:
            return web.json_response({"code": 500, "message": str(e)}, status=500)

    # --- Gen 1 REST API endpoints ---
    async def handle_gen1_relay(request: web.Request) -> web.Response:
        idx = int(request.match_info.get("id", 0))
        comp = device.get_component("relay", idx)
        if not comp:
            return web.json_response({"error": "Not found"}, status=404)
        
        turn = request.query.get("turn")
        if turn:
            comp.set_state(turn.lower())
        return web.json_response(comp.get_status())

    async def handle_gen1_settings(request: web.Request) -> web.Response:
        return web.json_response(device.get_config())

    # --- Common endpoints ---
    async def handle_shelly_get(request: web.Request) -> web.Response:
        return web.json_response(device.get_device_info())

    async def handle_status_get(request: web.Request) -> web.Response:
        return web.json_response(device.get_status())

    async def handle_simulate_input(request: web.Request) -> web.Response:
        try:
            body = await request.json()
        except Exception:
            body = {}
        cid = int(request.match_info.get("id", 0))
        event = body.get("event", "btn_down")
        state = body.get("state", None)
        comp = device.get_component("input", cid)
        if not comp:
            return web.json_response({"error": f"Input {cid} not found"}, status=404)
        res = comp.trigger(state=state, event_name=event)
        return web.json_response({"success": True, "result": res})

    if device.gen == 1:
        # Gen 1 Routes
        app.router.add_get("/relay/{id}", handle_gen1_relay)
        app.router.add_post("/relay/{id}", handle_gen1_relay)
        app.router.add_get("/settings", handle_gen1_settings)
        app.router.add_get("/status", handle_status_get)
        app.router.add_get("/shelly", handle_shelly_get)
    else:
        # Gen 2 & Gen 3 RPC Routes (HTTP + WebSocket)
        app.router.add_get("/rpc", handle_rpc_ws_or_get)
        app.router.add_post("/rpc", handle_rpc_post)
        app.router.add_get("/rpc/{method}", handle_rpc_ws_or_get)
        app.router.add_get("/shelly", handle_shelly_get)
        app.router.add_get("/status", handle_status_get)

    # Test/Simulation control endpoint (separated from Shelly API)
    app.router.add_post("/_yllehs/simulate/input/{id}", handle_simulate_input)

    return app
