import { createClient } from 'redis';

import { REDIS_URL } from './config.js';

let redisClientPromise;

function createRedisConnection() {
  const client = createClient({ url: REDIS_URL });
  client.on('error', (error) => {
    console.error('Redis client error:', error);
  });
  return client;
}

export async function getRedis() {
  if (!redisClientPromise) {
    const client = createRedisConnection();
    redisClientPromise = client.connect().then(() => client).catch((error) => {
      redisClientPromise = undefined;
      throw error;
    });
  }

  return redisClientPromise;
}

export async function createRedisDuplicate() {
  const redis = await getRedis();
  const duplicate = redis.duplicate();
  duplicate.on('error', (error) => {
    console.error('Redis duplicate client error:', error);
  });
  await duplicate.connect();
  return duplicate;
}

export async function withBlockingRedis(handler) {
  const client = await createRedisDuplicate();
  try {
    return await handler(client);
  } finally {
    await client.quit();
  }
}
