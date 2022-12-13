import {promises as fs} from 'fs'

// Read the settings file and return it
export function read() {
  return fs.readFile('settings.json', 'utf-8')
    .then(data => JSON.parse(data));
}

// Write settings to the file
export function write(settings) {
  return fs.writeFile('settings.json', JSON.stringify(settings));
}
