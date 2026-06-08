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

local function find_folder_recursive(folder, target_name)
    if folder:GetName() == target_name then
        return folder
    end
    for _, child in ipairs(folder:GetSubFolderList()) do
        local found = find_folder_recursive(child, target_name)
        if found ~= nil then
            return found
        end
    end
    return nil
end

local function parse_resolution(value)
    if value == nil then
        return 0, 0
    end
    local w, h = string.match(tostring(value), "(%d+)%s*x%s*(%d+)")
    if w == nil or h == nil then
        return 0, 0
    end
    return tonumber(w) or 0, tonumber(h) or 0
end

local function parse_frames(value)
    local n = tonumber(value)
    if n == nil then
        return 0
    end
    return math.floor(n)
end

local function move_clips_safe(media_pool, source_folder, clip_items, target_folder)
    media_pool:SetCurrentFolder(source_folder)
    local moved = media_pool:MoveClips(clip_items, target_folder)
    if moved then
        return true, #clip_items
    end

    local moved_count = 0
    for _, clip_item in ipairs(clip_items) do
        media_pool:SetCurrentFolder(source_folder)
        local single_moved = media_pool:MoveClips({clip_item}, target_folder)
        if single_moved then
            moved_count = moved_count + 1
        end
    end

    return moved_count == #clip_items, moved_count
end

local resolve = Resolve()
local project = resolve:GetProjectManager():GetCurrentProject()
local media_pool = project:GetMediaPool()
local root_folder = media_pool:GetRootFolder()
resolve:OpenPage("media")

local source_folder = find_folder_recursive(root_folder, INPUT_BIN_NAME)
if source_folder == nil then
    error("Could not find source bin named " .. INPUT_BIN_NAME)
end

media_pool:SetCurrentFolder(source_folder)

local source_clips = source_folder:GetClipList()
if source_clips == nil or #source_clips < 3 then
    error("Need at least 3 clips in source bin " .. INPUT_BIN_NAME)
end

local clips = {}
for _, item in ipairs(source_clips) do
    local props = item:GetClipProperty()
    local width, height = parse_resolution(props["Resolution"])
    local frames = parse_frames(props["Frames"])
    if frames > 0 then
        clips[#clips + 1] = {
            item = item,
            frames = frames,
            kind = (height > width) and "Vertical" or "Full"
        }
    end
end

if #clips < 3 then
    error("Need at least 3 clips with usable frame metadata in " .. INPUT_BIN_NAME)
end

table.sort(clips, function(a, b)
    if a.frames ~= b.frames then
        return a.frames > b.frames
    end
    return tostring(a.item:GetName()) < tostring(b.item:GetName())
end)

local bins = {
    {name = "Bin 1", clips = {}, totalFrames = 0},
    {name = "Bin 2", clips = {}, totalFrames = 0},
    {name = "Bin 3", clips = {}, totalFrames = 0}
}

for _, clip in ipairs(clips) do
    local best = bins[1]
    for i = 2, #bins do
        local candidate = bins[i]
        if candidate.totalFrames < best.totalFrames then
            best = candidate
        elseif candidate.totalFrames == best.totalFrames and #candidate.clips < #best.clips then
            best = candidate
        end
    end
    best.clips[#best.clips + 1] = clip
    best.totalFrames = best.totalFrames + clip.frames
end

table.sort(bins, function(a, b)
    return a.totalFrames < b.totalFrames
end)

local suffixes = {"A", "B", "C"}
local output_bins = {}
for i, source in ipairs(bins) do
    local suffix = suffixes[i]
    local vertical = {name = PARENT_BIN_NAME .. "_" .. suffix .. "_Vertical", clips = {}, kind = "Vertical"}
    local full = {name = PARENT_BIN_NAME .. "_" .. suffix .. "_Full", clips = {}, kind = "Full"}
    for _, clip in ipairs(source.clips) do
        if clip.kind == "Vertical" then
            vertical.clips[#vertical.clips + 1] = clip
        else
            full.clips[#full.clips + 1] = clip
        end
    end
    output_bins[#output_bins + 1] = vertical
    output_bins[#output_bins + 1] = full
end

local parent_folder, parent_name = unique_subfolder(media_pool, root_folder, PARENT_BIN_NAME)
print("[OrganizeBin] Source bin: " .. INPUT_BIN_NAME)
print("[OrganizeBin] Created parent bin: " .. parent_name)

for _, bin in ipairs(output_bins) do
    local child_folder, child_name = unique_subfolder(media_pool, parent_folder, bin.name)
    if #bin.clips > 0 then
        local clip_items = {}
        for _, clip in ipairs(bin.clips) do
            clip_items[#clip_items + 1] = clip.item
        end
        local moved, moved_count = move_clips_safe(media_pool, source_folder, clip_items, child_folder)
        if not moved then
            error("Failed to move clips into " .. child_name)
        end
        print("[OrganizeBin] " .. child_name .. ": moved " .. tostring(moved_count) .. " clips")
    else
        print("[OrganizeBin] " .. child_name .. ": moved 0 clips")
    end
end

media_pool:SetCurrentFolder(parent_folder)
