local function normalize_path(path)
    return tostring(path or ""):gsub("\\", "/")
end

local function to_done_path(path)
    local normalized = normalize_path(path)
    return normalized:gsub("/processed/create_bins/", "/processed/done/create_bins/", 1)
end

local function read_file(path)
    local handle = io.open(path, "rb")
    if not handle then
        return nil
    end
    local text = handle:read("*a")
    handle:close()
    return text
end

local function decode_payload_json_from_lua(lua_path)
    local script_text = read_file(lua_path)
    if not script_text then
        return nil, "unable to read file"
    end

    local quoted = script_text:match("local%s+payload_json%s*=%s*(\".*\")")
    if not quoted then
        return nil, "payload_json assignment not found"
    end

    local chunk, chunk_err = load("return " .. quoted)
    if not chunk then
        return nil, "failed to parse payload_json string: " .. tostring(chunk_err)
    end

    local ok, payload_json = pcall(chunk)
    if not ok or type(payload_json) ~= "string" then
        return nil, "failed to evaluate payload_json string"
    end

    local candidates = {}
    if type(json) == "table" and type(json.decode) == "function" then
        candidates[#candidates + 1] = json
    end
    for _, module_name in ipairs({"json", "dkjson", "cjson", "cjson.safe"}) do
        local module_ok, module = pcall(require, module_name)
        if module_ok and type(module) == "table" and type(module.decode) == "function" then
            candidates[#candidates + 1] = module
        end
    end

    for _, module in ipairs(candidates) do
        local decoded_ok, decoded = pcall(module.decode, payload_json)
        if decoded_ok and type(decoded) == "table" then
            return decoded
        end
    end

    return nil, "no usable JSON decoder"
end

local function index_subfolders(folder)
    local names = {}
    for _, subfolder in ipairs(folder:GetSubFolderList() or {}) do
        names[subfolder:GetName()] = subfolder
    end
    return names
end

local function index_clip_names(folder)
    local names = {}
    for _, clip in ipairs(folder:GetClipList() or {}) do
        local clip_name = clip:GetClipProperty("Clip Name")
        if type(clip_name) == "string" and clip_name ~= "" then
            names[clip_name] = true
        end
    end
    return names
end

local function validate_payload_applied(payload, root_folder)
    local parent_name = tostring(payload.parent_bin_name or "")
    if parent_name == "" then
        return false, "missing parent_bin_name"
    end

    local root_subfolders = index_subfolders(root_folder)
    local parent_folder = root_subfolders[parent_name]
    if not parent_folder then
        return false, "parent folder not found"
    end

    local expected_bins = {}
    for _, entry in ipairs(payload.bins or {}) do
        local bin_name = tostring(entry.name or "")
        if bin_name ~= "" then
            expected_bins[bin_name] = true
        end
    end

    local child_subfolders = index_subfolders(parent_folder)
    for bin_name, _ in pairs(expected_bins) do
        if not child_subfolders[bin_name] then
            return false, "missing bin folder: " .. bin_name
        end
    end

    if payload.create_timelines == true then
        local clip_names = index_clip_names(parent_folder)
        for bin_name, _ in pairs(expected_bins) do
            if not clip_names[bin_name] then
                return false, "missing timeline media: " .. bin_name
            end
        end

        local sep = tostring(payload.scene_rules_sep or ".")
        local release_name = tostring(payload.release_name or "")
        for _, kind in ipairs(payload.include_kinds or {}) do
            local aggregate = release_name .. sep .. tostring(kind)
            if not clip_names[aggregate] then
                return false, "missing aggregate timeline media: " .. aggregate
            end
        end
    end

    return true, "ok"
end

local function run_clean_create_bins_done()
    local resolve = Resolve()
    local project = resolve:GetProjectManager():GetCurrentProject()
    local media_pool = project:GetMediaPool()
    local root_folder = media_pool:GetRootFolder()

    local moved = 0
    local skipped = 0

    for _, lua_file in ipairs(CREATE_BINS_LUA_FILES or {}) do
        local payload, payload_err = decode_payload_json_from_lua(lua_file)
        if not payload then
            skipped = skipped + 1
            print("[CleanCreateBinsDone] Skip " .. tostring(lua_file) .. " :: " .. tostring(payload_err))
        else
            local ok, reason = validate_payload_applied(payload, root_folder)
            if not ok then
                skipped = skipped + 1
                print("[CleanCreateBinsDone] Keep " .. tostring(lua_file) .. " :: " .. tostring(reason))
            else
                local destination = to_done_path(lua_file)
                local renamed, rename_err = os.rename(lua_file, destination)
                if renamed then
                    moved = moved + 1
                    print("[CleanCreateBinsDone] Moved " .. tostring(lua_file) .. " -> " .. tostring(destination))
                else
                    skipped = skipped + 1
                    print("[CleanCreateBinsDone] Keep " .. tostring(lua_file) .. " :: move failed: " .. tostring(rename_err))
                end
            end
        end
    end

    print("[CleanCreateBinsDone] Done. moved=" .. tostring(moved) .. " skipped=" .. tostring(skipped))
end

run_clean_create_bins_done()
