#!/usr/bin/env node

import { Command } from 'commander';
import chalk from 'chalk';
import ora from 'ora';
import path from 'path';
import fs from 'fs';
import { execSync, spawn } from 'child_process';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const program = new Command();

// 项目根目录
const PROJECT_ROOT = path.resolve(__dirname, '..');
const DOCKER_COMPOSE_FILE = path.join(PROJECT_ROOT, 'docker-compose.yml');
const ENV_EXAMPLE = path.join(PROJECT_ROOT, '.env.example');
const ENV_FILE = path.join(PROJECT_ROOT, '.env');

// 辅助函数：执行 shell 命令
function execCommand(cmd, options = {}) {
  try {
    return execSync(cmd, {
      cwd: PROJECT_ROOT,
      stdio: options.stdio || 'pipe',
      encoding: 'utf-8'
    });
  } catch (error) {
    throw new Error(`命令执行失败：${cmd}\n${error.message}`);
  }
}

// 辅助函数：检查 Docker 是否安装
function checkDockerInstalled() {
  try {
    execSync('docker --version', { stdio: 'ignore' });
    return true;
  } catch {
    return false;
  }
}

// 辅助函数：检查 docker-compose 是否安装
function checkDockerComposeInstalled() {
  try {
    execSync('docker-compose --version', { stdio: 'ignore' });
    return true;
  } catch {
    try {
      execSync('docker compose version', { stdio: 'ignore' });
      return true;
    } catch {
      return false;
    }
  }
}

// 辅助函数：获取 docker-compose 命令
function getDockerComposeCmd() {
  try {
    execSync('docker-compose --version', { stdio: 'ignore' });
    return 'docker-compose';
  } catch {
    return 'docker compose';
  }
}

// 辅助函数：等待服务健康检查
async function waitForHealth(url, timeout = 60000) {
  const spinner = ora('等待服务启动...').start();
  const startTime = Date.now();
  
  while (Date.now() - startTime < timeout) {
    try {
      const response = await fetch(url, { method: 'HEAD' });
      if (response.ok) {
        spinner.succeed(chalk.green('服务已就绪！'));
        return true;
      }
    } catch {
      // 服务还未就绪
    }
    await new Promise(resolve => setTimeout(resolve, 2000));
  }
  
  spinner.fail(chalk.red('服务启动超时'));
  return false;
}

// 辅助函数：检查端口是否被占用
function checkPort(port) {
  try {
    execSync(`lsof -i :${port}`, { stdio: 'ignore' });
    return true;
  } catch {
    return false;
  }
}

// 辅助函数：获取容器状态
function getContainerStatus(containerName) {
  try {
    const result = execSync(`docker ps -f name=${containerName} --format "{{.Status}}"`, {
      encoding: 'utf-8'
    }).trim();
    return result || '未运行';
  } catch {
    return '未找到';
  }
}

program
  .name('memory-hub')
  .description('Memory Hub - 多智能体记忆中枢 CLI 工具')
  .version('1.0.0');

