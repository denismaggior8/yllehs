import json
import asyncio
import quickjs
from typing import Any, Dict, List, Optional, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from yllehs.device import VirtualDevice

class ScriptRuntime:
    def __init__(self, device: "VirtualDevice"):
        self.device = device
        self.ctx = quickjs.Context()
        self._timer_seq = 0
        self._timers: Dict[int, asyncio.Task] = {}
        self._event_handlers: List[str] = []
        self._status_handlers: List[str] = []
        self._setup_environment()

    def _setup_environment(self):
        self.ctx.add_callable("_host_print", self._host_print)
        self.ctx.add_callable("_host_shelly_call", self._host_shelly_call)
        self.ctx.add_callable("_host_get_component_status", self._host_get_component_status)
        self.ctx.add_callable("_host_get_component_config", self._host_get_component_config)
        self.ctx.add_callable("_host_get_device_info", self._host_get_device_info)
        self.ctx.add_callable("_host_timer_set", self._host_timer_set)
        self.ctx.add_callable("_host_timer_clear", self._host_timer_clear)

        bootstrap_js = """
        var print = function(...args) {
            var msg = args.map(a => typeof a === 'object' ? JSON.stringify(a) : String(a)).join(' ');
            _host_print(msg);
        };

        var console = {
            log: print,
            error: print,
            warn: print,
            info: print
        };

        var __event_handlers = [];
        var __status_handlers = [];
        var __callbacks = {};
        var __cb_seq = 0;

        var Shelly = {
            call: function(method, params, callback, userdata) {
                var cb_id = null;
                if (typeof callback === 'function') {
                    cb_id = String(++__cb_seq);
                    __callbacks[cb_id] = { fn: callback, userdata: userdata };
                }
                var params_str = JSON.stringify(params || {});
                _host_shelly_call(method, params_str, cb_id);
            },
            addEventHandler: function(handler, userdata) {
                if (typeof handler === 'function') {
                    __event_handlers.push({ fn: handler, userdata: userdata });
                    return handler;
                }
            },
            removeEventHandler: function(handler) {
                __event_handlers = __event_handlers.filter(h => h.fn !== handler);
            },
            addStatusHandler: function(handler, userdata) {
                if (typeof handler === 'function') {
                    __status_handlers.push({ fn: handler, userdata: userdata });
                    return handler;
                }
            },
            removeStatusHandler: function(handler) {
                __status_handlers = __status_handlers.filter(h => h.fn !== handler);
            },
            getComponentStatus: function(type_or_key, id) {
                var key = (id !== undefined && id !== null) ? (type_or_key + ":" + id) : type_or_key;
                var res = _host_get_component_status(key);
                return res ? JSON.parse(res) : null;
            },
            getComponentConfig: function(type_or_key, id) {
                var key = (id !== undefined && id !== null) ? (type_or_key + ":" + id) : type_or_key;
                var res = _host_get_component_config(key);
                return res ? JSON.parse(res) : null;
            },
            getDeviceInfo: function() {
                return JSON.parse(_host_get_device_info());
            }
        };

        var __timer_callbacks = {};
        var Timer = {
            set: function(period, repeat, callback, userdata) {
                var handle = _host_timer_set(period, repeat ? 1 : 0);
                __timer_callbacks[handle] = { fn: callback, userdata: userdata, repeat: repeat };
                return handle;
            },
            clear: function(handle) {
                _host_timer_clear(handle);
                delete __timer_callbacks[handle];
            }
        };

        function __invoke_timer(handle) {
            var item = __timer_callbacks[handle];
            if (item && item.fn) {
                try {
                    item.fn(item.userdata);
                } catch(e) {
                    print("Timer error:", e);
                }
                if (!item.repeat) {
                    delete __timer_callbacks[handle];
                }
            }
        }

        function __invoke_callback(cb_id, result_json, error_code, error_message) {
            var item = __callbacks[cb_id];
            if (item && item.fn) {
                delete __callbacks[cb_id];
                var result = result_json ? JSON.parse(result_json) : null;
                try {
                    item.fn(result, error_code, error_message, item.userdata);
                } catch(e) {
                    print("Callback error:", e);
                }
            }
        }

        function __dispatch_event(event_json) {
            var evt = JSON.parse(event_json);
            for (var i = 0; i < __event_handlers.length; i++) {
                try {
                    __event_handlers[i].fn(evt, __event_handlers[i].userdata);
                } catch(e) {
                    print("EventHandler error:", e);
                }
            }
        }

        function __dispatch_status(status_json) {
            var st = JSON.parse(status_json);
            for (var i = 0; i < __status_handlers.length; i++) {
                try {
                    __status_handlers[i].fn(st, __status_handlers[i].userdata);
                } catch(e) {
                    print("StatusHandler error:", e);
                }
            }
        }
        """
        self.ctx.eval(bootstrap_js)

    def _host_print(self, msg: str):
        print(f"[{self.device.name}] {msg}", flush=True)

    def _host_get_component_status(self, key: str) -> Optional[str]:
        if ":" in key:
            t, cid = key.split(":", 1)
            comp = self.device.get_component(t, int(cid))
        else:
            comp = self.device.get_component(key, 0)
        return json.dumps(comp.get_status()) if comp else None

    def _host_get_component_config(self, key: str) -> Optional[str]:
        if ":" in key:
            t, cid = key.split(":", 1)
            comp = self.device.get_component(t, int(cid))
        else:
            comp = self.device.get_component(key, 0)
        return json.dumps(comp.get_config()) if comp else None

    def _host_get_device_info(self) -> str:
        return json.dumps(self.device.get_device_info())

    def _host_timer_set(self, period_ms: int, repeat: int) -> int:
        self._timer_seq += 1
        handle = self._timer_seq

        async def _timer_loop():
            delay = max(0.001, period_ms / 1000.0)
            while True:
                await asyncio.sleep(delay)
                self.ctx.eval(f"__invoke_timer({handle});")
                if not repeat:
                    break

        task = asyncio.create_task(_timer_loop())
        self._timers[handle] = task
        return handle

    def _host_timer_clear(self, handle: int):
        task = self._timers.pop(handle, None)
        if task:
            task.cancel()

    def _host_shelly_call(self, method: str, params_str: str, cb_id: Optional[str]):
        params = json.loads(params_str) if params_str else {}

        async def _async_call():
            try:
                res = await self.device.rpc_handler.execute(method, params)
                res_json = json.dumps(res) if res is not None else "null"
                if cb_id:
                    self.ctx.eval(f"__invoke_callback({json.dumps(cb_id)}, {json.dumps(res_json)}, 0, null);")
            except Exception as e:
                code = getattr(e, "code", -1)
                msg = getattr(e, "message", str(e))
                if cb_id:
                    self.ctx.eval(f"__invoke_callback({json.dumps(cb_id)}, null, {code}, {json.dumps(msg)});");

        asyncio.create_task(_async_call())

    def on_event(self, data: Dict[str, Any]):
        evt_json = json.dumps(data)
        self.ctx.eval(f"__dispatch_event({json.dumps(evt_json)});");

    def on_status_change(self, data: Dict[str, Any]):
        st_json = json.dumps(data)
        self.ctx.eval(f"__dispatch_status({json.dumps(st_json)});");

    def load_script(self, code: str):
        return self.ctx.eval(code)

    def stop(self):
        for task in self._timers.values():
            task.cancel()
        self._timers.clear()
