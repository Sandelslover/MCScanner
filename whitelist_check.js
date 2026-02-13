const mineflayer = require('mineflayer');

const ip = process.argv[2];
const port = parseInt(process.argv[3]) || 25565;
const username = `Scanner_${Math.floor(Math.random() * 10000)}`;

const bot = mineflayer.createBot({
  host: ip,
  port: port,
  username: username,
  auth: 'offline', // Attempt cracked/offline join
  hideErrors: true,
  connectTimeout: 10000
});

bot.on('login', () => {
  // Wait a moment for the server to send initial messages
  setTimeout(() => {
    bot.chat('/plugins');
  }, 2000);
});

bot.on('message', (jsonMsg) => {
  const msg = jsonMsg.toString();
  if (msg.toLowerCase().includes('plugins (') || msg.toLowerCase().includes('plugins:')) {
    console.log(JSON.stringify({ 
      status: 'success', 
      message: 'Joined successfully',
      plugins: msg.replace(/Plugins \(\d+\): /i, '').replace(/Plugins: /i, '').trim()
    }));
    bot.quit();
    process.exit(0);
  }
});

// Fallback if no plugin message is received
setTimeout(() => {
    if (bot.entity) {
        console.log(JSON.stringify({ status: 'success', message: 'Joined successfully', plugins: 'Unknown/Hidden' }));
        bot.quit();
        process.exit(0);
    }
}, 10000);

bot.on('error', (err) => {
  // Common errors: ENOTFOUND, ECONNREFUSED
  process.exit(1);
});

bot.on('kicked', (reason) => {
    const reasonStr = typeof reason === 'string' ? reason : JSON.stringify(reason);
    const lowercaseReason = reasonStr.toLowerCase();
    
    if (lowercaseReason.includes('whitelist') || 
        lowercaseReason.includes('not whitelisted') ||
        lowercaseReason.includes('verify your username')) {
        console.log(JSON.stringify({ status: 'whitelisted', message: reasonStr }));
    } else {
        console.log(JSON.stringify({ status: 'kicked', message: reasonStr }));
    }
    process.exit(0);
});

// Timeout safeguard
setTimeout(() => {
  bot.quit();
  process.exit(1);
}, 15000);
