public without sharing abstract class XDO_Tool_TrackingEventProcessor //NOPMD
{
    private XDO_Tool_TrackingEventProcessor next;

    public XDO_Tool_TrackingEventProcessor(XDO_Tool_TrackingEventProcessor next) {
        this.next = next;
    }

    public virtual void process(List<XDO_Tool_Platform_Tracking_Event__e> trackingEvents) {
        if (!trackingEvents.isEmpty()) {
            next?.process(trackingEvents);
        }
    }

    public static XDO_Tool_TrackingEventProcessor getProcessors() {
        return new XDO_Tool_TrackingEventRemoveEdits(
                new XDO_Tool_TrackingEventFinalizer());
    }
}