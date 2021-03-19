module.paths.push('/home/ubuntu/node_modules');
const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
    executablePath: '/usr/bin/chromium-browser'
  });
  const page = await browser.newPage();
  const html_path = process.argv[2];
  const image_path = process.argv[3];
  const selector = '#vid_area';
  await page.goto(html_path);
  await page.waitForSelector(selector);
  const element = await page.$(selector);
  await element.screenshot({path: image_path});

  await browser.close();
})();
