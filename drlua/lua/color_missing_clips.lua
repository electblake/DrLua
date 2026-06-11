local resolve = Resolve()
local pm = resolve:GetProjectManager()
local project = pm:GetCurrentProject()
local timeline = project:GetCurrentTimeline()

if not timeline then
    print("NO CURRENT TIMELINE")
    return
end

local MARK_COLOR = "Yellow"
local FLAG_COLOR = "Yellow"

local function str(v)
    if v == nil then return "" end
    return tostring(v)
end

local function lower(v)
    return string.lower(str(v))
end

local function has_missing_status(props)
    if not props then return true end

    for k, v in pairs(props) do
        local kk = lower(k)
        local vv = lower(v)

        if kk == "status" and (vv == "offline" or vv == "missing") then
            return true
        end

        if vv == "offline" or vv == "missing" or vv:find("media offline", 1, true) then
            return true
        end
    end

    return false
end

local function mark_item(item)
    item:SetClipColor(MARK_COLOR)
    item:AddFlag(FLAG_COLOR)
end

local count = 0

for _, track_type in ipairs({ "video", "audio" }) do
    local tracks = timeline:GetTrackCount(track_type) or 0

    for track_index = 1, tracks do
        local items = timeline:GetItemListInTrack(track_type, track_index) or {}

        for _, item in ipairs(items) do
            local mpi = item:GetMediaPoolItem()
            local missing = false

            if not mpi then
                missing = true
            else
                missing = has_missing_status(mpi:GetClipProperty())
            end

            if missing then
                count = count + 1
                mark_item(item)
                print(track_type .. " " .. track_index .. " | " .. item:GetName())
            end
        end
    end
end

print("MISSING MEDIA MARKED: " .. count)
print("NOW USE: Timeline > Select Clips > By Clip Color > Pink")
