import { getRedis, withBlockingRedis } from './redis.js';

export async function publishCommand(command) {
  const redis = await getRedis();
  await redis.publish('wavox:commands', JSON.stringify(command));
}

export async function publishCommandAndWait(command, responseKey, timeoutSeconds) {
  const redis = await getRedis();
  await redis.publish('wavox:commands', JSON.stringify(command));

  return withBlockingRedis(async (blockingRedis) => {
    const result = await blockingRedis.blPop(responseKey, timeoutSeconds);
    if (!result) return null;

    const rawValue = Array.isArray(result) ? result[1] : result.element;
    if (!rawValue) return null;

    try {
      return JSON.parse(rawValue);
    } catch {
      return null;
    }
  });
}
