CREATE TABLE events (
  id SERIAL PRIMARY KEY,
  event_type TEXT,
  message TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
