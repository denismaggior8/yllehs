// Shelly JavaScript event & status listener
print("Alarm controller script initialized on virtual Shelly!");

// 1. Status change listener for switch state
Shelly.addStatusHandler(function(status) {
    if (status.component === "switch:0" && status.delta && typeof status.delta.output !== "undefined") {
        print("[SCRIPT NOTIFICATION] Switch 0 changed state -> output:", status.delta.output, "(source: " + status.delta.source + ")");
    }
});

// 2. Button/Input event listener
Shelly.addEventHandler(function(event) {
    if (event.component === "input:0") {
        print("[SCRIPT NOTIFICATION] Input 0 triggered event:", event.event);
    }
});
