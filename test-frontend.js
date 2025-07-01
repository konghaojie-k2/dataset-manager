const { chromium } = require('playwright');

async function testReloadIssue() {
  console.log('🔍 测试重新加载问题...');

  const browser = await chromium.launch({ headless: true }); // 无头模式运行
  const context = await browser.newContext();
  const page = await context.newPage();

  let errorCount = 0;
  let apiErrors = [];
  let consoleErrors = [];

  // 监听控制台错误
  page.on('console', msg => {
    if (msg.type() === 'error') {
      const errorText = msg.text();
      console.log('❌ 控制台错误:', errorText);
      consoleErrors.push(errorText);
      errorCount++;
    }
  });

  // 监听页面错误
  page.on('pageerror', error => {
    console.log('❌ 页面错误:', error.message);
    consoleErrors.push(error.message);
    errorCount++;
  });

  // 监听网络请求失败
  page.on('requestfailed', request => {
    const errorText = `请求失败: ${request.url()} - ${request.failure().errorText}`;
    console.log('❌', errorText);
    apiErrors.push(errorText);
    errorCount++;
  });

  // 监听网络响应
  page.on('response', response => {
    if (response.status() >= 400) {
      const errorText = `HTTP错误: ${response.status()} - ${response.url()}`;
      console.log('❌', errorText);
      apiErrors.push(errorText);
      errorCount++;
    } else if (response.url().includes('/api/')) {
      console.log(`✅ API请求成功: ${response.status()} - ${response.url()}`);
    }
  });

  try {
    // 第一次加载
    console.log('\n📍 第一次加载页面...');
    await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    const firstLoadErrors = errorCount;
    console.log(`第一次加载错误数量: ${firstLoadErrors}`);

    // 截图第一次加载
    await page.screenshot({ path: 'first-load.png', fullPage: true });

    // 重新加载页面
    console.log('\n📍 重新加载页面...');
    errorCount = 0; // 重置错误计数
    apiErrors = [];
    consoleErrors = [];

    await page.reload({ waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    const reloadErrors = errorCount;
    console.log(`重新加载错误数量: ${reloadErrors}`);

    // 截图重新加载
    await page.screenshot({ path: 'reload-test.png', fullPage: true });

    // 再次重新加载测试
    console.log('\n📍 第二次重新加载页面...');
    errorCount = 0;
    apiErrors = [];
    consoleErrors = [];

    await page.reload({ waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    const secondReloadErrors = errorCount;
    console.log(`第二次重新加载错误数量: ${secondReloadErrors}`);

    // 截图第二次重新加载
    await page.screenshot({ path: 'second-reload-test.png', fullPage: true });

    // 总结
    console.log('\n📊 测试总结:');
    console.log(`第一次加载错误: ${firstLoadErrors}`);
    console.log(`第一次重新加载错误: ${reloadErrors}`);
    console.log(`第二次重新加载错误: ${secondReloadErrors}`);

    if (reloadErrors > firstLoadErrors || secondReloadErrors > firstLoadErrors) {
      console.log('🔴 确认问题：重新加载时出现更多错误');
      console.log('API错误:', apiErrors);
      console.log('控制台错误:', consoleErrors);
    } else {
      console.log('🟢 未发现重新加载问题');
    }

  } catch (error) {
    console.log('❌ 测试失败:', error.message);
  } finally {
    // 等待一下确保所有请求完成
    await page.waitForTimeout(2000);
    await browser.close();
  }
}

testReloadIssue();