// ============================================================
// init 命令
// ============================================================
program
  .command('init')
  .description('初始化 Memory Hub 配置')
  .option('-f, --force', '强制覆盖现有配置')
  .option('--skip-docker-check', '跳过 Docker 检查')
  .helpOption('-h, --help', '查看此命令的帮助信息')
  .action(async (options) => {
    console.log(chalk.blue('\n🚀 开始初始化 Memory Hub...\n'));
    
    // 检查 Docker
    if (!options.skipDockerCheck) {
      const spinner = ora('检查 Docker 环境').start();
      if (!checkDockerInstalled()) {
        spinner.fail(chalk.red('Docker 未安装'));
        console.log(chalk.yellow('\n请先安装 Docker：'));
        console.log(chalk.gray('  Ubuntu/Debian: curl -fsSL https://get.docker.com | sh'));
        console.log(chalk.gray('  macOS: 下载 Docker Desktop https://www.docker.com/products/docker-desktop'));
        process.exit(1);
      }
      if (!checkDockerComposeInstalled()) {
        spinner.fail(chalk.red('docker-compose 未安装'));
        console.log(chalk.yellow('\n请安装 docker-compose'));
        process.exit(1);
      }
      spinner.succeed(chalk.green('Docker 环境检查通过'));
    }
    
    // 复制 .env.example 到 .env
    const envSpinner = ora('创建配置文件').start();
    if (fs.existsSync(ENV_FILE) && !options.force) {
      envSpinner.fail(chalk.red('.env 文件已存在'));
      console.log(chalk.yellow('使用 --force 选项强制覆盖'));
      process.exit(1);
    }
    
    try {
      fs.copyFileSync(ENV_EXAMPLE, ENV_FILE);
      envSpinner.succeed(chalk.green('配置文件已创建'));
      console.log(chalk.blue(`  → ${ENV_FILE}`));
    } catch (error) {
      envSpinner.fail(chalk.red('配置文件创建失败'));
      console.log(chalk.red(error.message));
      process.exit(1);
    }
    
    // 拉取 Docker 镜像
    const pullSpinner = ora('拉取 Docker 镜像').start();
    try {
      console.log(chalk.gray('  → 拉取 PostgreSQL 镜像...'));
      execSync('docker pull pgvector/pgvector:pg16', { stdio: 'inherit' });
      console.log(chalk.gray('  → 拉取 pgAdmin 镜像...'));
      execSync('docker pull dpage/pgadmin4:latest', { stdio: 'inherit' });
      pullSpinner.succeed(chalk.green('Docker 镜像拉取完成'));
    } catch (error) {
      pullSpinner.fail(chalk.red('Docker 镜像拉取失败'));
      console.log(chalk.red(error.message));
      process.exit(1);
    }
    
    // 生成配置文件
    const configSpinner = ora('生成配置文件').start();
    try {
      const configDir = path.join(PROJECT_ROOT, 'config');
      if (!fs.existsSync(configDir)) {
        fs.mkdirSync(configDir, { recursive: true });
      }
      
      const configPath = path.join(configDir, 'memory-hub.json');
      const config = {
        version: '1.0.0',
        initialized: true,
        initializedAt: new Date().toISOString(),
        dockerComposeFile: DOCKER_COMPOSE_FILE,
        services: ['postgres', 'api', 'pgadmin']
      };
      
      fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
      configSpinner.succeed(chalk.green('配置文件生成完成'));
      console.log(chalk.blue(`  → ${configPath}`));
    } catch (error) {
      configSpinner.fail(chalk.red('配置文件生成失败'));
      console.log(chalk.red(error.message));
      process.exit(1);
    }
    
    console.log(chalk.green('\n✅ Memory Hub 初始化完成！\n'));
    console.log(chalk.blue('下一步：'));
    console.log(chalk.gray('  memory-hub start  # 启动服务\n'));
  });

// ============================================================
// start 命令
// ============================================================
program
  .command('start')
  .description('启动 Memory Hub 服务')
  .option('-d, --detach', '后台运行', true)
  .option('--no-health-check', '跳过健康检查')
  .helpOption('-h, --help', '查看此命令的帮助信息')
  .action(async (options) => {
    console.log(chalk.blue('\n🚀 启动 Memory Hub 服务...\n'));
    
    // 检查配置文件
    if (!fs.existsSync(ENV_FILE)) {
      console.log(chalk.yellow('配置文件不存在，请先运行：memory-hub init'));
      process.exit(1);
    }
    
    const composeCmd = getDockerComposeCmd();
    
    // 启动服务
    const spinner = ora('启动 Docker 容器...').start();
    try {
      execSync(`${composeCmd} up -d`, {
        cwd: PROJECT_ROOT,
        stdio: 'inherit'
      });
      spinner.succeed(chalk.green('Docker 容器已启动'));
    } catch (error) {
      spinner.fail(chalk.red('启动失败'));
      console.log(chalk.red(error.message));
      process.exit(1);
    }
    
    // 健康检查
    if (options.healthCheck) {
      const apiHealthy = await waitForHealth('http://localhost:8000/api/v1/health');
      const pgAdminHealthy = await waitForHealth('http://localhost:5050');
      
      if (!apiHealthy || !pgAdminHealthy) {
        console.log(chalk.yellow('\n服务可能还未完全就绪，请稍后检查状态'));
      }
    } else {
      await new Promise(resolve => setTimeout(resolve, 3000));
    }
    
    // 显示访问地址
    console.log(chalk.green('\n✅ Memory Hub 服务已启动！\n'));
    console.log(chalk.blue('访问地址：'));
    console.log(chalk.gray('  API:       http://localhost:8000'));
    console.log(chalk.gray('  API Docs:  http://localhost:8000/docs'));
    console.log(chalk.gray('  pgAdmin:   http://localhost:5050'));
    console.log(chalk.gray('\n登录 pgAdmin:'));
    console.log(chalk.gray('  邮箱：admin@memory.hub'));
    console.log(chalk.gray('  密码：admin123\n'));
  });

