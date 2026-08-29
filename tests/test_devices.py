import pytest
import asyncio
from yllehs.device import VirtualDevice
from yllehs.rpc import RPCError

@pytest.mark.asyncio
async def test_gen1_shelly1():
    dev = VirtualDevice(name="test-shelly1", model="shelly1", port=8079)
    assert dev.gen == 1
    assert dev.runtime is None  # Gen 1 has no JS scripting engine
    assert "relay:0" in dev.components
    assert "switch:0" not in dev.components
    
    info = dev.get_device_info()
    assert info["type"] == "SHSW-1"
    
    status = dev.get_status()
    assert "relays" in status
    assert status["relays"][0]["ison"] is False
    
    # Toggle relay
    comp = dev.get_component("relay", 0)
    comp.set_state("on")
    assert comp.get_status()["ison"] is True

@pytest.mark.asyncio
async def test_gen2_plus_1_topology():
    dev = VirtualDevice(name="test-plus1", model="plus-1", port=8080)
    info = dev.get_device_info()
    assert info["model"] == "plus-1"
    assert info["gen"] == 2
    assert "switch:0" in dev.components
    assert "input:0" in dev.components
    assert "switch:1" not in dev.components
    assert "input:1" not in dev.components

@pytest.mark.asyncio
async def test_gen3_1pm_topology():
    dev = VirtualDevice(name="test-gen3", model="1pm-gen3", port=8085)
    info = dev.get_device_info()
    assert info["gen"] == 3
    assert "switch:0" in dev.components
    assert "input:0" in dev.components

@pytest.mark.asyncio
async def test_rpc_switch_toggle():
    dev = VirtualDevice(name="test-switch", model="plus-1", port=8080)
    
    status = await dev.rpc_handler.execute("Switch.GetStatus", {"id": 0})
    assert status["output"] is False
    
    res = await dev.rpc_handler.execute("Switch.Set", {"id": 0, "on": True})
    assert res["was_on"] is False
    
    status = await dev.rpc_handler.execute("Switch.GetStatus", {"id": 0})
    assert status["output"] is True
    
    # Toggle
    await dev.rpc_handler.execute("Switch.Toggle", {"id": 0})
    status = await dev.rpc_handler.execute("Switch.GetStatus", {"id": 0})
    assert status["output"] is False

@pytest.mark.asyncio
async def test_rpc_invalid_component():
    dev = VirtualDevice(name="test-invalid", model="plus-1", port=8080)
    with pytest.raises(RPCError):
        await dev.rpc_handler.execute("Switch.GetStatus", {"id": 5})

@pytest.mark.asyncio
async def test_javascript_event_and_rpc():
    dev = VirtualDevice(name="test-js", model="plus-1", port=8080)
    
    script = """
    var handled = false;
    Shelly.addEventHandler(function(event) {
        if (event.component === 'input:0' && event.event === 'btn_down') {
            handled = true;
            Shelly.call('Switch.Set', { id: 0, on: true });
        }
    });
    """
    dev.runtime.load_script(script)
    
    # Trigger input event
    dev.components["input:0"].trigger(state=True, event_name="btn_down")
    
    await asyncio.sleep(0.05)
    
    assert dev.runtime.ctx.eval("handled") is True
    assert dev.components["switch:0"].status["output"] is True

@pytest.mark.asyncio
async def test_javascript_timer():
    dev = VirtualDevice(name="test-timer", model="plus-1", port=8080)
    
    script = """
    var count = 0;
    Timer.set(20, false, function() {
        count += 1;
    });
    """
    dev.runtime.load_script(script)
    
    await asyncio.sleep(0.06)
    assert dev.runtime.ctx.eval("count") == 1
    dev.stop()

@pytest.mark.asyncio
async def test_shelly_get_component_status_sys_uptime():
    dev = VirtualDevice(name="test-sys", model="plus-1", port=8080)
    
    script = """
    var uptime = Shelly.getComponentStatus("sys").uptime;
    var uptimeWithId = Shelly.getComponentStatus("sys", 0).uptime;
    """
    dev.runtime.load_script(script)
    
    assert dev.runtime.ctx.eval("typeof uptime") == "number"
    assert dev.runtime.ctx.eval("uptime >= 0") is True
    assert dev.runtime.ctx.eval("uptimeWithId >= 0") is True

@pytest.mark.asyncio
async def test_switch_set_notifies_add_event_handler():
    dev = VirtualDevice(name="test-event", model="plus-1", port=8080)
    
    script = """
    var eventCount = 0;
    var lastEvent = null;
    Shelly.addEventHandler(function(event) {
        eventCount += 1;
        lastEvent = event;
        print("Event triggered for component:", event.component);
    });
    """
    dev.start_script()
    dev.runtime.load_script(script)
    
    # Switch is initialized to false. Setting to true triggers event.
    await dev.rpc_handler.execute("Switch.Set", {"id": 0, "on": True})
    await asyncio.sleep(0.01)
    
    assert dev.runtime.ctx.eval("eventCount") == 1
    assert dev.runtime.ctx.eval("lastEvent.component") == "switch:0"
    assert dev.runtime.ctx.eval("lastEvent.event") == "toggle"
    assert dev.runtime.ctx.eval("lastEvent.info.state") is True
    
    # Setting to true again (no state change) -> no additional event
    await dev.rpc_handler.execute("Switch.Set", {"id": 0, "on": True})
    await asyncio.sleep(0.01)
    assert dev.runtime.ctx.eval("eventCount") == 1
    
    # Setting to false (state change) -> triggers second event
    await dev.rpc_handler.execute("Switch.Set", {"id": 0, "on": False})
    await asyncio.sleep(0.01)
    assert dev.runtime.ctx.eval("eventCount") == 2
    assert dev.runtime.ctx.eval("lastEvent.info.state") is False

@pytest.mark.asyncio
async def test_device_name_with_uppercase_and_spaces_in_js():
    dev = VirtualDevice(name="LIVING ROOM ALARM", model="plus-1", port=8080)
    
    script = """
    var devInfo = Shelly.getDeviceInfo();
    var devNameFromInfo = devInfo.name;
    
    var sysConfig = Shelly.getComponentConfig("sys");
    var devNameFromSys = sysConfig.device.name;
    """
    dev.start_script()
    dev.runtime.load_script(script)
    
    assert dev.runtime.ctx.eval("devNameFromInfo") == "LIVING ROOM ALARM"
    assert dev.runtime.ctx.eval("devNameFromSys") == "LIVING ROOM ALARM"

@pytest.mark.asyncio
async def test_shelly_get_components_rpc():
    dev = VirtualDevice(name="test-components", model="plus-1", port=8080)
    res = await dev.rpc_handler.execute("Shelly.GetComponents")
    assert "components" in res
    assert res["total"] == len(dev.components)
    keys = [c["key"] for c in res["components"]]
    assert "switch:0" in keys
    assert "input:0" in keys
    assert "sys:0" in keys
    assert "wifi:0" in keys
