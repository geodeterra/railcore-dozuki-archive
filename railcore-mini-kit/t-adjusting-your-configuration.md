---
layout: default
title: "T) Adjusting Your Configuration"
---


# T) Adjusting Your Configuration

Category: [RailCore® Mini Kit](index.md) · Original: <https://railcore.dozuki.com/Guide/T)+Adjusting+Your+Configuration/42>

**Difficulty:** Moderate  
**Time required:** 1 hour  
**Author:** Ben Withem  
**Steps:** 6  
**Last modified on Dozuki:** 2022-04-04

## Step 1: Adjusting the Z probe height

- Home all 3 axis, and level the bed. Run `G32` at least 3 times, so your bed is as level as it can be.
- Run `G28 Z` to return to the center of the bed. Your bed will move to Z10.
- Run the following gcode, so we can move below Z0 if needed:
  - `G92 Z12`
- Place a sheet of paper on your bed.
- Using the jog buttons in duet web control, slowly jog down until your nozzle just contacts the paper (slide the paper around until you can feel the nozzle touching it. Use the smallest steps as you get close)
- Remove the piece of paper, and run the "Probe Point" macro (click on the macro and it will ask you if you want to run it)
- The printer will re-home Z, stopping when the probe triggers.

## Step 2: Adjusting the Z Probe Height - Continued

- In duet web control, find the current Z height value, and record it.
- Edit your config.g file, towards the end of it find the following line
  - `G31 X2 Y42 Z2.65 P25`
- Edit the Z value, put in the value from Duet Web control.
- Save the config.g and restart.

## Step 3: Adjusting Max X / Y / Z

- **Caution:** You can break your printer with this step, be cautious.
- Run this command to allow movement beyond what the printer is physically capable:
  - `M208 X400 Y400 Z700`
- Use the jog buttons in duet web control to slowly jog the hotend to max Y. Stop just before it hits the rear X carriage, and record the value.
- Use the jog buttons in duet web control to slowly jog the hotend to max X, near a leadscrew. Stop before it contacts a leadscrew with the fan. Record the X value.
- Use the jog buttons in duet web control to slowly move the bed down by increasing the Z height. Stop before the bed contacts the Z couplers, and record the Z height.
- Jog the bed back up, and center the hotend.
- Find this line in your config.g and replace the values with the ones you recorded: `M208 X290 Y290 Z280`

## Step 4: Hotend PID tuning

- **Caution:** This will heat your hotend up. Stay near your printer in case of problems.
- **Caution:** Be sure your hotend is not near your bed, or touching anything.
- Run this command:
  - `M303 T0 S250`
- Your hotend will go through a PID tuning cycle. When it's done, run M307 H1 to see the values, it will report something like this:
  - `Auto tuning heater 1 completed after 3 idle and 13 tuning cycles in 308 seconds. This heater needs the following M307 command: M307 H1 R4.275 K0.605:0.651 D2.29 E1.35 S1.00 B0 V23.9`
- Using that as an example, find the `M307 H1` line in your config.g and adjust it as follows, using the values for gain, time constant, dead time, and voltage from your M307 output.
  - `M307 H1 R4.275 K0.605:0.651 D2.29 E1.35 S1.00 B0 V23.9`

## Step 5: Bed PID Tuning

- **Caution:** This will heat your bed up. Stay near your printer in case of problems.
- **Caution:** Be sure nothing is on your bed.
- Run this command:
  - `M303 H0 S60`
- Your bed will go through a PID tuning cycle. When it's done, run M307 H0 to see the values, it will report something like this:
  - `Heater 0: heating rate 0.427, cooling rate 0.344, dead time 6.25, max PWM 1.00, mode PID Predicted max temperature rise 117°C PID parameters: heating P66.9 I1.494 D292.5, steady P66.9 I3.509 D292.5`
- Using that as an example, find the M307 H0 line in your config.g and adjust it as follows, using the values for gain, time constant, dead time, and voltage from your M307 output.
  - `M307 H0 R0.427 K0.344:0.000 D6.25 E1.35 S1.00 B0`

## Step 6: Test the Extruder Direction

- Attach the PTFE guide tube to the extruder input, and pass the other end through the PTFE holder on the right side of the printer.
- Set your hotend to an appropriate temperature for your filament.
- Feed some filament in through the feed tube, until it reaches the extruder.
- Using the DWC interface, slowly extrude some filament, it should grab the filament and pull it in.
- If instead it pushes the filament back out, find this line in your config.g and change the `S0` to an `S1`
  - `M569 P3 S0`


Previous: [S) First Moves](s-first-moves.md) · [RailCore® Mini Kit guide list](index.md)


---

Original page: <https://railcore.dozuki.com/Guide/T)+Adjusting+Your+Configuration/42>. Written by Ben Withem on railcore.dozuki.com. This copy was captured on 2026-11-16 and is licensed under [Creative Commons Attribution-ShareAlike 3.0 (CC BY-SA 3.0)](https://creativecommons.org/licenses/by-sa/3.0/), the license stated on the original site. This is an unofficial community mirror and is not affiliated with RailCore Labs, LLC. RAILCORE is a registered trademark of RailCore Labs, LLC.
