---
layout: default
title: "T) Adjusting Your Configuration"
---


# T) Adjusting Your Configuration

Category: [RailCore II](index.md) · Original: <https://railcore.dozuki.com/Guide/T)+Adjusting+Your+Configuration/20>

**Difficulty:** Moderate  
**Time required:** No estimate  
**Author:** Tony Akens  
**Steps:** 9  
**Last modified on Dozuki:** 2021-08-04

## Step 1: Adjusting the Z probe height

- Home all 3 axis, and level the bed. Run G32 at least 3 times, so your bed is as level as it can be.
- Run G28 Z to return to the center of the bed. Your bed will move to Z10.
- Run the following gcode, so we can move below Z0 if needed:
  - <span style="color:#15a1d6" title="light_blue bullet">&#9679;</span> G92 Z12
- Place a sheet of paper on your bed.
- Using the jog buttons in duet web control, slowly jog down until your nozzle just contacts the paper (slide the paper around until you can feel the nozzle touching it. Use the smallest steps as you get close)
- Remove the piece of paper, and run the "Probe Point" macro (click on the macro and it will ask you if you want to run it)
- The printer will re-home Z, stopping when the probe triggers.

## Step 2: Adjusting the Z Probe Height - Continued

- In duet web control, find the current Z height value, and record it.
- Edit your config.g file, towards the end of it find the following line
  - G31 X2 Y42 Z2.65 P25
- Edit the Z value, put in the value from Duet Web control.
- Save the config.g and restart.

## Step 3: Adjusting Max X / Y / Z

- You can break your printer with this step, be cautious.
- Run this command to allow movement beyond what the printer is physically capable:
  - <span style="color:#15a1d6" title="light_blue bullet">&#9679;</span> M208 X400 Y400 Z700
- Use the jog buttons in duet web control to slowly jog the hotend to max Y. Stop just before it hits the rear X carriage, and record the value.
- Use the jog buttons in duet web control to slowly jog the hotend to max X, near a leadscrew. Stop before it contacts a leadscrew with the fan. Record the X value.
- Use the jog buttons in duet web control to slowly move the bed down by increasing the Z height. Stop before the bed contacts the Z couplers, and record the Z height.
- Jog the bed back up, and center the hotend.
- Find this line in your config.g and replace the values with the ones you recorded: M208 X290 Y290 Z280

## Step 4: Hotend PID tuning

- **Caution:** This will heat your hotend up. Stay near your printer in case of problems.
- **Caution:** Be sure your hotend is not near your bed, or touching anything.
- Run this command:
  - <span style="color:#15a1d6" title="light_blue bullet">&#9679;</span> M303 H1 S250
- Your hotend will go through a PID tuning cycle. When it's done, run M307 H1 to see the values, it will report something like this:
- Heater 0 model: gain 199.0, time constant 962.6, dead time 4.5, max PWM 1.00, calibration voltage 24.2
- Using that as an example, find the M307 H1 line in your config.g and adjust it as follows, using the values for gain, time constant, dead time, and voltage from your M307 output
- M307 H1 A199.0 C962.6 D4.5 V24.2 B0

## Step 5: Bed PID Tuning

- **Caution:** This will heat your bed up. Stay near your printer in case of problems.
- **Caution:** Be sure nothing is on your bed.
- Run this command:
  - <span style="color:#15a1d6" title="light_blue bullet">&#9679;</span> M303 H0 S60
- Your bed will go through a PID tuning cycle. When it's done, run M307 H0 to see the values, it will report something like this:
- Heater 0 model: gain 170.9, time constant 771.5, dead time 4.5, max PWM 1.00, calibration voltage 24.1
- Using that as an example, find the M307 H0 line in your config.g and adjust it as follows, using the values for gain, time constant, dead time, and voltage from your M307 output.
- M307 H0 A170.9 C771.5 D5.2 V24.1 B0

## Step 6: Hot Tighten Your Nozzle

- E3D strongly recommends tightening your nozzle while hot.
- To do so, after you've PID tuned, run the following to allow your hotend to go above 280C
  - <span style="color:#15a1d6" title="light_blue bullet">&#9679;</span> M143 S295
- Run this to set your hotend to 285C, or set it in the DWC interface
  - <span style="color:#15a1d6" title="light_blue bullet">&#9679;</span> M104 S285
- Once your hotend is at 285C carefully tighten the nozzle
- Once tightened, turn off your hotend in Duet Web Control

## Step 7: Test the Extruder Direction

- Attach the PTFE guide tube to the extruder input, and pass the other end through the PTFE holder on the right side of the printer.
- Set your hotend to an appropriate temperature for your filament.
- Feed some filament in through the feed tube, until it reaches the extruder.
- Using the DWC interface, slowly extrude some filament, it should grab the filament and pull it in.
- If instead it pushes the filament back out, find this line in your config.g and change the S0 to an S1
  - <span style="color:#15a1d6" title="light_blue bullet">&#9679;</span> M569 P3 S0

## Step 8: Increasing the Z homing Speed

- A common request is to increase the speed the Z axis homes. Be careful with this change, you can damage your printer.
- Edit the config.g file and find the following line
  - <span style="color:#15a1d6" title="light_blue bullet">&#9679;</span> M558 P9 X0 Y0 Z1 H5 F50 T6000 A5 S0.02
- Change the "F50" value to a higher value to increase the speed. "F100" is twice as fast.
- A value of F150 should suffice without being too fast to break anything if homing is already confirmed working.

## Step 9: Extra Fasteners

- Railcore kits include extra hardware, don't be alarmed that you've reached the end and have some left - they're spares!


Previous: [S) First Moves](s-first-moves.md) · [RailCore II guide list](index.md)


---

Original page: <https://railcore.dozuki.com/Guide/T)+Adjusting+Your+Configuration/20>. Written by Tony Akens on railcore.dozuki.com. This copy was captured on 2026-11-16 and is licensed under [Creative Commons Attribution-ShareAlike 3.0 (CC BY-SA 3.0)](https://creativecommons.org/licenses/by-sa/3.0/), the license stated on the original site. This is an unofficial community mirror and is not affiliated with RailCore Labs, LLC. RAILCORE is a registered trademark of RailCore Labs, LLC.
