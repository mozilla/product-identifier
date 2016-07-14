redis.replicate_commands();

local domain = KEYS[1]
local cooloff_key = domain .. "_cooloff"
local cur_time = tonumber((redis.call('time'))[1]);
local prev_time = tonumber(redis.call('get', cooloff_key));

if prev_time ~= nil then
  local elapsed = cur_time - prev_time
  if elapsed > 2 then
    redis.call('set', cooloff_key, cur_time);
    return redis.call('lpop', domain);
  else
      return nil;
  end
end

redis.call('set', cooloff_key, cur_time);
return redis.call('lpop', domain);
