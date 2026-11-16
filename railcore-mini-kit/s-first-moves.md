---
layout: default
title: "S) First Moves"
---


# S) First Moves

Category: [RailCore® Mini Kit](index.md) · Original: <https://railcore.dozuki.com/Guide/S)+First+Moves/41>

**Difficulty:** Moderate  
**Time required:** 1 hour  
**Author:** Ben Withem  
**Steps:** 11  
**Last modified on Dozuki:** 2022-04-04

## Step 1: Safety Warning

- **Caution:** This section is written to be followed in order. DO NOT SKIP STEPS. Complete each step before moving on to the next.
- **Caution:** Your hotend fan should be turning when power is on if you connected it to an always on fan port as instructed. If not stop, power off, and fix it.

## Step 2: X (Rear) Stepper Direction

- These instructions are documented here as well: [https://reprap.org/wiki/Configuring_RepR...](https://reprap.org/wiki/Configuring_RepRapFirmware_for_a_CoreXY_printer "https://reprap.org/wiki/Configuring_RepRapFirmware_for_a_CoreXY_printer")
- Starting with the hotend over the center of the bed, issue the following in the "console" window of the Duet Web Control.
  - `G91`
  - `G1 H2 X10 F3000`
- That should move your Hotend in +X +Y (towards the right and back of the printer)
- If your hotend moves -X -Y (Left and front), find this line in the config.g and change the `S0` to `S1`:
  - `M569 P6 S0 D3`
- **Caution:** If the Y (front) stepper moves, you have the steppers in the wrong ports. Power Down and change the cables to the correct ports - see the wiring instructions.

## Step 3: Y (Front) Stepper Direction

- This is much the same as the X stepper.
- In the console window of Duet Web Control, run the following:
  - `G91`
  - `G1 H2 Y10 F3000`
- This should move the hotend in the +X and -Y Directions (towards the right side of the printer, and front of the printer)
- If it does not, find this line in your config.g value, and change the `S1` to `S0`
  - `M569 P5 S1 D3`

## Step 4: Z Stepper Direction

- **Caution:** Be sure your bed is not close to your hotend before doing this. If it is, power down and move your bed down at least 15mm by turning the leadscrews.
- In the gcode console in duet web control, run this:
  - `G1 Z10 H2`
- This should move your bed DOWN away from the hotend 10mm.
- If your Bed moves up, find the `M569 P2-4` lines in your config.g file, and change the `S0` to `S1` for all 3 lines.
- **Caution:** If only some steppers move the wrong direction, skewing the bed, you need to edit the lines only for those steppers.

## Step 5: Test X Endstop

- In the console for Duet Web Control, issue this gcode:
  - `M119`
- It should return: `Endstops - X: not stopped, Y: not stopped, Z: no endstop, Z probe: not stopped`
- Hold in the button on the X endstop switch (the one to the rear left of the printer, and run `M119` again.
- You should now get : `Endstops - X: at max stop, Y: not stopped, Z: no endstop, Z probe: not stopped`
- **Caution:** If none of the endstops show as stopped, check your X endstop connection
- **Caution:** If the Y endstop shows as stopped, you have the endstops in the wrong ports. Power down and double check they're plugged in correctly.

## Step 6: Test Y Endstop

- In the console for Duet Web Control, issue this gcode:
  - `M119`
- It should return: `Endstops - X: not stopped, Y: not stopped, Z: no endstop, Z probe: not stopped`
- Hold in the button on the Y endstop switch (the one to the rear left of the printer, and run `M119` again.
- You should now get : `Endstops - X:not stopped, Y: at max stop, Z: no endstop, Z probe: not stopped`
- If none of the endstops show as stopped, check your Y endstop connection
- If the X endstop shows as stopped, you have the endstops in the wrong ports. Power down and double check they're plugged in correctly.

## Step 7: BLTouch Testing

- Your BLTouch should be on, with a solid red light. If it's flashing, power off and check its wiring.
- Run the following gcode in the console in duet web control:
  - `M401`
  - Slightly tap the pin with your finger and the DWC interface should show `1000` on the dashboard under Z-Probe.
- Send the following to retract the probe:
  - `M402`
- The Z Probe value in DWC should now read zero.

## Step 8: X Homing Test

- **Caution:** When running the following commands, a lot can go wrong. Keep your finger near the power switch just in case. Read all of the instructions before beginnging.
- Test homing X by running the following in the gcode console:
  - `G28 X`
- Your printer should move to the left until it contacts the X endstop.

## Step 9: Y Homing Test

- **Caution:** When running the following commands, a lot can go wrong. Keep your finger near the power switch just in case. Read all of the instructions before beginnging.
- Test Homing Y by running the following in the gcode console:
  - `G28 Y`
- Your hotend should move towards the front of the printer until the Y endstop triggers against the front X carriage.

## Step 10: Z Homing Test

- **Caution:** When running the following commands, a lot can go wrong. Keep your finger near the power switch just in case. Read all of the instructions before beginnging.
- Move the bed at least 50mm below the nozzle by running this command in the gcode console (if it's already low enough, skip this)
  - `G1 H2 Z50`
- Trigger the homing of the bed by running this in the gcode console:
  - `G28 Z`
- The bltouch pin should drop, and the bed should start to move up. Tap the bltouch pin with your fingertip. It will raise and lower, tap it again. This should stop the bed.
- **Caution:** If the bed does not stop, flip the power switch immediately.
- If the bed stops as expected, re-run `G28 Z` to properly home the bed. Keep ready to hit the power switch in case something does not work.

## Step 11: Bed leveling

- Assuming all of the previous homing tests have worked, or any issues encountered have been resolved, you can now proceed with automated homing and bed leveling.
- Power off the printer, and adjust the bed manually by turning the leadscrews until it's close to level. It does not have to be perfect, but should be close.
- Power on the printer, and run the following to home all 3 axis:
  - `G28`
- To level the bed, send the following gcode:
  - `G32`
- The printer should probe 4 points on the bed, and return a status of the adjustments made.


Previous: [R) Firmware, Config, and Smoke Test](r-firmware-config-and-smoke-test.md) · [RailCore® Mini Kit guide list](index.md) · Next: [T) Adjusting Your Configuration](t-adjusting-your-configuration.md)


---

Original page: <https://railcore.dozuki.com/Guide/S)+First+Moves/41>. Written by Ben Withem on railcore.dozuki.com. This copy was captured on 2026-11-16 and is licensed under [Creative Commons Attribution-ShareAlike 3.0 (CC BY-SA 3.0)](https://creativecommons.org/licenses/by-sa/3.0/), the license stated on the original site. This is an unofficial community mirror and is not affiliated with RailCore Labs, LLC. RAILCORE is a registered trademark of RailCore Labs, LLC.
