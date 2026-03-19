#!/usr/bin/env node

import chalk from 'chalk';
import { execSync } from 'child_process';

console.log(chalk.blue('\n========================================'));
console.log(chalk.blue('  Memory Hub - Post Installation Setup'));
console.log(chalk.blue('========================================\n'));

// Check if Docker is installed
function checkDocker() {
  try {
    execSync('docker --version', { stdio: 'ignore' });
    console.log(chalk.green('✓ Docker is installed'));
    return true;
  } catch (error) {
    console.log(chalk.yellow('⚠ Docker is not installed'));
    return false;
  }
}

// Check if Docker daemon is running
function checkDockerDaemon() {
  try {
    execSync('docker info', { stdio: 'ignore' });
    console.log(chalk.green('✓ Docker daemon is running'));
    return true;
  } catch (error) {
    console.log(chalk.red('✗ Docker daemon is not running'));
    return false;
  }
}

console.log(chalk.white('Checking system requirements...\n'));

const hasDocker = checkDocker();
const isDockerRunning = hasDocker ? checkDockerDaemon() : false;

console.log('\n' + chalk.blue('========================================'));
console.log(chalk.blue('  Next Steps'));
console.log(chalk.blue('========================================\n'));

if (!hasDocker) {
  console.log(chalk.yellow('1. Install Docker:'));
  console.log(chalk.gray('   Visit: https://docs.docker.com/get-docker/\n'));
} else if (!isDockerRunning) {
  console.log(chalk.yellow('1. Start Docker Desktop or Docker daemon\n'));
} else {
  console.log(chalk.green('1. Docker is ready!\n'));
}

console.log(chalk.yellow('2. Initialize Memory Hub:'));
console.log(chalk.gray('   memory-hub init\n'));

console.log(chalk.yellow('3. Start the server:'));
console.log(chalk.gray('   memory-hub start\n'));

console.log(chalk.yellow('4. Configure your agents:'));
console.log(chalk.gray('   Edit config/memory-hub.json\n'));

console.log(chalk.white('For more information, run:'));
console.log(chalk.gray('   memory-hub --help\n'));

console.log(chalk.green('Installation complete! 🎉\n'));
