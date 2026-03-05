public without sharing virtual class XDO_Tool_TrackingEventReporting extends XDO_Tool_TrackingEvent //NOPMD
{
    public enum TRACKING_EVENT {
        Conversion
    }

    public enum TRACKING_PROPERTY {
        minutes_saved
    }

    public XDO_Tool_TrackingEventReporting() {
    }

    public XDO_Tool_TrackingEventReporting(TRACKING_EVENT event) {
        super(TRACKING_EVENT_TYPE.Reporting, event.name());
    }

    @InvocableMethod(Label='Capture Reporting Tracking Event' Description='Capture a reporting tracking event' Category='XDO Tool - Tracking Event' IconName='slds:utility:send_log')
    public static void publish(List<XDO_Tool_TrackingEvent> trackingEvents) {
        System.debug('>>>>> SDO_Tool_TrackingEventReportingInput.publish: ');
        System.debug(trackingEvents);

        for (XDO_Tool_TrackingEvent event : trackingEvents) {
            event.setType(TRACKING_EVENT_TYPE.Reporting)
                    .publish();
        }
    }

    public class Conversion extends XDO_Tool_TrackingEventReporting {
        public Conversion() {
            super(TRACKING_EVENT.Conversion);
        }

        public Conversion setMinutesSaved(Integer value) {
            this.addProperty(TRACKING_PROPERTY.minutes_saved.name(), String.valueOf(value));

            return this;
        }
    }
}