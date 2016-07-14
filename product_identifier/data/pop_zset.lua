local zset_to_process_key = KEYS[1]
local result = redis.call("ZRANGE", zset_to_process_key,  0, 0)
local queue_top = nil
for i, v in ipairs(result) do
    queue_top = v
    redis.call("ZREM", zset_to_process_key, v)
end
return queue_top
