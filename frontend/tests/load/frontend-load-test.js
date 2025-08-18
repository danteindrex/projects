import { browser } from 'k6/experimental/browser';
import { check } from 'k6';

export const options = {
  scenarios: {
    browser: {
      executor: 'constant-vus',
      exec: 'browserTest',
      vus: 3,
      duration: '1m',
      options: {
        browser: {
          type: 'chromium',
        },
      },
    },
  },
  thresholds: {
    browser_web_vital_fcp: ['p(95)<3000'], // First Contentful Paint
    browser_web_vital_lcp: ['p(95)<5000'], // Largest Contentful Paint
  },
};

export async function browserTest() {
  const page = browser.newPage();
  
  try {
    // Navigate to homepage
    await page.goto('http://localhost:3000');
    
    // Wait for page load
    await page.waitForSelector('h1', { timeout: 10000 });
    
    // Check page title
    const title = await page.title();
    check(title, {
      'page title is correct': (t) => t.includes('Business Systems Integration'),
    });
    
    // Test navigation to dashboard
    const dashboardLink = page.locator('a[href="/dashboard"]');
    if (await dashboardLink.count() > 0) {
      await dashboardLink.click();
      await page.waitForSelector('.dashboard', { timeout: 5000 });
      
      check(page, {
        'dashboard loads': async (p) => await p.locator('.dashboard').count() > 0,
      });
    }
    
    // Test chat interface if available
    const chatButton = page.locator('button:has-text("Chat")');
    if (await chatButton.count() > 0) {
      await chatButton.click();
      await page.waitForSelector('.chat-interface', { timeout: 5000 });
      
      // Type message and send
      const messageInput = page.locator('input[placeholder*="Ask me"]');
      if (await messageInput.count() > 0) {
        await messageInput.fill('Load test message');
        await page.keyboard.press('Enter');
        
        // Wait for response
        await page.waitForTimeout(2000);
        
        check(page, {
          'chat message sent': async (p) => await p.locator('.message').count() > 1,
        });
      }
    }
    
    // Measure performance
    const performanceMetrics = await page.evaluate(() => {
      const navigation = performance.getEntriesByType('navigation')[0];
      return {
        loadTime: navigation.loadEventEnd - navigation.loadEventStart,
        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
        timeToFirstByte: navigation.responseStart - navigation.requestStart,
      };
    });
    
    check(performanceMetrics, {
      'page load time < 3s': (m) => m.loadTime < 3000,
      'DOM content loaded < 2s': (m) => m.domContentLoaded < 2000,
      'TTFB < 1s': (m) => m.timeToFirstByte < 1000,
    });
    
  } catch (error) {
    console.error('Browser test error:', error);
    check(error, {
      'no browser errors': (e) => e === null,
    });
  } finally {
    page.close();
  }
}