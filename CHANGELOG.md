# Changelog

## [1.0.0] - 2025-07-19

### Changed
- Renamed integration from "metoffice" to "weatherbitch" 
- Updated domain in manifest.json from "metoffice" to "weatherbitch"
- Updated name in manifest.json from "Met Office" to "Weather Bitch"
- Updated DOMAIN constant in const.py from "metoffice" to "weatherbitch"
- Added required version field "1.0.0" to manifest.json for Home Assistant compatibility

### Fixed
- Fixed Home Assistant loader error about missing version key in manifest
- Fixed domain mismatch between manifest.json and const.py

### Notes
- These changes were necessary to make the forked component work as a separate integration
- Component is now properly recognized by Home Assistant as "weatherbitch"

## [1.0.1] - 2025-07-20

### Updated
- Pulled latest changes from upstream dev branch
- Re-applied weatherbitch compatibility fixes after merge
- Maintained all Home Assistant compatibility changes

### Technical
- Fetched from: https://github.com/blurphanatic/core.git (branch: dev)
- Component source: homeassistant/components/weatherbitch/
