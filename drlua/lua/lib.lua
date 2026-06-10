-- DrLua Library Start

function CreateBins(payload)
    if type(payload) ~= "table" then
        error("CreateBins expected a payload table")
    end

    local create_timelines = payload.create_timelines == true
    local scene_rules_sep = tostring(payload.scene_rules_sep or "")
    local parent_bin_name = tostring(payload.parent_bin_name or "")
    local release_name = tostring(payload.release_name or "")
    local bins = payload.bins or {}

    local resolve = Resolve()
    local project = resolve:GetProjectManager():GetCurrentProject()
    local media_pool = project:GetMediaPool()
    local root_folder = media_pool:GetRootFolder()
    resolve:OpenPage("media")

    print("[CreateBins] Resolver version: 2026-06-09-b")

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

    local function clip_totals(bins)
        local TotalClips = 0
        local TotalFrames = 0

        for _, bin in ipairs(bins) do
            TotalFrames = TotalFrames + (tonumber(bin.total_frames) or 0)
            TotalClips = TotalClips + #bin.clips
        end

        return TotalClips, TotalFrames
    end

    TotalClips, TotalFrames = clip_totals(bins)
    local seen_kinds = {}

    print("[CreateBins] Created parent bin: " .. parent_name .. " total_clips: " .. TotalClips .. "(" .. TotalFrames .. ")")

    for i, bin in ipairs(bins) do
        if #bin.clips > 0 then
            local kind = tostring(bin.kind or "Bin")
            local bin_name = parent_bin_name .. "_" .. kind .. "_" .. bin.layer_suffix
            print("[CreateBins] working" .. bin_name .. " (kind=" .. kind .. ")")

            if not seen_kinds[kind] then
                seen_kinds[kind] = true
                seen_kinds[#seen_kinds + 1] = kind
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
            print("[CreateBins] Importing " .. tostring(#bin.clips) .. " media to " .. child_name)
            local ordered_imported = {}
            for _, clip in ipairs(bin.clips) do
                local imported = media_pool:ImportMedia({clip.path})
                local item = nil
                if imported ~= nil and imported[1] ~= nil then
                    item = imported[1]
                end
                ordered_imported[#ordered_imported + 1] = item
            end

            print("[CreateBins] " .. child_name .. ": imported " .. tostring(#ordered_imported) .. " clips, " .. tostring(bin.totalFrames) .. " total frames")

            if create_timelines then
                media_pool:SetCurrentFolder(parent_folder)
                local timeline = nil
                if #ordered_imported > 0 then
                    timeline = media_pool:CreateTimelineFromClips(child_name, ordered_imported)
                    print("[CreateBins] Created timeline " .. i .. ". " .. bin.kind .. "_" .. bin.layer_suffix)
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
        for _, kind in ipairs(seen_kinds) do
            media_pool:SetCurrentFolder(parent_folder)
            local aggregate_name = release_name .. scene_rules_sep .. kind
            local aggregate = media_pool:CreateEmptyTimeline(aggregate_name)
            if aggregate == nil then
                error("Could not create aggregate timeline " .. aggregate_name)
            end
            print("[CreateBins] Created aggregate timeline: " .. aggregate_name)
        end
    end

    media_pool:SetCurrentFolder(parent_folder)
end

-- DrLua Library End

