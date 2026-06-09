local function decode_payload(value)
    if type(value) == "table" then
        return value
    end
    if type(value) ~= "string" then
        error("CreateBins expected a config table or JSON string")
    end

    local candidates = {}
    if type(json) == "table" and type(json.decode) == "function" then
        candidates[#candidates + 1] = json
    end
    for _, module_name in ipairs({"json", "dkjson", "cjson", "cjson.safe"}) do
        local ok, module = pcall(require, module_name)
        if ok and type(module) == "table" and type(module.decode) == "function" then
            candidates[#candidates + 1] = module
        end
    end

    for _, module in ipairs(candidates) do
        local ok, decoded, extra = pcall(module.decode, value)
        if ok and type(decoded) == "table" then
            if extra == nil or extra == 1 or extra == value:len() then
                return decoded
            end
            return decoded
        end
    end

    error("CreateBins could not find a JSON decoder in the Resolve Lua runtime")
end

local function create_bins(config)
    config = decode_payload(config)
    local create_timelines = config.create_timelines == true
    local scene_rules_sep = tostring(config.scene_rules_sep or "")
    local source_folder = tostring(config.source_folder or "")
    local parent_bin_name = tostring(config.parent_bin_name or "")
    local release_name = tostring(config.release_name or "")
    local include_kinds = config.include_kinds or {"Vertical", "Full"}
    local bins = config.bins or {}
    local allowed_kinds = {}
    for _, kind in ipairs(include_kinds) do
        allowed_kinds[tostring(kind)] = true
    end

    local resolve = Resolve()
    local project = resolve:GetProjectManager():GetCurrentProject()
    local media_pool = project:GetMediaPool()
    local root_folder = media_pool:GetRootFolder()
    resolve:OpenPage("media")

    print("[CreateBins] Resolver version: 2026-06-07-b")

    local taken_parent = {}
    for _, child in ipairs(root_folder:GetSubFolderList()) do
        taken_parent[child:GetName()] = true
    end
    local parent_name = parent_bin_name
    local parent_suffix = 2
    while taken_parent[parent_name] do
        parent_name = parent_bin_name .. " (" .. tostring(parent_suffix) .. ")"
        parent_suffix = parent_suffix + 1
    end
    local parent_folder = media_pool:AddSubFolder(root_folder, parent_name)
    if parent_folder == nil then
        error("Could not create subfolder " .. parent_name)
    end

    print("[CreateBins] Source folder: " .. source_folder)
    print("[CreateBins] Created parent bin: " .. parent_name)

    for i, bin in ipairs(bins) do
        local bin_kind = tostring(bin.kind or "")
        if allowed_kinds[bin_kind] then
            local bin_name = bin.name
            if type(bin_name) ~= "string" or #bin_name == 0 then
                local kind = tostring(bin.kind or "Bin")
                local layer = bin.layer
                local suffix
                if type(layer) == "number" and layer >= 1 and layer <= 26 then
                    suffix = string.char(string.byte("A") + layer - 1)
                else
                    suffix = tostring(layer or "X")
                end
                if suffix == "X" then
                    suffix = tostring(i)
                end
                bin_name = parent_bin_name .. "_" .. kind .. "_" .. suffix
            end

            local taken = {}
            for _, child in ipairs(parent_folder:GetSubFolderList()) do
                taken[child:GetName()] = true
            end
            local child_name = bin_name
            local child_suffix = 2
            while taken[child_name] do
                child_name = bin_name .. " (" .. tostring(child_suffix) .. ")"
                child_suffix = child_suffix + 1
            end
            local child_folder = media_pool:AddSubFolder(parent_folder, child_name)
            if child_folder == nil then
                error("Could not create subfolder " .. child_name)
            end

            media_pool:SetCurrentFolder(child_folder)
            local ordered_imported = {}
            local unresolved_count = 0
            if #bin.clips > 0 then
                for _, clip in ipairs(bin.clips) do
                    local imported = media_pool:ImportMedia({clip.path})
                    local item = nil
                    if imported ~= nil and imported[1] ~= nil then
                        item = imported[1]
                    end
                    if item == nil then
                        unresolved_count = unresolved_count + 1
                        print("[CreateBins] Warning: import failed; skipping " .. clip.path)
                    else
                        ordered_imported[#ordered_imported + 1] = item
                    end
                end
                if unresolved_count > 0 then
                    print("[CreateBins] Warning: skipped " .. tostring(unresolved_count) .. " failed imports in " .. child_name)
                end
            end

            print("[CreateBins] " .. child_name .. ": imported " .. tostring(#ordered_imported) .. " clips, " .. tostring(bin.totalFrames) .. " total frames")

            if create_timelines then
                media_pool:SetCurrentFolder(parent_folder)
                local timeline = nil
                if #ordered_imported > 0 then
                    timeline = media_pool:CreateTimelineFromClips(child_name, ordered_imported)
                else
                    timeline = media_pool:CreateEmptyTimeline(child_name)
                end
                if timeline == nil then
                    error("Could not create timeline " .. child_name)
                end
                bin.timeline_media = nil
                local start_frame = timeline:GetStartFrame()
                local end_frame = timeline:GetEndFrame()
                if start_frame == nil or end_frame == nil then
                    error("Could not read timeline frame range for " .. child_name)
                end
                bin.timeline_frames = end_frame - start_frame
                for _, item in ipairs(parent_folder:GetClipList()) do
                    local item_name = item:GetClipProperty("Clip Name")
                    if item_name == child_name then
                        bin.timeline_media = item
                        break
                    end
                end
                if bin.timeline_media == nil then
                    error("Could not resolve timeline media pool item for " .. child_name)
                end
                print("[CreateBins] Created timeline: " .. child_name)
            end
        end
    end

    if create_timelines then
        local aggregate_names = {
            Vertical = release_name .. scene_rules_sep .. "Vertical",
            Full = release_name .. scene_rules_sep .. "Full",
        }
        for _, kind in ipairs({"Vertical", "Full"}) do
            if allowed_kinds[kind] then
                media_pool:SetCurrentFolder(parent_folder)
                local aggregate = media_pool:CreateEmptyTimeline(aggregate_names[kind])
                if aggregate == nil then
                    error("Could not create aggregate timeline " .. aggregate_names[kind])
                end
                print("[CreateBins] Created aggregate timeline: " .. aggregate_names[kind])
            end
        end
    end

    media_pool:SetCurrentFolder(parent_folder)
end

return create_bins
