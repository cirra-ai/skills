public without sharing class XDO_Tool_TrackingEventRemoveDuplicates extends XDO_Tool_TrackingEventProcessor //NOPMD
{
    private static final Integer DUPLICATE_TIME_THRESHOLD_SECONDS = 5;

    public XDO_Tool_TrackingEventRemoveDuplicates() {
        this(null);
    }

    public XDO_Tool_TrackingEventRemoveDuplicates(XDO_Tool_TrackingEventProcessor next) {
        super(next);
    }

    public override void process(List<XDO_Tool_Platform_Tracking_Event__e> trackingEvents) {
        Boolean isDuplicate = false;
        Integer items = trackingEvents.size() - 1;
        Set<String> eventContexts = new Set<String>();

        List<XDO_Tool_Tracking_Event__c> stagedEvents = [
                SELECT Payload__c
                FROM XDO_Tool_Tracking_Event__c
                WHERE SystemModstamp > :Datetime.now().addSeconds(-(DUPLICATE_TIME_THRESHOLD_SECONDS))
        ];

        for (Integer i = items; i >= 0; i--) {
            for (XDO_Tool_Tracking_Event__c stagedEvent : stagedEvents) {
                if (trackingEvents[i].Payload__c == stagedEvent.Payload__c) {
                    isDuplicate = true;
                    break;
                }
            }

            if (isDuplicate || eventContexts.contains(trackingEvents[i].Payload__c)) {
                trackingEvents.remove(i);
            } else {
                eventContexts.add(trackingEvents[i].Payload__c);
            }

            isDuplicate = false;
        }

        super.process(trackingEvents);
    }
}