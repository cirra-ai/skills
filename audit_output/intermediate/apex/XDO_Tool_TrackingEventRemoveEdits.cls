public with sharing class XDO_Tool_TrackingEventRemoveEdits extends XDO_Tool_TrackingEventProcessor //NOPMD
{
    private static final String FLEXI_PAGE_EDITOR_PATH_PREFIX = '/flexipageEditor/';
    private static final String TRACKING_EVENT_PROPERTY_PAGE = 'page';

    public XDO_Tool_TrackingEventRemoveEdits() {
        this(null);
    }

    public XDO_Tool_TrackingEventRemoveEdits(XDO_Tool_TrackingEventProcessor next) {
        super(next);
    }

    public override void process(List<XDO_Tool_Platform_Tracking_Event__e> trackingEvents) {
        Integer items = trackingEvents.size() - 1;

        for (Integer i = items; i >= 0; i--) {
            XDO_Tool_TrackingEvent event = (XDO_Tool_TrackingEvent) JSON.deserialize(trackingEvents[i].Payload__c, XDO_Tool_TrackingEvent.class);

            if (event.getPropertyValue(TRACKING_EVENT_PROPERTY_PAGE) != null &&
                    event.getPropertyValue(TRACKING_EVENT_PROPERTY_PAGE)?.contains(FLEXI_PAGE_EDITOR_PATH_PREFIX)) {
                trackingEvents.remove(i);
            }
        }

        super.process(trackingEvents);
    }
}