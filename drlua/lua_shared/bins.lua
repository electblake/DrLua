local function unique_subfolder(media_pool, parent_folder, base_name)
    local taken = {}
    for _, child in ipairs(parent_folder:GetSubFolderList()) do
        taken[child:GetName()] = true
    end
    local name = base_name
    local suffix = 2
    while taken[name] do
        name = base_name .. " (" .. tostring(suffix) .. ")"
        suffix = suffix + 1
    end
    local folder = media_pool:AddSubFolder(parent_folder, name)
    if folder == nil then
        error("Could not create subfolder " .. name)
    end
    return folder, name
end

local resolve = Resolve()
local project = resolve:GetProjectManager():GetCurrentProject()
local media_pool = project:GetMediaPool()
local root_folder = media_pool:GetRootFolder()
local original_timeline = project:GetCurrentTimeline()
resolve:OpenPage("media")

print("[CreateBins] Resolver version: 2026-06-07-b")

local parent_folder, parent_name = unique_subfolder(media_pool, root_folder, PARENT_BIN_NAME)
print("[CreateBins] Source folder: " .. SOURCE_FOLDER)
print("[CreateBins] Created parent bin: " .. parent_name)

local function layer_suffix(layer)
    if type(layer) == "number" and layer >= 1 and layer <= 26 then
        return string.char(string.byte("A") + layer - 1)
    end
    return tostring(layer or "X")
end

local function fallback_bin_name(bin, index)
    if type(bin.name) == "string" and #bin.name > 0 then
        return bin.name
    end
    local kind = tostring(bin.kind or "Bin")
    local suffix = layer_suffix(bin.layer)
    if suffix == "X" then
        suffix = tostring(index)
    end
    return PARENT_BIN_NAME .. "_" .. kind .. "_" .. suffix
end

for i, bin in ipairs(BINS) do
    local bin_name = fallback_bin_name(bin, i)
    local child_folder, child_name = unique_subfolder(media_pool, parent_folder, bin_name)
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
    -- @@PER_BIN_TIMELINES@@
end

-- @@AGGREGATE_TIMELINES@@