// ============================================================
// stop 命令
// ============================================================
program
  .command('stop')
  .description('停止 Memory Hub 服务')
  .option('-v, --volumes', '同时删除数据卷')
  .option('--remove-orphans', '删除孤立容器')
  .helpOption('-h, --help', '查看此命令的帮助信息')
  .action((options) => {
    console.log(chalk.blue('\n🛑 停止 Memory Hub 服务...\n'));
    
    const composeCmd = getDockerComposeCmd();
    let cmd = `${composeCmd} down`;
    
    if (options.volumes) {
      cmd += ' --volumes';
      console.log(chalk.yellow('⚠️  将删除所有数据卷！'));
    }
    
    if (options.removeOrphans) {
      cmd += ' --remove-orphans';
    }
    
    const spinner = ora('停止 Docker 容器...').start();
    try {
      execSync(cmd, {
        cwd: PROJECT_ROOT,
        stdio: 'inherit'
      });
      spinner.succeed(chalk.green('服务已停止'));
    } catch (error) {
      spinner.fail(chalk.red('停止失败'));
      console.log(chalk.red(error.message));
      process.exit(1);
    }
    
    console.log(chalk.green('\n✅ Memory Hub 服务已停止！\n'));
  });

// ============================================================
// status 命令
// ============================================================
program
  .command('status')
  .description('查看 Memory Hub 服务状态')
  .option('--json', '以 JSON 格式输出')
  .helpOption('-h, --help', '查看此命令的帮助信息')
  .action((options) => {
    const composeCmd = getDockerComposeCmd();
    
    // 获取容器状态
    const containers = [
      { name: 'memory-hub-db', service: 'PostgreSQL', port: 5433 },
      { name: 'memory-hub-api', service: 'API', port: 8000 },
      { name: 'memory-hub-admin', service: 'pgAdmin', port: 5050 }
    ];
    
    const status = {
      timestamp: new Date().toISOString(),
      containers: []
    };
    
    console.log(chalk.blue('\n📊 Memory Hub 服务状态\n'));
    
    containers.forEach(container => {
      const running = getContainerStatus(container.name);
      const portInUse = checkPort(container.port);
      
      status.containers.push({
        name: container.name,
        service: container.service,
        status: running,
        port: container.port,
        portInUse
      });
      
      const statusIcon = running !== '未找到' && running !== '未运行' 
        ? chalk.green('●') 
        : chalk.red('○');
      
      console.log(`${statusIcon} ${chalk.bold(container.service)} (${container.name})`);
      console.log(chalk.gray(`  状态：${running}`));
      console.log(chalk.gray(`  端口：:${container.port} ${portInUse ? chalk.green('已占用') : chalk.red('未占用')}`));
      console.log();
    });
    
    // 健康检查
    const healthSpinner = ora('执行健康检查...').start();
    setTimeout(() => {
      healthSpinner.succeed(chalk.green('健康检查完成'));
      
      // API 健康检查
      fetch('http://localhost:8000/api/v1/health', { method: 'HEAD' })
        .then(res => {
          if (res.ok) {
            console.log(chalk.green('\n✓ API 服务正常'));
          } else {
            console.log(chalk.yellow('\n⚠ API 服务响应异常'));
          }
        })
        .catch(() => {
          console.log(chalk.red('\n✗ API 服务无法访问'));
        });
      
      if (options.json) {
        console.log('\n' + JSON.stringify(status, null, 2));
      }
    }, 1000);
  });

// ============================================================
// logs 命令
// ============================================================
program
  .command('logs')
  .description('查看 Memory Hub 服务日志')
  .option('-n, --tail <number>', '显示最近 N 行日志', '100')
  .option('-f, --follow', '持续跟踪日志输出')
  .option('-s, --service <service>', '指定服务 (postgres|api|pgadmin)')
  .helpOption('-h, --help', '查看此命令的帮助信息')
  .action((options) => {
    const composeCmd = getDockerComposeCmd();
    let cmd = `${composeCmd} logs --tail ${options.tail}`;
    
    if (options.service) {
      cmd += ` ${options.service}`;
    }
    
    if (options.follow) {
      cmd += ' -f';
      console.log(chalk.blue(`\n📜 跟踪日志输出 (Ctrl+C 退出)\n`));
      
      // 使用 spawn 实现实时日志跟踪
      const logProcess = spawn(composeCmd, ['logs', '--tail', options.tail, ...(options.follow ? ['-f'] : []), ...(options.service ? [options.service] : [])], {
        cwd: PROJECT_ROOT,
        stdio: 'inherit'
      });
      
      logProcess.on('error', (error) => {
        console.log(chalk.red(`日志命令执行失败：${error.message}`));
        process.exit(1);
      });
      
      logProcess.on('close', (code) => {
        if (code !== 0) {
          console.log(chalk.yellow(`日志进程退出，代码：${code}`));
        }
      });
    } else {
      console.log(chalk.blue(`\n📜 最近 ${options.tail} 行日志\n`));
      try {
        const output = execSync(cmd, {
          cwd: PROJECT_ROOT,
          encoding: 'utf-8'
        });
        console.log(chalk.gray(output));
      } catch (error) {
        console.log(chalk.red(`获取日志失败：${error.message}`));
        process.exit(1);
      }
    }
  });

program.parse();
