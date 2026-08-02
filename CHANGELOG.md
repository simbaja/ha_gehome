
# GE Home Appliances (SmartHQ) Changelog

## 2026.8.0

- Feature: Added per-door binary sensors for refrigerators (fridge left/right, freezer, drawer, and Fridge V2 doors)
- Feature: Added setpoint and setpoint limit temperature sensors for refrigerators
- Feature: Added water filter remaining life (%) and days remaining sensors for refrigerators
- Feature: Added AutoFill pitcher state/presence/full and hydration station total volume entities for refrigerators
- Feature: Added alert notification binary sensors for all refrigerator alert conditions
- Feature: Added oven cavity diagnostic sensors (delay time remaining, elapsed cook time, probe present)
- Feature: Added appliance setting controls for ovens (control lock, 12-hour shutoff, convection conversion, sound level, end tone, clock format, and mode temperature bounds)
- Feature: Added additional resource monitoring sensors (Wh cumulative energy, mL hot/cold water, gas type)
- Bugfix: Fixed turbo cool switch mapping on refrigerators
- Bugfix: Fixed fridge interior light entity disappearing when light is turned off (0 brightness) at startup [#545]

## 2026.7.0-dev0

- Feature: Added interactive multi-factor authentication (MFA) support to the config and re-auth flows. Accounts with email MFA enabled can now be set up directly in Home Assistant, which prompts for the emailed verification code (with a resend option) instead of failing.
- Feature: Added support for toaster oven appliances and toaster oven light control
- Feature: Added ability to change between mac/serial for unique id generation
- Feature: Improved handling of auto mode for some WACs [#536]
- Change: Reworded the config and re-auth flow screens to explain the sign-in and verification-code steps.
- Bugfix: Made fridge temperature setting getters defensive [#529, #418, #503, #499]
- Bugfix: Fixed issue with laundry dryer sheet interpretation [#444]
- Bugfix: Fixed issue with oven temperatures displaying negative temperatures when using Celsius when oven is off

## 2026.6.0

- Feature: Added hood fan and light entities [#507]
- Feature: Added cooktop-specific entities (sensors and controls)
- Feature: Added kitchen timer to cooktop as number entities (in minutes)
- Feature: Added gas cooktop to known device mapping
- Feature: Added quiet/turbo mode for AC-capable appliances [#397]
- Feature: Added potential support for dishwasher delay start on some models [#434]
- Feature: Added cross-appliance resource usage sensors to all supported appliances (instantaneous power, cumulative energy, hot/cold water usage, gas usage) where reported by the appliance [#335,#492]
- Change: Improved login error messages now specifically indicate when MFA or Terms of Service acceptance is required
- Change: Refactored common cooktop logic to apply to both cooktop and oven devices
- Change: Tightened typing for binary sensor and sensor device/state classes
- Change: Removed AC-specific demand response sensors from WAC/BIAC (superseded by cross-appliance resource sensors)
- Bugfix: Fixed dehumidifier sensors incorrectly typed (should be binary sensors)
- Bugfix: Fixed typing issue in oven target_temperature
- Bugfix: Avoid returning None for oven target_temperature [#457]
- Bugfix: Allow eco mode access for non-heating split ACs [#474]
- Bugfix: Fix oven off mode to use HA's STATE_OFF constant [#485]
- Bugfix: Restore appliance availability on state update [#495]
- Bugfix: Ignore non-printable serial numbers and fall back to MAC as unique device identifier [#502]

## 2026.2.0

- Feature: Added DRY mode to HVAC options and mappings [#441]
- Feature: Added GeWasherCycleButton to WasherDryerApi [#462]
- Feature: Added DishDrawer User Setting wifi_enabled (read only) [#463]
- Feature: Added native fan and light entities for range hoods
- Change: Changed mode names for Haier water heaters [#442]
- Change: Made LAUNDRY_MACHINE_STATE diagnostic on all appliances [#447]
- Bugfix: Cooktop Sensor fixes [#440, #454]
- Bugfix: Persist ApplianceApis on reconnect to prevent duplicate entities [#464]

## 2025.12.0

- Bugfix: Climate heat mode setting [#433, #435]
- Feature: Changed time-related entities to be durations instead of text [#312]

## 2025.11.0

- Breaking: changed name of some SAC/WAC entities to have a AC prefix
- Feature: Added heat mode for Window ACs
- Feature: Added support for Advantium
- Feature: Brand inference and stale device cleanup
- Feature: Added support for new hoods that require state/control ERDs
- Feature: Added entity categorization
- Feature: Added dishwasher remote commands
- Change: Refactored code internally to improve reliability
- Change: Cleaned up initialization and config flow
- Bugfix: Fixed temperature unit for ovens [#248, #328, #344]
- Bugfix: Water heater mode setting [#107]

## 2025.7.0

- Change: Silenced string prep warning [#386] (@derekcentrico)
- Feature: Enabled Washer/Dryer remote start [#369] (@derekcentrico)
- Feature: Enabled K-cup refrigerator functionality [#101] (@derekcentrico)

## 2025.5.0

- Bugfix: Fixed helper deprecations
- Feature: Added boost/active states for water heaters
- Change: Improved documentation around terms of acceptance

## 2025.2.1

- Bugfix: Fixed #339

## 2025.2.0

- Breaking: Changed dishwasher pods to number
- Breaking: Removed outdated laundry status sensor
- Feature: Added under counter ice maker controls and sensors
- Feature: Changed versioning scheme
- Bugfix: Updated SDK to fix broken types

## 0.6.15

- Feature: Improved Support for Laundry
- Breaking: Some enums changed names/values and may need updates to client code
- Bugfix: More deprecation fixes

## 0.6.14

- Bugfix: Error checking socket status [#304]
- Bugfix: Error with setup [#301]
- Bugfix: Logger deprecations

## 0.6.13

- Bugfix: Deprecations [#290] [#297]

## 0.6.12

- Bugfix: Deprecations [#271]

## 0.6.11

- Bugfix: Fixed convertable drawer issue [#243]
- Bugfix: Updated app types to include electric cooktops [#252]
- Bugfix: Updated clientsession to remove deprecation [#253]
- Bugfix: Fixed error strings
- Bugfix: Updated climate support for new flags introduced in 2024.2.0

## 0.6.10

- Bugfix: Removed additional deprecated constants [#229]
- Bugfix: Fixed issue with climate entities [#228]

## 0.6.9

- Added additional fridge controls [#200]
- Bugfix: Additional auth stability improvements [#215, #211]
- Bugfix: Removed deprecated constants [#218]

## 0.6.8

- Added Dehumidifier [#114]
- Added oven drawer sensors
- Added oven current state sensors [#175]
- Added descriptors to manifest [#181]
- Bugfix: Fixed issue with oven lights [#174]
- Bugfix: Fixed issues with dual dishwasher [#161]
- Bugfix: Fixed disconnection issue [#169]

## 0.6.7

- Bugfix: fixed issues with dishwasher [#155]
- Added OIM descaling sensor [#154]

## 0.6.6

- Bugfix: Fixed issue with region setting (EU accounts) [#130]
- Updated the temperature conversion (@partsdotpdf)
- Updated configuration documentation
- Modified dishwasher to include new functionality (@NickWaterton)
- Bugfix: Fixed oven typo (@jdc0730) [#149]
- Bugfix: UoM updates (@morlince) [#138]
- Updated light control (@tcgoetz) [#144]
- Dependency version bumps

## 0.6.5

- Added beverage cooler support (@kksligh)
- Added dual dishwasher support (@jkili)
- Added initial espresso maker support (@datagen24)
- Added whole home water heater support (@seantibor)

## 0.6.3

- Updated detection of invalid serial numbers (#89)
- Updated implementation of number entities to fix deprecation warnings (#85)

## 0.6.2

- Fixed issue with water heater naming when no serial is present
- Initial support for built-in air conditioners (@DaveZheng)

## 0.6.1

- Fixed issue with water filter life sensor (@rgabrielson11)

## 0.6.0

- Requires HA 2021.12.x or later
- Enabled authentication to both US and EU regions
- Changed the sensors to use native value/uom
- Changed the temperatures to always be natively fahrenheit (API appears to always use this system) (@vignatyuk)
- Initial support for Microwaves (@mbcomer, @mnestor)
- Initial support for Water Softeners (@npentell, @drjeff)
- Initial support for Opal Ice Makers (@mbcomer, @knobunc)
- Initial support for Coffee Makers (@alexanv1)
- Updated deprecated icons (@mjmeli, @schmittx)

## 0.5.0

- Initial support for oven hoods (@digitalbites)
- Added extended mode support for ovens
- Added logic to prevent multiple configurations of the same GE account
- Fixed device info when serial not present (@Xe138)
- Fixed issue with ovens when raw temperature not available (@chadohalloran)
- Fixed issue where Split A/C temperature sensors report UOM incorrectly (@RobertusIT)
- Added convertable drawer mode, proximity light, and interior lights to fridge (@groto27, @elwing00)

## 0.4.3

- Enabled support for appliances without serial numbers
- Added support for Split A/C units (@RobertusIT)
- Added support for Window A/C units (@mbrentrowe, @swcrawford1)
- Added support for Portable A/C units (@luddystefenson)
- Fixed multiple binary sensors (bad conversion from enum) (@steveredden)
- Fixed delay time interpretation for laundry (@steveredden, @sweichbr)
- Fixed startup issue when encountering an unknown unit type(@chansearrington, @opie546)
- Fixed interpretation of A/C demand response power (@garulf)
- Fixed issues with updating disabled entities (@willhayslett)
- Advantium fixes (@willhayslett)

## 0.4.1

- Fixed an issue with dryer entities causing an error in HA (@steveredden)

## 0.4.0

- Implemented Laundry Support (@warrenrees, @ssindsd)
- Implemented Water Filter Support (@bendavis, @tumtumsback, @rgabrielson11)
- Implemented Initial Advantium Support (@ssinsd)
- Bug fixes for ovens (@TKpizza)
- Additional authentication error handling (@rgabrielson11)
- Additional dishwasher functionality (@ssinsd)
- Introduced new select entity (@bendavis)
- Miscellaneous entity bug fixes/refinements
- Integrated new version of SDK

## 0.3.12

- Initial tracked version
