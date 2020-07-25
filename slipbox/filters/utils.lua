local function character_class(character)
  local code = string.byte(character)
  if 47 <= code and code < 58 then return 'd' end
  if 97 <= code and code < 123 then return 'a' end
end

local function is_valid_alias(alias)
  if alias == nil then return true end
  if type(alias) ~= "string" then return false end
  if alias == "" then return false end
  if character_class(alias:sub(1, 1)) ~= 'd' then return false end

  for i = 1, #alias do
    local class = character_class(alias:sub(i, i))
    if class ~= 'd' and class ~= 'a' then return false end
  end
  return true
end

return { is_valid_alias = is_valid_alias }
