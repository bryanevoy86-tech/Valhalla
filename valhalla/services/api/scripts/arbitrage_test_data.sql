-- Arbitrage Phase A: Test Market Feed Events
-- Insert test data to verify arbitrage scanning logic

-- Test case 1: Good spread (SKU123)
-- Buy at $100, sell at $155 = $55 gross spread
INSERT INTO market_feed_events (source, sku, title, venue, price, currency, url, observed_at)
VALUES 
  ('ebay_buy', 'BESTSELLER_001', 'Popular Item', 'BUY', 100.00, 'CAD', 'https://ebay.com/itm/item1', NOW()),
  ('marketplace_sell', 'BESTSELLER_001', 'Popular Item', 'SELL', 155.00, 'CAD', 'https://shop.example/bestseller1', NOW());

-- Test case 2: Marginal spread (SKU999)
-- Buy at $120, sell at $130 = $10 gross spread (too small)
INSERT INTO market_feed_events (source, sku, title, venue, price, currency, url, observed_at)
VALUES
  ('facebook_buy', 'SKU999', 'Marginal Item', 'BUY', 120.00, 'CAD', 'https://facebook.com/marketplace/item', NOW()),
  ('kijiji_sell', 'SKU999', 'Marginal Item', 'SELL', 130.00, 'CAD', 'https://kijiji.ca/item', NOW());

-- Test case 3: Excellent spread (ELECTRONICS_042)
-- Buy at $80, sell at $220 = $140 gross spread
INSERT INTO market_feed_events (source, sku, title, venue, price, currency, url, observed_at)
VALUES
  ('aliexpress', 'ELECTRONICS_042', 'Tech Gadget', 'BUY', 80.00, 'CAD', 'https://aliexpress.com/item', NOW()),
  ('amazon_ca', 'ELECTRONICS_042', 'Tech Gadget', 'SELL', 220.00, 'CAD', 'https://amazon.ca/dp/B123456', NOW());

SELECT COUNT(*) as feed_events_created FROM market_feed_events;
