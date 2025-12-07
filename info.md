# GE Home Appliances (SmartHQ)

Integration for GE WiFi-enabled appliances into Home Assistant.  This integration currently support the following devices:

- Fridge
- Oven
- Dishwasher / F&P Dual Dishwasher
- Laundry (Washer/Dryer)
- Whole Home Water Filter
- Whole Home Water Softener
- Whole Home Water Heater
- A/C (Portable, Split, Window)
- Range Hood
- Advantium
- Microwave
- Opal Ice Maker
- Coffee Maker / Espresso Maker
- Beverage Center

**Forked from Andrew Mark's [repository](https://github.com/ajmarks/ha_components).**

## Updates

Unfortunately, I'm pretty much at the end of what I can do without assistance from others with these devices that can help provide logs.  I'll do what I can to make updates if there's something broken, but I am not really able to add new functionality if I can't get a little help to do so.

## Home Assistant UI Examples
Entities card:

![Entities](https://raw.githubusercontent.com/simbaja/ha_components/master/img/appliance_entities.png)

Fridge Controls:

![Fridge controls](https://raw.githubusercontent.com/simbaja/ha_components/master/img/fridge_control.png)

Oven Controls:

![Fridge controls](https://raw.githubusercontent.com/simbaja/ha_components/master/img/oven_controls.png)

A/C Controls:

![A/C controls](https://raw.githubusercontent.com/simbaja/ha_components/master/img/ac_controls.png)


{% if installed %}
### Changes as compared to your installed version:

#### Breaking Changes

{% if version_installed.split('.') | map('int') < '2025.11.0'.split('.') | map('int') %}
- changed name of some SAC/WAC entities to have a AC prefix 
{% endif %}

{% if version_installed.split('.') | map('int') < '2025.2.0'.split('.') | map('int') %}
- Changed dishwasher pods to number
- Removed outdated laundry status sensor
{% endif %}

{% if version_installed.split('.') | map('int') < '0.6.15'.split('.') | map('int') %}
- Some enums changed names/values and may need updates to client code
{% endif %}

{% if version_installed.split('.') | map('int') < '0.6.6'.split('.') | map('int') %}
- Requires HA version 2022.12.0 or later
{% endif %}

{% if version_installed.split('.') | map('int') < '0.6.0'.split('.') | map('int') %}
- Requires HA version 2021.12.0 or later
- Enabled authentication to both US and EU regions (may require re-auth)
- Changed the sensors to use native value/uom
- Changed the temperatures to always be natively fahrenheit (API appears to always use this system) (@vignatyuk) 
{% endif %}

{% if version_installed.split('.') | map('int') < '0.4.0'.split('.') | map('int') %}
- Laundry support changes will cause entity names to be different, you will need to fix in HA (uninstall, reboot, delete leftover entitites, install, reboot)
{% endif %}

#### Changes

{% if version_installed.split('.') | map('int') < '2025.11.0'.split('.') | map('int') %}
- Refactored code internally to improve reliability
- Cleaned up initialization and config flow
{% endif %}

{% if version_installed.split('.') | map('int') < '2025.7.0'.split('.') | map('int') %}
- Silenced string prep warning [#386] (@derekcentrico)
{% endif %}

{% if version_installed.split('.') | map('int') < '2025.5.0'.split('.') | map('int') %}
- Improved documentation around terms of acceptance
{% endif %}

{% if version_installed.split('.') | map('int') < '0.5.0'.split('.') | map('int') %}
- Added logic to prevent multiple configurations of the same GE account
{% endif %}

#### Features

{% if version_installed.split('.') | map('int') < '2025.12.0'.split('.') | map('int') %}
- Changed time-related entities to be durations instead of text [#312]
{% endif %}

{% if version_installed.split('.') | map('int') < '2025.11.0'.split('.') | map('int') %}
- Added heat mode for Window ACs
- Added support for Advantium
- Brand inference and stale device cleanup
- Added support for new hoods that require state/control ERDs
- Added entity categorization
- Added dishwasher remote commands
{% endif %}

{% if version_installed.split('.') | map('int') < '2025.7.0'.split('.') | map('int') %}
- Enabled Washer/Dryer remote start [#369] (@derekcentrico)
- Enabled K-cup refrigerator functionality [#101] (@derekcentrico)
{% endif %}

{% if version_installed.split('.') | map('int') < '2025.5.0'.split('.') | map('int') %}
- Added boost/active states for water heaters
{% endif %}

{% if version_installed.split('.') | map('int') < '2025.2.0'.split('.') | map('int') %}
- Added under counter ice maker controls and sensors
- Changed versioning scheme for integration
{% endif %}

{% if version_installed.split('.') | map('int') < '0.6.15'.split('.') | map('int') %}
- Improved Support for Laundry
{% endif %}

{% if version_installed.split('.') | map('int') < '0.6.9'.split('.') | map('int') %}
- Added additional fridge controls (#200)
{% endif %}

{% if version_installed.split('.') | map('int') < '0.6.8'.split('.') | map('int') %}
- Added Dehumidifier (#114)
- Added oven drawer sensors
- Added oven current state sensors (#175)
- Added descriptors to manifest (#181)
{% endif %}

{% if version_installed.split('.') | map('int') < '0.6.7'.split('.') | map('int') %}
- Added OIM descaling sensor (#154)
{% endif %}

{% if version_installed.split('.') | map('int') < '0.6.6'.split('.') | map('int') %}
- Modified dishwasher to include new functionality (@NickWaterton)
{% endif %}

{% if version_installed.split('.') | map('int') < '0.6.5'.split('.') | map('int') %}
- Added beverage cooler support (@kksligh)
- Added dual dishwasher support (@jkili)
- Added initial espresso maker support (@datagen24)
- Added whole home water heater support (@seantibor)
{% endif %}

{% if version_installed.split('.') | map('int') < '0.6.0'.split('.') | map('int') %}
- Initial support for built-in air conditioners (@DaveZheng)
{% endif %}

{% if version_installed.split('.') | map('int') < '0.6.0'.split('.') | map('int') %}
- Initial support for Water Softeners (@npentell, @drjeff)
- Initial support for Opal Ice Makers (@mbcomer, @knobunc)
- Initial support for Microwaves (@mbcomer, @mnestor)
- Initial support for Coffee Makers (@alexanv1)
{% endif %}

{% if version_installed.split('.') | map('int') < '0.5.0'.split('.') | map('int') %}
- Support for Oven Hood units (@digitalbites)
- Added extended mode support for ovens
{% endif %}

{% if version_installed.split('.') | map('int') < '0.4.3'.split('.') | map('int') %}
- Support for Portable, Split, and Window AC units (@swcrawford1, @mbrentrowe, @RobertusIT, @luddystefenson)
{% endif %}

{% if version_installed.split('.') | map('int') < '0.4.0'.split('.') | map('int') %}
- Implemented Laundry Support (@warrenrees, @ssindsd)
- Implemented Water Filter Support (@bendavis, @tumtumsback, @rgabrielson11)
- Implemented Initial Advantium Support (@ssinsd)
- Additional authentication error handling (@rgabrielson11)
- Additional dishwasher functionality (@ssinsd)
- Introduced new select entity (@bendavis)
- Integrated new version of SDK
{% endif %}

#### Bugfixes

{% if version_installed.split('.') | map('int') < '2025.11.0'.split('.') | map('int') %}
- Climate heat mode setting [#433, #435]
{% endif %}

{% if version_installed.split('.') | map('int') < '2025.5.0'.split('.') | map('int') %}
- Fixed temperature unit for ovens [#248, #328, #344]
- Water heater mode setting [#107]
{% endif %}

{% if version_installed.split('.') | map('int') < '2025.5.0'.split('.') | map('int') %}
- Fixed helper deprecations
{% endif %}

{% if version_installed.split('.') | map('int') < '2025.2.1'.split('.') | map('int') %}
- Fix for #339
{% endif %}

{% if version_installed.split('.') | map('int') < '2025.2.0'.split('.') | map('int') %}
- Updated SDK to fix broken types
{% endif %}

{% if version_installed.split('.') | map('int') < '0.6.14'.split('.') | map('int') %}
- Error checking socket status [#304]
- Error with setup [#301]
- Logger deprecations
{% endif %}

{% if version_installed.split('.') | map('int') < '0.6.13'.split('.') | map('int') %}
- Deprecations [#290] [#297] 
{% endif %}

{% if version_installed.split('.') | map('int') < '0.6.12'.split('.') | map('int') %}
- Deprecations [#271] 
{% endif %}

{% if version_installed.split('.') | map('int') < '0.6.13'.split('.') | map('int') %}
- Deprecations [#290] [#297] 
{% endif %}

{% if version_installed.split('.') | map('int') < '0.6.12'.split('.') | map('int') %}
- Deprecations [#271] 
{% endif %}

{% if version_installed.split('.') | map('int') < '0.6.11'.split('.') | map('int') %}
- Fixed convertable drawer issue (#243)
- Updated app types to include electric cooktops (#252)
- Updated clientsession to remove deprecation (#253)
- Fixed error strings
- Updated climate support for new flags introduced in 2024.2.0
{% endif %}

{% if version_installed.split('.') | map('int') < '0.6.10'.split('.') | map('int') %}
- Removed additional deprecated constants (#229)
- Fixed issue with climate entities (#228)
{% endif %}

{% if version_installed.split('.') | map('int') < '0.6.9'.split('.') | map('int') %}
- Additional auth stability improvements (#215, #211)
- Removed deprecated constants (#218)
{% endif %}

{% if version_installed.split('.') | map('int') < '0.6.8'.split('.') | map('int') %}
- Fixed issue with oven lights (#174)
- Fixed issues with dual dishwasher (#161)
- Fixed disconnection issue (#169)
{% endif %}

{% if version_installed.split('.') | map('int') < '0.6.7'.split('.') | map('int') %}
- fixed issues with dishwasher (#155)
{% endif %}

{% if version_installed.split('.') | map('int') < '0.6.6'.split('.') | map('int') %}
- Fixed region issues after setup (#130)
- Updated the temperature conversion (#137)
- UoM updates (#138)
- Fixed oven typo (#149)
- Updated light control (#144)
{% endif %}

{% if version_installed.split('.') | map('int') < '0.6.3'.split('.') | map('int') %}
- Updated detection of invalid serial numbers (#89)
- Updated implementation of number entities to fix deprecation warnings (#85)
{% endif %}

{% if version_installed.split('.') | map('int') < '0.6.2'.split('.') | map('int') %}
- Fixed issue with water heater naming when no serial is present
{% endif %}

{% if version_installed.split('.') | map('int') < '0.6.1'.split('.') | map('int') %}
- Fixed issue with water filter life sensor (@rgabrielson11)
{% endif %}

{% if version_installed.split('.') | map('int') < '0.6.0'.split('.') | map('int') %}
- Updated deprecated icons (@mjmeli, @schmittx)
{% endif %}

{% if version_installed.split('.') | map('int') < '0.5.0'.split('.') | map('int') %}
- Advantium fixes (@willhayslett)
- Fixed device info when serial not present (@Xe138)
- Fixed issue with ovens when raw temperature not available (@chadohalloran)
- Fixed issue where Split A/C temperature sensors report UOM incorrectly (@RobertusIT)
- Added convertable drawer mode, proximity light, and interior lights to fridge (@groto27, @elwing00)
{% endif %}

{% if version_installed.split('.') | map('int') < '0.4.3'.split('.') | map('int') %}
- Bug fixes for laundry (@steveredden, @sweichbr)
- Fixed startup issue when encountering an unknown unit type(@chansearrington, @opie546)
- Fixed interpretation of A/C demand response power (@garulf)
- Fixed issues with updating disabled entities (@willhayslett)
- Advantium fixes (@willhayslett)
{% endif %}

{% if version_installed.split('.') | map('int') < '0.4.1'.split('.') | map('int') %}
- Fixed an issue with dryer entities causing an error in HA (@steveredden)
{% endif %}

{% if version_installed.split('.') | map('int') < '0.4.0'.split('.') | map('int') %}
- Bug fixes for ovens (@TKpizza)
- Miscellaneous entity bug fixes/refinements
{% endif %}

{% endif %}
