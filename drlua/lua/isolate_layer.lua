function isolate_layer(layer)
    local resolve = Resolve()
    local project = resolve:GetProjectManager():GetCurrentProject()
    local timeline = project:GetCurrentTimeline()

    if not timeline then
        print("NO CURRENT TIMELINE")
        return false
    end

    layer = tonumber(layer)

    if not layer then
        print("INVALID LAYER: " .. tostring(layer))
        return false
    end

    local function set_tracks_locked(track_type, keep_layer)
        local count = timeline:GetTrackCount(track_type) or 0

        for i = 1, count do
            if keep_layer <= 0 then
                timeline:SetTrackLock(track_type, i, false)
            else
                timeline:SetTrackLock(track_type, i, i ~= keep_layer)
            end
        end
    end

    set_tracks_locked("video", layer)
    set_tracks_locked("audio", layer)

    if layer <= 0 then
        print("UNLOCKED ALL VIDEO/AUDIO LAYERS")
    else
        print("ISOLATED VIDEO/AUDIO LAYER " .. tostring(layer))
    end

    return true
end
