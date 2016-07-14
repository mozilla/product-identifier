redis.replicate_commands()
local zset_to_process_key = "zset-to-process"
local set_processed_key = "set-processed"
local count_added = 0

for i, v in pairs(ARGV) do
    local in_to_process = type(redis.call("ZRANK", zset_to_process_key, v)) ~= "boolean"
    local seen_before = redis.call("SISMEMBER", set_processed_key, v)
    if (seen_before == 0 and not in_to_process) then
        local seconds = tonumber(redis.call("TIME")[1])
        redis.call("ZADD", zset_to_process_key, seconds, v)
        count_added = count_added + 1
    end
end

return count_added
