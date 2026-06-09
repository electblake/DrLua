local function get_clip_duration_frames(timeline_item)
    local ok_duration, duration = pcall(function()
        return timeline_item:GetDuration()
    end)
    if ok_duration and type(duration) == "number" then
        return duration
    end

    local ok_start, start_frame = pcall(function()
        return timeline_item:GetStart()
    end)
    local ok_end, end_frame = pcall(function()
        return timeline_item:GetEnd()
    end)
    if ok_start and ok_end and type(start_frame) == "number" and type(end_frame) == "number" then
        return end_frame - start_frame
    end

    return nil
end

local resolve = Resolve()
local project = resolve:GetProjectManager():GetCurrentProject()
if project == nil then
    error("No active project")
end

local timeline = project:GetCurrentTimeline()
if timeline == nil then
    error("No current timeline selected")
end

local threshold = tonumber(SHORT_CLIP_MAX_FRAMES) or 12
if threshold < 1 then
    threshold = 1
end

local to_delete = {}
local seen = {}
local scanned = 0

for _, track_type in ipairs({"video", "audio", "subtitle"}) do
    local track_count = timeline:GetTrackCount(track_type) or 0
    for track_index = 1, track_count do
        local items = timeline:GetItemListInTrack(track_type, track_index) or {}
        for _, timeline_item in ipairs(items) do
            scanned = scanned + 1
            local duration_frames = get_clip_duration_frames(timeline_item)
            if type(duration_frames) == "number" and duration_frames <= threshold then
                local key = tostring(timeline_item)
                if not seen[key] then
                    seen[key] = true
                    to_delete[#to_delete + 1] = timeline_item
                end
            end
        end
    end
end

if #to_delete == 0 then
    print("[CleanShortClips] No clips <= " .. tostring(threshold) .. " frames on current timeline. Scanned " .. tostring(scanned) .. " clips.")
    return
end

local deleted = timeline:DeleteClips(to_delete, false)
if not deleted then
    error("Failed to delete short clips from current timeline")
end

print("[CleanShortClips] Deleted " .. tostring(#to_delete) .. " clips <= " .. tostring(threshold) .. " frames from current timeline (scanned " .. tostring(scanned) .. ").")
