if CREATE_TIMELINES then
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

-- @@AGGREGATE@@

if CREATE_TIMELINES then
    local aggregate_names = {
        Vertical = PARENT_BIN_NAME .. SCENERULES_SEP .. "Vertical",
        Full = PARENT_BIN_NAME .. SCENERULES_SEP .. "Full",
    }
    for _, kind in ipairs({"Vertical", "Full"}) do
        media_pool:SetCurrentFolder(parent_folder)
        local aggregate = media_pool:CreateEmptyTimeline(aggregate_names[kind])
        if aggregate == nil then
            error("Could not create aggregate timeline " .. aggregate_names[kind])
        end
        project:SetCurrentTimeline(aggregate)
        while aggregate:GetTrackCount("video") < 3 do
            aggregate:AddTrack("video")
        end
        local clip_infos = {}
        for _, bin in ipairs(BINS) do
            if bin.kind == kind and bin.timeline_frames > 0 then
                clip_infos[#clip_infos + 1] = {
                    mediaPoolItem = bin.timeline_media,
                    startFrame = 0,
                    endFrame = bin.timeline_frames - 1,
                    trackIndex = bin.layer,
                    recordFrame = 0,
                    mediaType = 1,
                }
            end
        end
        media_pool:AppendToTimeline(clip_infos)
        print("[CreateBins] Created aggregate timeline: " .. aggregate_names[kind])
    end
end
