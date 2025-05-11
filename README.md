# GE Home Appliances (SmartHQ)

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)
[![hacs][hacsbadge]][hacs]

Integration for GE WiFi-enabled appliances into Home Assistant.  This integration currently supports the following devices:

- Fridge
- Oven
- Dishwasher / F&P Dual Dishwasher 
- Laundry (Washer/Dryer)
- Whole Home Water Filter
- Whole Home Water Softener
- Whole Home Water Heater
- A/C (Portable, Split, Window, Built-In)
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

## Installation (Manual)

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
2. If you do not have a `custom_components` directory (folder) there, you need to create it.
3. In the `custom_components` directory (folder) create a new folder called `ge_home`.
4. Download _all_ the files from the `custom_components/ge_home/` directory (folder) in this repository.
5. Place the files you downloaded in the new directory (folder) you created.
6. Restart Home Assistant
7. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "GE Home"

## Installation (HACS)

Please follow directions [here](https://hacs.xyz/docs/faq/custom_repositories/), and use https://github.com/simbaja/ha_gehome as the repository URL.

## Configuration

Configuration is done via the HA user interface. You need to have your device registered with the [SmartHQ](https://www.geappliances.com/connect) website.

Once the HACS Integration of GE Home is completed:

1. Navigate to Settings --> Devices & Services
2. Click **Add Integration** blue button on the bottom-right of the page
3. Locate the **GE Home (SmartHQ)** "Brand" (Integration)
4. Open a new browser tab and navigate to <https://accounts.brillion.geappliances.com> where you can verify your username/password (helpful) but more importantly Accept the TermsOfUseAgreement (required!)
5. Click on the integration, and you will be prompted to enter a Username, Password and Location (US or EU)
6. Enter the email address you used to register/connect your device as the Username
7. Same with the password
8. Select the region you registered your device in (US or EU).
9. Once you submit, the integration will log in and get all your connected devices.
10. You can define in which area you device is, then click **Finish**
11. Your sensors should appear as **sensor.<serial_number>_<sensor_function>**
    ie: sensor.fs12345678_dishwasher_cycle_name

## Change Log

Please click [here](CHANGELOG.md) for change information.

[commits-shield]: https://img.shields.io/github/commit-activity/y/simbaja/ha_gehome.svg?style=for-the-badge
[commits]: https://github.com/simbaja/ha_gehome/commits/master
[hacs]: https://github.com/custom-components/hacs
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/simbaja/ha_gehome.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-Jack%20Simbach%20%40simbaja-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/simbaja/ha_gehome.svg?style=for-the-badge
[releases]: https://github.com/simbaja/ha_gehome/releases
