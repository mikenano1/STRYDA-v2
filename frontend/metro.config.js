const { getDefaultConfig } = require("expo/metro-config");
const { withNativeWind } = require("nativewind/metro");

const config = getDefaultConfig(__dirname);

// Reduce the number of workers to decrease resource usage
config.maxWorkers = 2;

module.exports = withNativeWind(config, { input: "./global.css" });
