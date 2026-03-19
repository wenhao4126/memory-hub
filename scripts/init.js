#!/usr/bin/env node

import fs from 'fs';
import path from 'path';
import chalk from 'chalk';
import ora from 'ora';

function createConfig() {
  const configDir = path.join(process.cwd(), 'config');
  const configPath = path.join(configDir, 'memory-hub.json');

  if (!fs.existsSync(configDir)) {
    fs.mkdirSync(configDir, { recursive: true });
  }

  const defaultConfig = {
    server: {
      host: 'localhost',
      port: 8000
    },
    database: {
      type: 'sqlite',
      path: './data/memory-hub.db'
    },
    agents: [],
    memory: {
      maxMemories: 10000,
      retentionDays: 90
    }
  };

  fs.writeFileSync(configPath, JSON.stringify(defaultConfig, null, 2));
  return configPath;
}

function createDataDir() {
  const dataDir = path.join(process.cwd(), 'data');
  if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, { recursive: true });
  }
  return dataDir;
}

function init() {
  const spinner = ora('Initializing Memory Hub...').start();

  try {
    const configPath = createConfig();
    createDataDir();

    spinner.succeed(chalk.green('Memory Hub initialized successfully!'));
    console.log(chalk.blue('\nCreated:'));
    console.log(chalk.gray(`  - ${configPath}`));
    console.log(chalk.gray(`  - ${path.join(process.cwd(), 'data/')}`));
    console.log(chalk.blue('\nNext steps:'));
    console.log(chalk.gray('  1. Edit config/memory-hub.json to customize settings'));
    console.log(chalk.gray('  2. Run "memory-hub start" to start the server'));
  } catch (error) {
    spinner.fail(chalk.red('Initialization failed'));
    console.error(chalk.red(error.message));
    process.exit(1);
  }
}

export default init;

if (import.meta.url === `file://${process.argv[1]}`) {
  init();
}
