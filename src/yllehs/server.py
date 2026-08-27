import json
from aiohttp import web
from typing import TYPE_CHECKING
from yllehs.rpc import RPCError

if TYPE_CHECKING:
    from yllehs.device import VirtualDevice

def create_device_app(device: "VirtualDevice") -> web.Application:
    app = web.Application()
    
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

    async def handle_rpc_get(request: web.Request) -> web.Response:
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
        # Gen 2 & Gen 3 RPC Routes
        app.router.add_post("/rpc", handle_rpc_post)
        app.router.add_get("/rpc/{method}", handle_rpc_get)
        app.router.add_get("/shelly", handle_shelly_get)
        app.router.add_get("/status", handle_status_get)

    # Test/Simulation control endpoint (separated from Shelly API)
    app.router.add_post("/_yllehs/simulate/input/{id}", handle_simulate_input)

    return app
